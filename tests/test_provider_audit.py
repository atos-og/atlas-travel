import json
import unittest

from atlas.provider_audit import audit


class ProviderAuditTests(unittest.TestCase):
    def setUp(self):
        self.values = {'origin': 'CNF', 'destination': 'GRU', 'departure': '23/10/2027',
                       'return': '30/10/2027', 'adults': '2', 'priority': '1'}

    def test_success_is_sanitized_and_summarized(self):
        offers = [{
            'price': '900.50', 'journeys': [{}, {}],
            'url': 'https://www.google.com/travel/flights/booking?tfs=private-token',
        }, {
            'price': '1200', 'journeys': [{}, {}], 'url': None,
        }]
        result = audit(self.values, provider=lambda _: {
            'status': 'success', 'offers': offers, 'checked_at': 'test time'})
        self.assertTrue(result['ok'])
        self.assertEqual(result['lowest_brl'], '900.50')
        self.assertEqual(result['offers_with_links'], 1)
        self.assertEqual(result['link_hosts'], ['www.google.com'])
        self.assertNotIn('private-token', json.dumps(result))

    def test_empty_or_incomplete_response_fails_honestly(self):
        result = audit(self.values, provider=lambda _: {'status': 'empty', 'offers': []})
        self.assertFalse(result['ok'])
        self.assertEqual(result['normalized_offers'], 0)
        result = audit(self.values, provider=lambda _: {
            'status': 'success', 'offers': [{'price': '10', 'journeys': [{}]}]})
        self.assertFalse(result['ok'])


if __name__ == '__main__':
    unittest.main()
