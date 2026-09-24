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
        offer = {'price': '1234', 'url': url, 'journeys': []}
        s = Session('complete', {'origin': 'CNF', 'destination': 'GRU', 'adults': '2', 'result': {'offers': [offer]}})
        p = payload_for(s, 'Confira:\n'+url)
        self.assertEqual(p['interactive']['type'], 'cta_url')
        self.assertEqual(p['interactive']['action']['parameters']['url'], url)
        self.assertEqual(p['interactive']['action']['parameters']['display_text'], 'Abrir oferta')
        self.assertEqual(payload_for(s, 'https://attacker.test')['type'], 'text')


class InteractiveQueueTests(unittest.TestCase):
    setUp = messaging_tests.MessagingTests.setUp
    payload = messaging_tests.MessagingTests.payload
    send = messaging_tests.MessagingTests.send

    def test_native_click_advances_once_and_stale_click_does_not(self):
        self.config['ATLAS_LIVE_FLIGHTS_ENABLED'] = 'true'
        session = Session('adults', {'origin': 'CNF', 'destination': 'GRU', 'departure': '23/10/2027', 'return': '30/10/2027'})
        payload_for(session, 'Adultos?')
        action = next(k for k,v in session.values['_choices'].items() if v == '2')
        with database(self.path) as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?)', ('570000000000',session.step,json.dumps(session.values)))
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
