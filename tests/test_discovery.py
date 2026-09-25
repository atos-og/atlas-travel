import copy
import unittest
from datetime import date
from atlas.conversation import Conversation, Session
from atlas.discovery import compare, destinations
from atlas.interactive import payload_for


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.values = dict(origin='CNF', departure='23/10/2027', **{'return': '30/10/2027'},
                           adults='2', budget='1500', priority='1', candidates=['GRU', 'BOG', 'REC'])
        self.calls = []

    def provider(self, values):
        self.calls.append(values.copy())
        price = {'GRU': '1000', 'BOG': '2000', 'REC': '800'}[values['destination']]
        return {'status': 'success', 'checked_at': 'test time', 'offers': [dict(
            price=price, duration=120, stops=0, journeys=[{'destination': values['destination']}],
            url='https://www.google.com/travel/flights?to=' + values['destination'])]}

    def test_explicit_candidates_bounded_deduplicated_and_unambiguous(self):
        self.assertEqual(destinations('Bogotá, BOG, Recife', 'CNF'), ['BOG', 'REC'])
        for text in ('GRU,REC,BOG,MDE', 'São Paulo', 'CNF', 'GRU,'):
            with self.assertRaises(ValueError):
                destinations(text, 'CNF')

    def test_budget_ranking_query_bound_and_request_isolation(self):
        original = copy.deepcopy(self.values)
        report = compare(self.provider, self.values)
        self.assertEqual([r['destination'] for r in report['matches']], ['REC', 'GRU'])
        self.assertEqual(report['queries'][1]['status'], 'no_match')
        self.assertEqual(len(self.calls), 3)
        self.assertTrue(all(c['adults'] == '2' and c['departure'] == '23/10/2027' for c in self.calls))
        self.assertTrue(all('candidates' not in c for c in self.calls))
        self.assertEqual(self.values, original)

    def test_failure_is_not_reported_as_no_matching_fares(self):
        def provider(values):
            if values['destination'] == 'BOG':
                raise TimeoutError()
            return self.provider(values)
        report = compare(provider, self.values)
        self.assertEqual(report['queries'][1]['status'], 'unavailable')
        self.assertEqual(len(report['matches']), 2)

    def test_nonstop_filter_and_malformed_price(self):
        def provider(values):
            result = self.provider(values)
            result['offers'][0]['stops'] = 1
            return result
        self.values['priority'] = '3'
        self.assertFalse(compare(provider, self.values)['matches'])
        for price in ('NaN', '-1', 'Infinity'):
            def invalid(values):
                result = self.provider(values)
                result['offers'][0]['price'] = price
                return result
            self.assertTrue(all(r['status'] == 'unavailable' for r in compare(invalid, self.values)['queries']))

    def test_guided_flow_confirms_before_search_and_preserves_original_trip(self):
        bot = Conversation(self.provider)
        original = {'origin': 'CNF', 'destination': 'MDE'}
        bot.sessions['u'] = Session('departure', dict(original))
        def send(text):
            return bot.reply('u', text, today=date(2026, 9, 24))
        for text in ('explorar destinos', '23/10/2027', '7 dias depois', 'dois adultos', '1500', 'GRU, BOG, REC'):
            answer = send(text)
        self.assertEqual(self.calls, [])
        self.assertIn('datas exatas', answer)
        self.assertEqual(bot.sessions['u'].step, 'departure')
        send('sim')
        self.assertEqual(len(self.calls), 3)
        for key, value in original.items():
            self.assertEqual(bot.sessions['u'].values[key], value)
        payload = payload_for(bot.sessions['u'], send('opções'))
        self.assertEqual(payload['interactive']['type'], 'list')
        # Use a fully shaped provider result only when selecting for flight display.
        for r in bot.sessions['u'].values['_discovery']['report']['matches']:
            r['result']['offers'][0]['journeys'] = []
        answer = send('destino 1')
        self.assertIn('sem buscar novamente', answer)
        self.assertEqual(bot.sessions['u'].values['destination'], 'REC')
        self.assertEqual(bot.sessions['u'].step, 'complete')
        self.assertEqual(len(self.calls), 3)

    def test_back_and_menu_suspend_without_overwriting_criteria(self):
        bot = Conversation(self.provider)
        bot.sessions['u'] = Session('adults', {'origin': 'CNF'})
        bot.reply('u', 'explorar destinos')
        self.assertIn('Quantos adultos', bot.reply('u', 'voltar aos voos'))
        self.assertFalse(bot.sessions['u'].values['_discovery']['active'])
        self.assertEqual(bot.sessions['u'].values['origin'], 'CNF')

    def test_reset_does_not_keep_old_budget_and_expired_dates_do_not_query(self):
        bot = Conversation(self.provider)
        bot.sessions['u'] = Session('complete', dict(self.values, destination='GRU'))
        bot.reply('u', 'explorar destinos', today=date(2027, 10, 24))
        bot.reply('u', 'REC', today=date(2027, 10, 24))
        self.assertIn('data de ida passou', bot.reply('u', 'sim', today=date(2027, 10, 24)))
        self.assertEqual(self.calls, [])
        bot.reply('u', 'refazer comparação')
        state = bot.sessions['u'].values['_discovery']
        self.assertNotIn('budget', state)
        self.assertEqual(state['stage'], 'origin')

    def test_disabled_provider_does_not_claim_search(self):
        bot = Conversation()
        self.assertIn('não consulta tarifas reais', bot.reply('u', 'explorar destinos'))

    def test_help_does_not_become_a_destination_or_trigger_a_search(self):
        bot = Conversation(self.provider)
        bot.sessions['u'] = Session('complete', dict(self.values, destination='GRU'))
        bot.reply('u', 'explorar destinos')
        stage = bot.sessions['u'].values['_discovery']['stage']
        self.assertIn('Nenhuma busca', bot.reply('u', 'ajuda'))
        self.assertEqual(bot.sessions['u'].values['_discovery']['stage'], stage)
        self.assertEqual(self.calls, [])

    def test_switch_between_itinerary_and_discovery_without_resetting_flights(self):
        bot = Conversation(self.provider)
        bot.sessions['u'] = Session('adults', {'origin': 'CNF', 'destination': 'GRU'})
        bot.reply('u', 'explorar destinos')
        self.assertIn('primeiro dia', bot.reply('u', 'roteiro para Bogotá'))
        session = bot.sessions['u']
        self.assertFalse(session.values['_discovery']['active'])
        self.assertTrue(session.values['_itinerary']['active'])
        bot.reply('u', 'explorar destinos')
        self.assertFalse(session.values['_itinerary']['active'])
        self.assertTrue(session.values['_discovery']['active'])
        self.assertEqual(session.step, 'adults')
        self.assertEqual(session.values['destination'], 'GRU')
