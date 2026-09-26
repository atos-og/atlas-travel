import unittest
from datetime import date
from atlas.language import parse_date, choice, is_greeting
from atlas.conversation import Conversation


class LanguageTests(unittest.TestCase):
    def test_only_standalone_greetings_are_recognized(self):
        for text in ('oi', 'Olá!', 'bom dia Atlas', 'boa noite'):
            self.assertTrue(is_greeting(text))
        self.assertFalse(is_greeting('Bom dia, quero ir de Confins para Bogotá'))

    def test_dates_and_relative_year(self):
        today = date(2026, 9, 23)
        for text in ['dia 23 de outubro desse ano', '23 de outubro de 2026', 'quero ir no dia 23 de outubro deste ano', '23/10', '23-10-2026']:
            with self.subTest(text=text):
                self.assertEqual(parse_date(text, today), date(2026, 10, 23))
        self.assertEqual(parse_date('23 de outubro do próximo ano', today), date(2027, 10, 23))
        self.assertEqual(parse_date('amanhã', date(2026, 12, 31)), date(2027, 1, 1))
        self.assertEqual(parse_date('em 3 dias', today), date(2026, 9, 26))
        self.assertEqual(parse_date('uma semana depois', today, date(2026, 10, 23)), date(2026, 10, 30))

    def test_invalid_or_ambiguous_dates_are_not_guessed(self):
        for text in ['dia 23', 'outubro', '23 ou 24 de outubro', '31 de fevereiro de 2026', '29/02/2026', 'sexta-feira', '7 dias depois']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_date(text, date(2026, 9, 23))

    def test_natural_choices(self):
        self.assertEqual(choice('prefiro a mais barata', 'priority'), '1')
        self.assertEqual(choice('quero a mais em conta', 'priority'), '1')
        self.assertEqual(choice('menos tempo', 'priority'), '2')
        self.assertEqual(choice('sem escalas', 'priority'), '3')
        self.assertEqual(choice('sem conexão', 'priority'), '3')
        self.assertEqual(choice('somos duas pessoas', 'adults'), '2')
        self.assertEqual(choice('somos um casal', 'adults'), '2')
        self.assertEqual(choice('vou sozinho', 'adults'), '1')
        self.assertEqual(choice('mais confortável', 'priority'), 'mais confortável')

    def test_full_flow_confirms_interpreted_dates(self):
        requests = []
        def search(v):
            requests.append(v)
            return {'status': 'empty', 'offers': []}
        bot = Conversation(search)
        for text in ['oi', 'saio de Confins', 'quero ir para Guarulhos', 'dia 23 de outubro desse ano', '7 dias depois', 'duas pessoas', 'a mais barata', 'sem limite']:
            reply = bot.reply('user', text, today=date(2026, 9, 23))
        self.assertIn('23/10/2026', reply)
        self.assertIn('30/10/2026', reply)
        self.assertEqual(requests, [])
        bot.reply('user', 'pode buscar', today=date(2026, 9, 23))
        self.assertEqual(requests[0]['adults'], '2')
        self.assertEqual(requests[0]['priority'], '1')
