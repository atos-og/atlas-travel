import unittest
from datetime import date
from atlas.flexible import date_pairs, search_nearby
from atlas.conversation import Conversation, Session
from atlas.flights import format_results, rank
from atlas.interactive import payload_for


class FlexibleTests(unittest.TestCase):
    def setUp(self):
        self.values = {'origin': 'CNF', 'destination': 'GRU', 'departure': '31/12/2026',
                       'return': '07/01/2027', 'adults': '2', 'priority': '1', 'budget': None}

    def provider(self, values):
        return {'status': 'success', 'offers': [{
            'price': '1000', 'duration': 120, 'stops': 0,
            'journeys': [{'departure': values['departure'], 'arrival': values['return'],
                          'duration': 120, 'stops': 0, 'airlines': 'TEST'}],
            'url': 'https://www.google.com/travel/flights?day=' + values['departure']}]}

    def test_pairs_cross_year_and_preserve_duration(self):
        self.assertEqual(date_pairs(self.values, date(2026, 9, 24)), [
            ('31/12/2026', '07/01/2027'), ('30/12/2026', '06/01/2027'), ('01/01/2027', '08/01/2027')])

    def test_past_pair_is_not_queried(self):
        self.assertEqual(len(date_pairs(self.values, date(2026, 12, 31))), 2)
        with self.assertRaises(ValueError):
            date_pairs(self.values, date(2027, 1, 1))

    def test_three_queries_keep_actual_dates_and_do_not_mutate_request(self):
        before = dict(self.values)
        result = search_nearby(self.provider, self.values, date(2026, 9, 24))
        self.assertEqual(len(result['queries']), 3)
        self.assertEqual(len(result['offers']), 3)
        self.assertEqual(result['offers'][2]['travel_dates']['departure'], '01/01/2027')
        self.assertEqual(self.values, before)
        self.assertFalse(result['partial'])
        self.assertEqual(rank(result['offers'], '1', '999'), [])

    def test_partial_failure_is_visible_with_or_without_offers(self):
        def provider(values):
            if values['departure'] == '31/12/2026':
                return self.provider(values)
            raise TimeoutError()
        result = search_nearby(provider, self.values, date(2026, 9, 24))
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['partial'])
        self.assertIn('Consulta parcial', format_results(result, self.values))
        empty = search_nearby(lambda _: {'status': 'timeout'}, self.values, date(2026, 9, 24))
        self.assertEqual(empty['status'], 'unavailable')
        self.assertTrue(empty['partial'])

    def test_empty_search_is_not_a_claim_of_no_flights(self):
        result = search_nearby(lambda _: {'status': 'empty'}, self.values, date(2026, 9, 24))
        self.assertEqual(result['status'], 'empty')
        self.assertFalse(result['partial'])
        self.assertIn('não prova ausência', format_results(result, self.values))

    def test_setting_requires_explicit_confirmation_and_can_be_disabled(self):
        calls = []
        bot = Conversation(lambda values: calls.append(values) or self.provider(values))
        bot.sessions['u'] = Session('complete', dict(self.values))
        def send(text):
            return bot.reply('u', text, today=date(2026, 9, 24))
        send('datas flexíveis')
        self.assertEqual(payload_for(bot.sessions['u'], 'Escolha')['interactive']['type'], 'button')
        confirmation = send('datas próximas')
        self.assertIn('até 3 consultas', confirmation)
        self.assertEqual(calls, [])
        send('sim')
        self.assertEqual(len(calls), 3)
        send('datas flexíveis')
        self.assertIn('Datas exatas', send('manter datas'))
        send('sim')
        self.assertEqual(len(calls), 4)

    def test_actual_dates_appear_in_native_offer_and_long_summary(self):
        result = search_nearby(self.provider, self.values, date(2026, 9, 24))
        session = Session('complete', dict(self.values, result=result, flexibility='nearby'))
        menu = payload_for(session, 'x' * 1500)
        self.assertIn('Datas consultadas', menu['interactive']['body']['text'])
        self.assertLessEqual(len(menu['interactive']['body']['text']), 1024)
        self.assertLessEqual(len(menu['interactive']['action']['sections'][0]['rows']), 10)
        offer = result['offers'][2]
        payload = payload_for(session, offer['url'])
        self.assertIn('01/01/2027', payload['interactive']['body']['text'])

    def test_first_message_flexibility_does_not_invent_other_fields(self):
        bot = Conversation(self.provider)
        bot.reply('u', 'datas flexíveis')
        bot.reply('u', 'comparar 1 dia')
        self.assertEqual(bot.sessions['u'].step, 'origin')
        self.assertEqual(bot.sessions['u'].values, {'flexibility': 'nearby'})
