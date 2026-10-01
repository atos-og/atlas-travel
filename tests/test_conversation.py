import unittest
from datetime import date

from atlas.conversation import Conversation, Session


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.bot = Conversation()

    def send(self, message, user="a"):
        return self.bot.reply(user, message, today=date(2026, 9, 23))

    def test_complete_flow_does_not_claim_live_search(self):
        for message in ["oi", "BH", "Bogotá", "12/11/2026", "19/11/2026"]:
            self.send(message)
        answer = self.send("3")
        self.assertIn("sem paradas", answer)
        self.assertIn("Não realizei uma busca", answer)
        self.assertNotIn("R$", answer)

    def test_dates_rejected_without_advancing(self):
        for message in ["oi", "BH", "Bogotá"]:
            self.send(message)
        self.assertIn("válida", self.send("31/02/2027"))
        self.assertIn("passado", self.send("01/01/2026"))
        self.send("12/11/2026")
        self.assertIn("anterior", self.send("11/11/2026"))
        self.assertEqual(self.bot.sessions["a"].step, "return")

    def test_users_have_independent_sessions(self):
        self.send("oi")
        self.send("BH")
        self.send("oi", user="b")
        self.assertEqual(self.bot.sessions["b"].values, {})
        self.assertEqual(self.bot.sessions["a"].values, {"origin": "BH"})

    def test_cancel_clears_trip(self):
        self.send("oi")
        self.send("BH")
        self.send("cancelar")
        self.assertEqual(self.bot.sessions["a"].values, {})
        self.assertEqual(self.bot.sessions["a"].step, "origin")

    def test_controlled_faq_does_not_need_live_search(self):
        answer = self.send('duvida bagagem')
        self.assertIn('não confirma bagagem', answer)
        self.assertIn('fornecedor', answer)

    def test_controlled_scope_answers_do_not_promise_future_features(self):
        self.assertIn('ainda não consulta tarifas ao vivo', self.send('duvida onibus'))
        self.assertIn('credenciamento', self.send('duvida onibus'))
        self.assertIn('ainda não monitora', self.send('duvida alertas'))
        self.assertIn('São Paulo, Bogotá ou Rio de Janeiro', self.send('duvida cobertura'))
        self.assertIn('Ainda não avalia', self.send('duvida conforto'))
        self.assertIn('Por nada', self.send('obrigado atlas'))

    def test_trip_summary_uses_only_saved_session_data(self):
        self.bot.sessions['a'] = Session('complete', {
            'origin': 'CNF', 'destination': 'BOG', 'departure': '12/11/2026',
            'return': '19/11/2026', 'adults': '2', 'budget': '2500',
            '_itinerary': {'city': 'bogota', 'days': 2, 'interest': 'cultura',
                           'pace': 'tranquilo', 'plan': [{'date': None, 'places': ['botero']}]},
        })
        answer = self.send('resumo da viagem')
        self.assertIn('CNF → BOG', answer)
        self.assertIn('R$ 2.500,00', answer)
        self.assertIn('Cidade: Bogotá', answer)
        self.assertNotIn('_itinerary', answer)

    def test_checklist_distinguishes_domestic_and_international_without_legal_claims(self):
        self.bot.sessions['a'] = Session('destination', {'destination': 'GRU'})
        domestic = self.send('checklist da viagem')
        self.assertIn('Documento oficial', domestic)
        self.assertNotIn('Passaporte válido', domestic)
        self.bot.sessions['a'].values['destination'] = 'BOG'
        international = self.send('checklist da viagem')
        self.assertIn('Passaporte válido', international)
        self.assertIn('fontes oficiais', international)
        self.assertIn('apoio geral', international)

    def test_recommendation_and_comparison_use_only_saved_offers(self):
        bot = Conversation(lambda _: None)
        offers = [
            {'price': '900.00', 'duration': 300, 'stops': 1, 'journeys': [{'id': 'a'}], 'url': 'https://google.com/travel/flights'},
            {'price': '700.00', 'duration': 420, 'stops': 0, 'journeys': [{'id': 'b'}], 'url': 'https://google.com/travel/flights'},
        ]
        bot.sessions['a'] = Session('complete', {
            'origin': 'CNF', 'destination': 'GRU', 'departure': '12/11/2026',
            'return': '19/11/2026', 'adults': '1', 'priority': '1', 'budget': None,
            'result': {'status': 'success', 'offers': offers},
        })
        recommendation = bot.reply('a', 'recomendar oferta', today=date(2026, 9, 23))
        self.assertIn('R$ 700,00', recommendation)
        self.assertIn('link 1', recommendation)
        comparison = bot.reply('a', 'comparar ofertas', today=date(2026, 9, 23))
        self.assertLess(comparison.index('R$ 700,00'), comparison.index('R$ 900,00'))
        self.assertNotIn('bagagem incluída', comparison)

    def test_bus_overlay_preserves_flight_data_and_can_return_to_flights(self):
        bot = Conversation(lambda _: {'status': 'empty', 'offers': []},
                           bus_search=lambda _: {'status': 'empty', 'offers': []})
        bot.sessions['a'] = Session('departure', {'origin': 'CNF', 'destination': 'GRU'})
        answer = bot.reply('a', 'ônibus', today=date(2026, 9, 23))
        self.assertIn('De qual cidade', answer)
        self.assertEqual(bot.sessions['a'].values['origin'], 'CNF')
        self.assertIn('Qual é a data de ida', bot.reply('a', 'voos', today=date(2026, 9, 23)))
        self.assertFalse(bot.sessions['a'].values['_bus']['active'])

    def test_trip_summary_includes_saved_bus_query(self):
        self.bot.sessions['a'] = Session('origin', {'_bus': {
            'active': False, 'stage': 'done', 'origin': 'Belo Horizonte',
            'destination': 'São Paulo', 'departure': '12/11/2026', 'adults': '2',
            'result': {'status': 'success', 'offers': [{'price': '100'}]},
        }})
        answer = self.send('resumo da viagem')
        self.assertIn('Ônibus', answer)
        self.assertIn('Belo Horizonte → São Paulo', answer)
        self.assertIn('1 opção', answer)


if __name__ == "__main__":
    unittest.main()
