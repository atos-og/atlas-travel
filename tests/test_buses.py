import unittest
from datetime import date
from unittest.mock import Mock

from atlas.buses import format_results, handle, normalize_offer, rank
from atlas.conversation import Conversation, Session
from atlas.nlu import SemanticMessage


def offer(price='120.00', duration=480, connections=0, service_class='Executivo'):
    return {
        'price': price,
        'duration': duration,
        'connections': connections,
        'available_seats': 8,
        'departure': {'place': 'Belo Horizonte', 'time': '08:00'},
        'arrival': {'place': 'São Paulo - Tietê', 'time': '16:00'},
        'company': 'Viação Exemplo',
        'service_class': service_class,
    }


class BusDomainTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 9, 29)
        self.session = Session()
        self.requests = []

    def search(self, values):
        self.requests.append(values)
        return {'status': 'success', 'checked_at': '29/09/2026 15:00 UTC',
                'offers': [offer(), offer('180', 420, 1, 'Leito')]}

    def send(self, text):
        return handle(self.session, text, self.today, self.search)

    def test_unconfigured_source_does_not_collect_or_invent_a_fare(self):
        answer = handle(self.session, 'quero passagem de ônibus', self.today)
        self.assertIn('credenciamento', answer)
        self.assertIn('não vai inventar preços', answer)
        self.assertFalse(self.session.values['_bus']['active'])

    def test_guided_search_requires_confirmation(self):
        self.assertIn('De qual cidade', self.send('ônibus'))
        for value in ('Belo Horizonte', 'São Paulo', '23/10/2026', '2', '1', 'até 400'):
            answer = self.send(value)
        self.assertIn('Confirmar ônibus', answer)
        self.assertEqual(self.requests, [])
        answer = self.send('bora')
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.requests[0]['budget'], '400.00')
        self.assertIn('R$ 120,00 no total', answer)

    def test_explicit_city_route_skips_two_questions(self):
        answer = self.send('quero ir de BH pra São Paulo de ônibus')
        self.assertIn('data da viagem', answer)
        self.assertEqual(self.session.values['_bus']['origin'], 'bh')
        self.assertEqual(self.session.values['_bus']['destination'], 'sao paulo')

    def test_ranking_is_bounded_and_uses_declared_class_for_comfort(self):
        options = [offer('90', 600, 0, 'Convencional'), offer('150', 420, 1, 'Leito'),
                   offer('120', 480, 0, 'Executivo')]
        self.assertEqual(rank(options, '1')[0]['price'], '90.00')
        self.assertEqual(rank(options, '2')[0]['price'], '150.00')
        self.assertEqual(rank(options, '3')[0]['price'], '120.00')
        self.assertEqual(rank(options, '4')[0]['service_class'], 'Leito')
        self.assertEqual([item['price'] for item in rank(options, '1', '100')], ['90.00'])

    def test_invalid_or_insufficient_offer_is_removed(self):
        self.assertIsNone(normalize_offer({'price': '-1'}, 1))
        raw = offer()
        raw['available_seats'] = 1
        self.assertIsNone(normalize_offer(raw, 2))
        self.assertEqual(rank([raw], '1', adults=2), [])

    def test_failure_copy_never_estimates_a_price(self):
        values = {'origin': 'BH', 'destination': 'São Paulo', 'departure': '23/10/2026',
                  'adults': '1', 'priority': '1', 'budget': None}
        answer = format_results({'status': 'unauthorized'}, values)
        self.assertIn('não está credenciada', answer)
        self.assertIn('Nenhum preço foi estimado', answer)

    def test_semantic_request_prefills_every_explicit_bus_choice(self):
        semantic = SemanticMessage('bus', {
            'origin': 'Belo Horizonte', 'destination': 'São Paulo',
            'departure': '23/10/2027', 'adults': '2',
            'priority': '2', 'budget': '500',
        })
        search = Mock(return_value={'status': 'empty', 'offers': []})
        bot = Conversation(bus_search=search, interpreter=lambda *args: semantic)
        answer = bot.reply('semantic-bus', 'pedido livre', today=self.today)
        state = bot.sessions['semantic-bus'].values['_bus']
        self.assertIn('Confirmar ônibus', answer)
        self.assertEqual(state['stage'], 'confirm')
        self.assertEqual(state['adults'], '2')
        self.assertEqual(state['budget'], '500.00')
        search.assert_not_called()


if __name__ == '__main__':
    unittest.main()
