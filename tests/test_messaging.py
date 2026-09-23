import tempfile
import unittest
from pathlib import Path
from atlas.messaging import database, ingest, process_one


class MessagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'test.db'
        self.config = {'ATLAS_ALLOWED_WHATSAPP_USER': '570000000000',
                       'WHATSAPP_PHONE_NUMBER_ID': '123', 'WHATSAPP_ACCESS_TOKEN': 'fake',
                       'ATLAS_WHATSAPP_REPLIES_ENABLED': 'true'}
        self.sent = []

    def payload(self, mid='m1', user='570000000000', text='oi', timestamp='100'):
        return {'entry': [{'changes': [{'field': 'messages', 'value': {
            'metadata': {'phone_number_id': '123'}, 'messages': [
                {'id': mid, 'from': user, 'type': 'text', 'text': {'body': text}, 'timestamp': timestamp}
            ]}}]}]}

    def send(self, config, user, text):
        self.sent.append(text)
        return 'sent', 'outbound-' + str(len(self.sent)), None

    def test_duplicates_and_sessions_survive_reopening(self):
        p = self.payload()
        self.assertEqual(ingest(p, self.config, self.path, now=100), 1)
        self.assertEqual(ingest(p, self.config, self.path, now=100), 0)
        process_one(self.config, self.path, self.send, now=100)
        self.assertFalse(process_one(self.config, self.path, self.send, now=100))
        ingest(self.payload(mid='m2', text='BH'), self.config, self.path, now=100)
        process_one(self.config, self.path, self.send, now=100)
        self.assertEqual(len(self.sent), 2)
        self.assertIn('Para onde', self.sent[-1])

    def test_other_user_old_messages_and_missing_allowlist_are_ignored(self):
        self.assertEqual(ingest(self.payload(user='other'), self.config, self.path, now=100), 0)
        self.assertEqual(ingest(self.payload(), self.config, self.path, now=100000), 0)
        config = dict(self.config, ATLAS_ALLOWED_WHATSAPP_USER='')
        self.assertEqual(ingest(self.payload(), config, self.path, now=100), 0)
        self.assertEqual(ingest({'entry': []}, self.config, self.path, now=100), 0)

    def test_uncertain_send_is_not_retried(self):
        ingest(self.payload(), self.config, self.path, now=100)
        process_one(self.config, self.path, lambda *args: ('uncertain', None, 'timeout'), now=100)
        self.assertFalse(process_one(self.config, self.path, self.send, now=100))
        with database(self.path) as db:
            self.assertEqual(db.execute('select state from inbox').fetchone()[0], 'uncertain')

    def test_disabled_replies_do_not_send(self):
        ingest(self.payload(), self.config, self.path, now=100)
        config = dict(self.config, ATLAS_WHATSAPP_REPLIES_ENABLED='false')
        self.assertFalse(process_one(config, self.path, self.send, now=100))
        self.assertEqual(self.sent, [])
