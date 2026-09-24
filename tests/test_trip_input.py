import json
import unittest
from datetime import date
from unittest.mock import patch

from atlas.conversation import Conversation, Session
from atlas.interactive import payload_for
from atlas.messaging import database, ingest, process_one
import test_messaging as messaging_tests


class TripInputTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.bot = Conversation(lambda values: self.calls.append(values) or {'status': 'empty', 'offers': []})

    def send(self, text):
        return self.bot.reply('u', text, today=date(2026, 9, 24))

    def prepare(self):
        return self.send('Confins para Guarulhos, ida 23/10/2026, volta 30/10/2026, dois adultos, mais barata, sem limite')

    def test_first_message_collects_fields_without_searching(self):
        answer = self.prepare()
        self.assertIn('Confirmar busca', answer)
        self.assertEqual(self.calls, [])
        self.send('sim')
        self.assertEqual(self.calls, [{'origin': 'CNF', 'destination': 'GRU',
                                      'departure': '23/10/2026', 'return': '30/10/2026',
                                      'adults': '2', 'priority': '1', 'budget': None}])

    def test_ambiguous_country_keeps_other_answers(self):
        answer = self.send('Confins -> Colômbia, de avião, para 2 adultos')
        self.assertIn('Qual destino', answer)
        self.assertEqual(self.bot.sessions['u'].values, {'origin': 'CNF', 'adults': '2'})
        self.send('San Andrés')
        self.send('23/10/2026')
        answer = self.send('7 dias depois')
        self.assertIn('menor preço', answer)
        self.assertEqual(self.bot.sessions['u'].values['destination'], 'ADZ')

    def test_natural_dates_in_combined_request(self):
        answer = self.send('de Confins para Bogotá, ida dia 23 de outubro desse ano, volta 7 dias depois, 2 adultos')
        self.assertIn('menor preço', answer)
        self.assertEqual(self.bot.sessions['u'].values['departure'], '23/10/2026')
        self.assertEqual(self.bot.sessions['u'].values['return'], '30/10/2026')

    def test_month_request_does_not_invent_dates_or_keep_old_offers(self):
        self.prepare()
        self.send('sim')
        answer = self.send('Eu gostaria q fossem para janeiro de 2027')
        values = self.bot.sessions['u'].values
        self.assertIn('mês inteiro', answer)
        self.assertEqual(values['adults'], '2')
        self.assertEqual(values['destination'], 'GRU')
        self.assertNotIn('departure', values)
        self.assertNotIn('return', values)
        self.assertNotIn('result', values)
        self.assertEqual(len(self.calls), 1)

    def test_change_passengers_keeps_trip_and_requires_new_confirmation(self):
        self.prepare()
        self.send('sim')
        answer = self.send('somos três adultos')
        self.assertIn('Confirmar busca', answer)
        self.assertEqual(self.bot.sessions['u'].values['adults'], '3')
        self.assertEqual(self.bot.sessions['u'].values['departure'], '23/10/2026')
        self.assertNotIn('result', self.bot.sessions['u'].values)
        self.assertEqual(len(self.calls), 1)

    def test_invalid_return_is_not_used_in_search(self):
        self.send('CNF para GRU, ida 30/10/2026, volta 23/10/2026, 2 adultos')
        self.assertEqual(self.bot.sessions['u'].step, 'return')
        self.assertNotIn('return', self.bot.sessions['u'].values)
        self.assertEqual(self.calls, [])

    def test_unsupported_passengers_and_negation_do_not_change_trip(self):
        self.prepare()
        before = dict(self.bot.sessions['u'].values)
        for text in ['2 adultos e 1 criança', '-2 adultos', 'não quero sem escalas', 'ida 23 ou 24 de outubro', '2 adultos, 3 adultos']:
            self.send(text)
            self.assertEqual(self.bot.sessions['u'].values, before)

    def test_price_clarification_has_native_choices_and_uses_cached_budget(self):
        self.prepare()
        self.send('sim')
        answer = self.send('carinho em')
        self.assertIn('preço alto', answer)
        payload = payload_for(self.bot.sessions['u'], answer)
        self.assertEqual(payload['interactive']['type'], 'button')
        self.assertIn('todos os adultos', self.send('sim'))
        self.assertIn('consulta anterior', self.send('até 2000'))
        self.assertEqual(len(self.calls), 1)

    def test_direct_price_complaint_opens_budget(self):
        self.prepare()
        self.send('sim')
        self.assertIn('todos os adultos', self.send('Achei bem caro'))
        self.assertEqual(self.bot.sessions['u'].step, 'budget')


class ProgressQueueTests(unittest.TestCase):
    setUp = messaging_tests.MessagingTests.setUp
    payload = messaging_tests.MessagingTests.payload
    send = messaging_tests.MessagingTests.send

    def prepare(self):
        self.config['ATLAS_LIVE_FLIGHTS_ENABLED'] = 'true'
        values = {'origin': 'CNF', 'destination': 'GRU', 'departure': '23/10/2099',
                  'return': '30/10/2099', 'adults': '2', 'priority': '1', 'budget': None}
        with database(self.path) as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?)', ('570000000000', 'confirm', json.dumps(values)))
        ingest(self.payload(text='sim'), self.config, self.path, now=100)

    def test_notice_precedes_search_and_does_not_repeat_on_duplicate(self):
        self.prepare()
        def search(values):
            self.assertEqual(len(self.sent), 1)
            self.assertIn('consultando', self.sent[0])
            # The slow provider must not run inside a write transaction.
            with database(self.path) as db:
                db.execute("UPDATE progress SET delivery='test'")
            return {'status': 'empty', 'offers': []}
        with patch('atlas.flights.search', side_effect=search) as provider:
            process_one(self.config, self.path, self.send, now=100)
            ingest(self.payload(text='sim'), self.config, self.path, now=100)
            self.assertFalse(process_one(self.config, self.path, self.send, now=100))
        self.assertEqual(len(self.sent), 2)
        provider.assert_called_once()

    def test_failed_progress_send_does_not_prevent_results(self):
        self.prepare()
        attempts = []
        def send(*args):
            attempts.append(args[-1])
            if len(attempts) == 1:
                raise TimeoutError()
            return 'sent', 'final', None
        with patch('atlas.flights.search', return_value={'status': 'empty', 'offers': []}):
            process_one(self.config, self.path, send, now=100)
        self.assertEqual(len(attempts), 2)
        with database(self.path) as db:
            self.assertEqual(db.execute('SELECT state FROM progress').fetchone()[0], 'uncertain')
            self.assertEqual(db.execute('SELECT state FROM inbox').fetchone()[0], 'sent')

    def test_recovered_search_does_not_repeat_attempted_progress(self):
        self.prepare()
        with database(self.path) as db:
            db.execute("INSERT INTO progress(inbox_id,state) VALUES ('m1','attempted')")
        with patch('atlas.flights.search', return_value={'status': 'empty', 'offers': []}):
            process_one(self.config, self.path, self.send, now=100)
        self.assertEqual(len(self.sent), 1)
        self.assertNotIn('consultando', self.sent[0])
