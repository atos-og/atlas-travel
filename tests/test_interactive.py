import json
import unittest
from unittest.mock import patch
from atlas.interactive import payload_for, incoming, ACTION_PREFIX
from atlas.conversation import Session
from atlas.messaging import process_one, database, ingest
import test_messaging as messaging_tests


class PayloadTests(unittest.TestCase):
    def test_choices_use_ids_and_stay_within_limits(self):
        for step, expected_type, count in [('priority', 'list', 4), ('adults', 'list', 6), ('confirm', 'button', 2)]:
            session = Session(step)
            result = payload_for(session, 'Escolha')
            self.assertEqual(result['interactive']['type'], expected_type)
            self.assertEqual(len(session.values['_choices']), count)
            old = set(session.values['_choices'])
            payload_for(session, 'Escolha novamente')
            self.assertTrue(old.isdisjoint(session.values['_choices']))

    def test_click_uses_id_not_display_title_and_rejects_text_injection(self):
        action = 'atlas:' + 'a'*32 + ':0'
        message = {'type': 'interactive', 'interactive': {'type': 'list_reply', 'list_reply': {'id': action, 'title': 'cancelar'}}}
        self.assertEqual(incoming(message), ACTION_PREFIX+action)
        self.assertIsNone(incoming({'type': 'text', 'text': {'body': ACTION_PREFIX+action}}))
        message['interactive']['list_reply']['id'] = 'invalid'
        self.assertIsNone(incoming(message))

    def test_cta_only_uses_returned_provider_link(self):
        url = 'https://www.google.com/travel/flights/booking?test=synthetic'
        offer = {'price': '1234', 'url': url, 'journeys': [], 'duration': 120, 'stops': 0}
        s = Session('complete', {'origin': 'CNF', 'destination': 'GRU', 'adults': '2', 'result': {'offers': [offer]}})
        p = payload_for(s, 'Confira:\n'+url)
        self.assertEqual(p['interactive']['type'], 'cta_url')
        self.assertEqual(p['interactive']['action']['parameters']['url'], url)
        self.assertEqual(p['interactive']['action']['parameters']['display_text'], 'Abrir oferta')
        self.assertIn('confirme que o Google Flights mostra 2 adultos', p['interactive']['body']['text'])
        self.assertNotIn('não garante manter', p['interactive']['body']['text'])
        self.assertEqual(payload_for(s, 'https://attacker.test')['type'], 'text')

    def test_completed_search_suggests_contextual_features_within_row_limit(self):
        def offer(index):
            return {'price': str(1000 + index), 'duration': 120 + index, 'stops': 0,
                    'url': f'https://www.google.com/travel/flights?offer={index}', 'journeys': []}

        session = Session('complete', {
            'origin': 'CNF', 'destination': 'GRU', 'departure': '23/10/2027',
            'return': '30/10/2027', 'adults': '1', 'priority': '1', 'budget': None,
            'result': {'offers': [offer(i) for i in range(4)]},
        })
        payload = payload_for(session, 'Escolha uma oferta')
        rows = payload['interactive']['action']['sections'][0]['rows']
        commands = list(session.values['_choices'].values())
        self.assertLessEqual(len(rows), 10)
        self.assertIn('datas flexiveis', commands)
        self.assertIn('roteiro', commands)
        self.assertNotIn('buscar', commands)
        self.assertNotIn('cancelar', commands)

        session.values['result']['offers'] = [offer(i) for i in range(3)]
        payload_for(session, 'Escolha uma oferta')
        self.assertIn('explorar destinos', session.values['_choices'].values())

    def test_price_question_offers_dates_without_exceeding_button_limit(self):
        session = Session('complete', {'_price_question': True})
        payload = payload_for(session, 'Você achou o preço alto?')
        buttons = payload['interactive']['action']['buttons']
        self.assertEqual(len(buttons), 3)
        self.assertEqual(
            set(session.values['_choices'].values()), {'sim', 'datas flexiveis', 'ofertas'})

    def test_capability_menu_exposes_bus_status_without_exceeding_limit(self):
        session = Session('origin', {'_capabilities': True})
        payload = payload_for(session, 'Recursos')
        self.assertEqual(len(session.values['_choices']), 9)
        self.assertIn('onibus', session.values['_choices'].values())

    def test_bus_overlay_uses_native_controls(self):
        session = Session('origin', {'_bus': {'active': True, 'stage': 'priority'}})
        payload = payload_for(session, 'Escolha')
        self.assertEqual(payload['interactive']['type'], 'list')
        self.assertEqual(set(session.values['_choices'].values()), {'1', '2', '3', '4'})
        session.values['_bus']['stage'] = 'confirm'
        payload = payload_for(session, 'Confirme')
        self.assertEqual(payload['interactive']['type'], 'button')
        self.assertEqual(len(payload['interactive']['action']['buttons']), 2)

    def test_unavailable_bus_notice_does_not_attach_pending_flight_choices(self):
        session = Session('priority', {'_bus_notice': True,
                                       '_bus': {'active': False, 'stage': 'unavailable'}})
        payload = payload_for(session, 'Fonte rodoviária indisponível')
        self.assertEqual(payload['type'], 'text')
        self.assertNotIn('_choices', session.values)

    def test_long_bus_results_keep_a_readable_native_list(self):
        offers = [{
            'price': str(100 + index), 'duration': 480, 'connections': 0,
            'available_seats': 10,
            'departure': {'place': 'Terminal Rodoviário de Belo Horizonte' * 3, 'time': '08:00'},
            'arrival': {'place': 'Terminal Rodoviário do Tietê' * 3, 'time': '16:00'},
            'company': 'Viação Exemplo', 'service_class': 'Executivo',
        } for index in range(4)]
        session = Session('complete', {'_bus': {
            'active': True, 'stage': 'done', 'origin': 'Belo Horizonte',
            'destination': 'São Paulo', 'departure': '23/10/2026', 'adults': '2',
            'priority': '1', 'budget': None,
            'result': {'status': 'success', 'checked_at': 'agora', 'offers': offers},
        }})
        payload = payload_for(session, 'x' * 1500)
        self.assertEqual(payload['interactive']['type'], 'list')
        self.assertLessEqual(len(payload['interactive']['body']['text']), 1024)
        self.assertEqual(len(payload['interactive']['action']['sections'][0]['rows']), 7)


