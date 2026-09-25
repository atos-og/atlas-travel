import unittest
from datetime import date, datetime
from types import SimpleNamespace as Obj
from unittest.mock import patch

from atlas.conversation import Conversation
from atlas.flights import rank, resolve_airport, search
from atlas.providers.google_flights import normalize


class FlightTests(unittest.TestCase):
    def setUp(self):
        self.values = dict(origin='CNF', destination='GRU', departure='23/10/2026', adults='2', priority='1')
        self.values['return'] = '30/10/2026'
        def journey(origin, destination, day, price):
            leg = Obj(departure_airport=origin, arrival_airport=destination,
                      departure_datetime=datetime(2026, 10, day, 10),
                      arrival_datetime=datetime(2026, 10, day, 11), airline='AD', flight_number=123)
            return Obj(price=price, currency='BRL', duration=60, stops=0, legs=[leg])
        self.raw = (journey('CNF', 'GRU', 23, 900), journey('GRU', 'CNF', 30, 700))
        self.client = Obj(build_flight_booking_url=lambda *a, **k: 'https://www.google.com/travel/flights/booking?tfs=synthetic')

    def test_round_trip_price_is_not_sum_or_last_journey(self):
        offer = normalize(self.raw, self.client, self.values)
        self.assertEqual(offer['price'], '900')
        self.assertEqual(offer['duration'], 120)

    def test_reject_incomplete_wrong_route_date_currency_and_price(self):
        self.assertIsNone(normalize(self.raw[0], self.client, self.values))
        for field, value in [('origin', 'BSB'), ('departure', '24/10/2026')]:
            self.assertIsNone(normalize(self.raw, self.client, dict(self.values, **{field: value})))
        self.raw[0].currency = 'USD'
        self.assertIsNone(normalize(self.raw, self.client, self.values))
        self.raw[0].currency = 'BRL'
        self.raw[0].price = float('nan')
        self.assertIsNone(normalize(self.raw, self.client, self.values))

    def test_untrusted_link_does_not_reach_user(self):
        self.client.build_flight_booking_url = lambda *a, **k: 'https://www.google.com.attacker.test/x'
        self.assertIsNone(normalize(self.raw, self.client, self.values)['url'])

    def test_generic_provider_fallback_is_not_presented_as_an_offer_link(self):
        self.client.build_flight_booking_url = lambda *a, **k: 'https://www.google.com/travel/flights'
        offer = normalize(self.raw, self.client, self.values)
        self.assertIsNone(offer['url'])
        self.assertEqual(offer['price'], '900')

    def test_multiple_adults_require_explicit_link_passenger_check(self):
        self.assertTrue(normalize(self.raw, self.client, self.values)['link_requires_passenger_check'])

    def test_rank_deduplicates_filters_and_sorts(self):
        a = normalize(self.raw, self.client, self.values)
        b = dict(a, price='500', duration=300, stops=1, journeys=[{'id': 'other'}])
        duplicate = dict(a, price='1000')
        self.assertEqual([o['price'] for o in rank([a, b, duplicate], '1')], ['500', '900'])
        self.assertEqual(rank([a, b], '2')[0]['price'], '900')
        self.assertEqual(len(rank([a, b], '3')), 1)
        self.assertEqual(rank([a, b], '4')[0]['price'], '900')

    def test_ambiguous_destinations_require_choice(self):
        self.assertEqual(resolve_airport('Confins'), ('CNF', None))
        self.assertIsNone(resolve_airport('Colômbia')[0])
        self.assertIsNone(resolve_airport('São Paulo')[0])

    def test_live_flow_requires_confirmation_and_recovers_from_empty(self):
        calls = []
        def provider(values):
            calls.append(values)
            return {'status': 'empty', 'offers': []}
        bot = Conversation(provider)
        def say(text):
            return bot.reply('test', text, today=date(2026, 9, 23))
        for message in ['oi', 'CNF', 'GRU', '23/10/2026', '30/10/2026', '2', '1', 'sem limite']:
            last = say(message)
        self.assertIn('Confirmar', last)
        self.assertEqual(calls, [])
        self.assertIn('não retornou', say('sim'))
        self.assertEqual(calls[0]['adults'], '2')
        self.assertIn('data de ida', say('datas'))
        self.assertEqual(bot.sessions['test'].step, 'departure')

    def test_live_links_follow_display_order(self):
        offer = normalize(self.raw, self.client, self.values)
        bot = Conversation(lambda _: {'status': 'success', 'offers': [offer]})
        for text in ['oi', 'CNF', 'GRU', '23/10/2026', '30/10/2026', '2', '1', 'sem limite', 'sim']:
            answer = bot.reply('test', text, today=date(2026, 9, 23))
        self.assertIn('900,00', answer)
        self.assertLess(len(answer), 4096)
        self.assertIn(offer['url'], bot.reply('test', 'link 1'))
        self.assertNotIn('https', bot.reply('test', 'link 0'))

    def test_provider_timeout_is_explicit(self):
        import subprocess
        with patch('atlas.flights.subprocess.run', side_effect=subprocess.TimeoutExpired('provider', 55)):
            self.assertEqual(search(self.values)['status'], 'timeout')
