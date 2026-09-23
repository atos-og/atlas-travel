import hashlib
import hmac
import tempfile
import unittest
from pathlib import Path

from atlas.webhook import ExclusiveHTTPServer, Handler, record_receipt, valid_signature, verify_challenge


class WebhookTests(unittest.TestCase):
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
