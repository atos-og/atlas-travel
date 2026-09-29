import io
import json
import unittest
from urllib.error import HTTPError

from atlas.callback import callback_url, subscription, synchronize


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class CallbackTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "META_APP_ID": "123456",
            "META_APP_SECRET": "secret-sentinel",
            "META_GRAPH_API_VERSION": "v24.0",
            "WHATSAPP_VERIFY_TOKEN": "verify-sentinel",
        }

    def test_callback_url_is_strict_and_adds_webhook_path(self):
        self.assertEqual(callback_url("https://atlas.example"), "https://atlas.example/webhook")
        self.assertEqual(
            callback_url("https://atlas.example/webhook/"), "https://atlas.example/webhook")
        for value in (
                "http://atlas.example", "https://user@atlas.example", "https://atlas.example/other",
                "https://atlas.example/webhook?token=x", "https://atlas.example:8443/webhook"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                callback_url(value)

    def test_subscription_returns_only_safe_readiness_facts(self):
        captured = {}

        def opener(request, timeout):
            captured.update(request=request, timeout=timeout)
            return Response(json.dumps({"data": [{
                "object": "whatsapp_business_account", "active": True,
                "callback_url": "https://atlas.example/webhook",
                "fields": [{"name": "messages"}, {"name": "account_update"}],
            }]}).encode())

        result = subscription(self.config, opener=opener)
        self.assertEqual(result, {
            "active": True, "callback_url": "https://atlas.example/webhook", "messages": True})
        self.assertEqual(captured["timeout"], 15)
        self.assertNotIn("secret-sentinel", captured["request"].full_url)
        self.assertNotIn("verify-sentinel", captured["request"].full_url)

    def test_synchronize_updates_then_verifies_exact_subscription(self):
        requests = []

        def opener(request, timeout):
            requests.append(request)
            if request.data is not None:
                return Response(b'{"success": true}')
            return Response(json.dumps({"data": [{
                "object": "whatsapp_business_account", "active": True,
                "callback_url": "https://atlas.example/webhook",
                "fields": [{"name": "messages"}],
            }]}).encode())

        result = synchronize(
            self.config, "https://atlas.example", opener=opener, sleeper=lambda _: None)
        self.assertTrue(result["ok"])
        self.assertEqual(len(requests), 2)
        posted = requests[0].data.decode()
        self.assertIn("callback_url=https%3A%2F%2Fatlas.example%2Fwebhook", posted)
        self.assertIn("verify_token=verify-sentinel", posted)
        self.assertNotIn("secret-sentinel", posted)

    def test_synchronize_tolerates_eventually_consistent_readback(self):
        reads = 0
        delays = []

        def opener(request, timeout):
            nonlocal reads
            if request.data is not None:
                return Response(b'{"success": true}')
            reads += 1
            callback = "https://old.example/webhook" if reads == 1 else "https://atlas.example/webhook"
            return Response(json.dumps({"data": [{
                "object": "whatsapp_business_account", "active": True,
                "callback_url": callback, "fields": [{"name": "messages"}],
            }]}).encode())

        result = synchronize(
            self.config, "https://atlas.example", opener=opener, sleeper=delays.append)
        self.assertTrue(result["ok"])
        self.assertEqual(reads, 2)
        self.assertEqual(delays, [0.25])

    def test_synchronize_rejects_bad_config_and_verification_mismatch(self):
        self.assertEqual(
            synchronize({}, "https://atlas.example", opener=lambda *a, **k: None),
            {"ok": False, "reason": "configuration"})

        calls = 0
        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return Response(b'{"success": true}')
            return Response(b'{"data": []}')

        result = synchronize(
            self.config, "https://atlas.example", opener=opener, sleeper=lambda _: None)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "verification_failed")

    def test_synchronize_reports_bounded_api_errors(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 403, "secret provider message", {}, None)

        result = synchronize(self.config, "https://atlas.example", opener=opener)
        self.assertEqual(result, {"ok": False, "reason": "credentials_or_access", "code": 403})
        self.assertNotIn("secret", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
