import io
import json
import unittest

from atlas.providers.clickbus import normalize, resolve_place, search


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def response(value):
    return Response(json.dumps(value).encode())


class ClickBusAdapterTests(unittest.TestCase):
    def setUp(self):
        self.config = {'CLICKBUS_ACCESS_TOKEN': 'secret-test-token'}
        self.values = {'origin': 'Belo Horizonte', 'destination': 'São Paulo',
                       'departure': '23/10/2026', 'adults': '2',
                       'priority': '1', 'budget': None}

    def trip(self):
        return {
            'price': 100, 'discountedPrice': 90, 'duration': '06:30',
            'availableSeats': 4, 'type': 'direct',
            'departure': {'datetime': '2026-10-23T08:00:00-03:00', 'station': 'BH'},
            'arrival': {'datetime': '2026-10-23T14:30:00-03:00', 'station': 'Tietê'},
            'company': {'name': 'Viação Exemplo'},
            'serviceClass': {'name': 'Executivo'},
        }

    def test_normalizes_documented_trip_and_multiplies_ticket_price(self):
        result = normalize(self.trip(), 2)
        self.assertEqual(result['price'], '180.00')
        self.assertEqual(result['duration'], 390)
        self.assertEqual(result['connections'], 0)
        self.assertIsNone(result['url'])

    def test_resolves_highest_weight_exact_city(self):
        def opener(request, timeout):
            self.assertNotIn('secret-test-token', request.full_url)
            self.assertEqual(timeout, 12)
            return response({'content': [
                {'name': 'São Paulo', 'slug': 'sp-low', 'weight': 1},
                {'name': 'São Paulo', 'slug': 'sao-paulo-tiete-sp', 'weight': 10},
            ]})
        self.assertEqual(resolve_place('São Paulo', self.config, opener=opener), 'sao-paulo-tiete-sp')

    def test_search_uses_places_then_trips_and_returns_no_purchase_url(self):
        requests = []
        def opener(request, timeout):
            requests.append(request)
            if '/places/' in request.full_url:
                slug = 'belo-horizonte-mg' if len(requests) == 1 else 'sao-paulo-tiete-sp'
                return response([{'name': 'City', 'slug': slug, 'weight': 1}])
            return response({'departures': [self.trip()]})
        result = search(self.values, self.config, opener=opener)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['offers'][0]['price'], '180.00')
        self.assertIsNone(result['offers'][0]['url'])
        self.assertIn('departureDate=2026-10-23', requests[-1].full_url)
        self.assertIn('Authorization', requests[-1].headers)

    def test_missing_credentials_never_calls_network(self):
        result = search(self.values, {}, opener=lambda *args: self.fail('network call'))
        self.assertEqual(result['status'], 'unauthorized')

    def test_rejects_unapproved_api_host(self):
        config = dict(self.config, CLICKBUS_API_BASE_URL='https://attacker.test/partners/api')
        self.assertEqual(search(self.values, config, opener=lambda *args: self.fail('network call'))['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
