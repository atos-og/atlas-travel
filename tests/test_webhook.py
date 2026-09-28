import hashlib
import hmac
import tempfile
import unittest
from pathlib import Path

from atlas.webhook import ExclusiveHTTPServer, Handler, ready, record_receipt, server_address, valid_signature, verify_challenge


class WebhookTests(unittest.TestCase):
    def test_readiness_checks_configuration_and_writable_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {'WHATSAPP_VERIFY_TOKEN': 'verify', 'META_APP_SECRET': 'secret'}
            self.assertTrue(ready(base, root))
            self.assertFalse(ready({}, root))
            self.assertFalse(ready(dict(base, ATLAS_NLU_ENABLED='true'), root))
            replies = dict(base, ATLAS_WHATSAPP_REPLIES_ENABLED='true')
            self.assertFalse(ready(replies, root))
            replies.update(WHATSAPP_ACCESS_TOKEN='token', WHATSAPP_PHONE_NUMBER_ID='123',
                           ATLAS_ALLOWED_WHATSAPP_USER='57123', META_GRAPH_API_VERSION='v23.0')
            self.assertTrue(ready(replies, root))

    def test_server_address_defaults_and_hosted_port(self):
        self.assertEqual(server_address({}), ('127.0.0.1', 8787))
        self.assertEqual(server_address({'ATLAS_WEBHOOK_HOST': '0.0.0.0', 'PORT': '8080'}),
                         ('0.0.0.0', 8080))
        self.assertEqual(server_address({'ATLAS_WEBHOOK_PORT': '9000'}), ('127.0.0.1', 9000))

    def test_server_address_rejects_unbounded_values(self):
        for config in ({'ATLAS_WEBHOOK_HOST': ''}, {'ATLAS_WEBHOOK_HOST': 'example.com'},
                       {'PORT': '0'}, {'PORT': '65536'}, {'PORT': 'eight'}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                server_address(config)

    def test_second_server_cannot_bind_same_port(self):
        first = ExclusiveHTTPServer(('127.0.0.1', 0), Handler)
        self.addCleanup(first.server_close)
        with self.assertRaises(OSError):
            second = ExclusiveHTTPServer(first.server_address, Handler)
            second.server_close()

    def test_challenge_requires_exact_mode_and_token(self):
        query = "hub.mode=subscribe&hub.verify_token=test&hub.challenge=123"
        self.assertEqual(verify_challenge(query, "test"), "123")
        self.assertIsNone(verify_challenge(query, "wrong"))
        self.assertIsNone(verify_challenge(query, ""))
        self.assertIsNone(verify_challenge(query + "&hub.challenge=456", "test"))
        self.assertIsNone(verify_challenge(query.replace("subscribe", "other"), "test"))

    def test_signature_rejects_tampering(self):
        body = b'{"object":"whatsapp_business_account"}'
        signature = "sha256=" + hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
        self.assertTrue(valid_signature(body, signature, "test-secret"))
        self.assertFalse(valid_signature(body + b" ", signature, "test-secret"))
        self.assertFalse(valid_signature(body, signature, ""))
        self.assertFalse(valid_signature(body, "", "test-secret"))

    def test_duplicate_receipts_survive_new_connections_and_store_no_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipts.db"
            body = b'private-message-content'
            self.assertTrue(record_receipt(body, path))
            self.assertFalse(record_receipt(body, path))
            self.assertNotIn(body, path.read_bytes())
