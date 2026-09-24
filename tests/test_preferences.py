import tempfile
import unittest
from datetime import date
from pathlib import Path
from atlas.preferences import Preferences
from atlas.conversation import Conversation, Session


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'preferences.db'
        self.values = {'origin': 'CNF', 'destination': 'GRU', 'departure': '23/10/2027',
                       'return': '30/10/2027', 'adults': '2', 'priority': '1', 'budget': '1000',
                       'result': {'status': 'empty', 'offers': []}}
        self.bot = Conversation(lambda _: self.fail('Preferences must not search'), preferences=Preferences(self.path))
        self.bot.sessions['u'] = Session('complete', dict(self.values))

    def send(self, text):
        return self.bot.reply('u', text, today=date(2026, 9, 24))

    def test_only_explicit_save_persists_selected_fields(self):
        self.assertEqual(Preferences(self.path).load('u'), {})
        self.send('salvar preferências')
        self.assertEqual(Preferences(self.path).load('u'), {'origin': 'CNF', 'adults': '2', 'priority': '1'})
        self.assertEqual(Preferences(self.path).load('other'), {})

    def test_cancel_keeps_preferences_but_does_not_apply_them_automatically(self):
        self.send('salvar preferências')
        greeting = self.send('cancelar')
        self.assertIn('usar preferências', greeting)
        self.assertEqual(self.bot.sessions['u'].values, {})
        self.send('usar preferências')
        self.assertEqual(self.bot.sessions['u'].step, 'destination')
        self.assertEqual(self.bot.sessions['u'].values['adults'], '2')

    def test_reusing_preferences_invalidates_old_fares_and_requires_confirmation(self):
        self.send('salvar preferências')
        self.bot.sessions['u'].values['adults'] = '3'
        reply = self.send('usar preferências')
        self.assertIn('Confirmar busca', reply)
        self.assertNotIn('result', self.bot.sessions['u'].values)
        self.assertEqual(self.bot.sessions['u'].values['adults'], '2')

    def test_delete_is_scoped_and_preserves_current_trip(self):
        self.send('salvar preferências')
        self.bot.preferences.save('other', self.values)
        self.send('apagar preferências')
        self.assertEqual(Preferences(self.path).load('u'), {})
        self.assertEqual(self.bot.sessions['u'].values, self.values)
        self.assertTrue(Preferences(self.path).load('other'))

    def test_incomplete_save_does_not_overwrite_existing_profile(self):
        self.send('salvar preferências')
        self.send('cancelar')
        self.assertIn('Primeiro informe', self.send('salvar preferências'))
        self.assertEqual(Preferences(self.path).load('u')['origin'], 'CNF')

    def test_same_origin_destination_is_clarified_when_reusing(self):
        self.send('salvar preferências')
        self.bot.sessions['u'].values['destination'] = 'CNF'
        self.assertIn('diferente', self.send('usar preferências'))
        self.assertNotIn('destination', self.bot.sessions['u'].values)