class InteractiveQueueTests(unittest.TestCase):
    setUp = messaging_tests.MessagingTests.setUp
    payload = messaging_tests.MessagingTests.payload
    send = messaging_tests.MessagingTests.send

    def test_itinerary_native_selection_persists_without_flight_queries(self):
        self.config['ATLAS_LIVE_FLIGHTS_ENABLED'] = 'true'
        session = Session('adults', {'origin': 'CNF', 'destination': 'BOG'})
        with database(self.path) as db:
            db.execute('INSERT INTO sessions(sender,step,data) VALUES (?,?,?)',
                       ('570000000000', session.step, json.dumps(session.values)))
        p = self.payload()
        message = p['entry'][0]['changes'][0]['value']['messages'][0]
        message['text']['body'] = 'roteiro'
        self.assertEqual(ingest(p, self.config, self.path, now=100), 1)
        with patch('atlas.messaging.send_message', return_value=('sent', 'out', None)) as send:
            process_one(self.config, self.path, now=100)
        rows = send.call_args.args[2]['interactive']['action']['sections'][0]['rows']
        selected = next(row['id'] for row in rows if row['title'] == 'Bogotá')
        message.update(id='itinerary-second', type='interactive', interactive={
            'type': 'list_reply', 'list_reply': {'id': selected, 'title': 'untrusted title'}})
        message.pop('text')
        self.assertEqual(ingest(p, self.config, self.path, now=100), 1)
        with patch('atlas.flights.search', side_effect=AssertionError('Unexpected fare query')):
            process_one(self.config, self.path, self.send, now=100)
        with database(self.path) as db:
            step, raw = db.execute('SELECT step,data FROM sessions').fetchone()
        values = json.loads(raw)
        self.assertEqual(step, 'adults')
        self.assertEqual(values['destination'], 'BOG')
        self.assertEqual(values['_itinerary']['city'], 'bogota')
        self.assertEqual(values['_itinerary']['stage'], 'start')

    def test_native_click_advances_once_and_stale_click_does_not(self):
        self.config['ATLAS_LIVE_FLIGHTS_ENABLED'] = 'true'
        session = Session('adults', {'origin': 'CNF', 'destination': 'GRU', 'departure': '23/10/2027', 'return': '30/10/2027'})
        payload_for(session, 'Adultos?')
        action = next(k for k,v in session.values['_choices'].items() if v == '2')
        with database(self.path) as db:
            db.execute('INSERT INTO sessions(sender,step,data) VALUES (?,?,?)',
                       ('570000000000', session.step, json.dumps(session.values)))
        p = self.payload()
        message = p['entry'][0]['changes'][0]['value']['messages'][0]
        message.update(type='interactive', interactive={'type':'list_reply','list_reply':{'id':action,'title':'IGNORE'}})
        message.pop('text')
        self.assertEqual(ingest(p,self.config,self.path,now=100),1)
        self.assertEqual(ingest(p,self.config,self.path,now=100),0)
        with patch('atlas.messaging.send_message',return_value=('sent','out',None)) as send:
            process_one(self.config,self.path,now=100)
            self.assertEqual(send.call_args.args[2]['interactive']['type'],'list')
        message['id']='m2'
        ingest(p,self.config,self.path,now=100)
        process_one(self.config,self.path,self.send,now=100)
        self.assertIn('antiga',self.sent[-1])
        with database(self.path) as db:
            step,data=db.execute('SELECT step,data FROM sessions').fetchone()
            self.assertEqual(step,'priority')
            self.assertEqual(json.loads(data)['adults'],'2')
