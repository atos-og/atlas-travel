import io
import json
import unittest
from urllib.error import HTTPError
from atlas.check import check, token_check, REQUIRED


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.config = dict.fromkeys(REQUIRED, 'secret-sentinel')
        self.config.update(META_GRAPH_API_VERSION='v26.0', WHATSAPP_PHONE_NUMBER_ID='123')

    def test_default_is_local_only_and_never_prints_secrets(self):
        calls = []
        def open_local(request, **kwargs):
            calls.append(request)
            return io.BytesIO(b'atlas-test')
        result = check(self.config, opener=open_local)
        self.assertEqual(calls, ['http://127.0.0.1:8787/health'])
        self.assertFalse(result['meta']['checked'])
        self.assertNotIn('secret-sentinel', json.dumps(result))

    def test_meta_check_uses_header_and_matches_number_without_exposing_it(self):
        def open_request(request, **kwargs):
            if isinstance(request, str):
                return io.BytesIO(b'atlas-test')
            self.assertEqual(request.headers['Authorization'], 'Bearer secret-sentinel')
            self.assertNotIn('secret-sentinel', request.full_url)
            return io.BytesIO(b'{"id":"123"}')
        result = check(self.config, meta=True, opener=open_request)
        self.assertTrue(result['meta']['ok'])
        self.assertNotIn('123', json.dumps(result))

    def test_expiry_is_actionable_without_raw_api_messages(self):
        def expired(request, **kwargs):
            if isinstance(request, str):
                return io.BytesIO(b'atlas-test')
            body = b'{"error":{"code":190,"error_subcode":463,"message":"secret-sentinel"}}'
            raise HTTPError('https://graph.facebook.com', 400, '', {}, io.BytesIO(body))
        result = check(self.config, meta=True, opener=expired)
        self.assertEqual(result['meta']['reason'], 'token_expired')
        self.assertNotIn('secret-sentinel', json.dumps(result))

    def test_missing_configuration_does_not_call_external_api(self):
        result = check({}, meta=True, opener=lambda *a, **k: io.BytesIO(b'other-service'))
        self.assertFalse(result['configuration']['ok'])
        self.assertFalse(result['local_server']['ok'])
        self.assertFalse(result['meta']['checked'])

    def test_network_failure_and_malformed_response_are_reported(self):
        def failure(*args, **kwargs):
            raise TimeoutError('secret-sentinel')
        result = check(self.config, meta=True, opener=failure)
        self.assertFalse(result['local_server']['ok'])
        self.assertEqual(result['meta']['reason'], 'network_or_response')
        self.assertNotIn('secret-sentinel', json.dumps(result))

    def inspect_token(self, **metadata):
        self.config['META_APP_ID'] = '456'
        data = {'is_valid': True, 'app_id': '456', **metadata}
        return token_check(self.config, now=100000,
                           opener=lambda *a, **k: io.BytesIO(json.dumps({'data': data}).encode()))

    def test_token_expiry_warning_and_data_access_deadline(self):
        result = self.inspect_token(expires_at=103600, data_access_expires_at=99999)
        self.assertEqual(result['expires_at']['status'], 'expiring_soon')
        self.assertEqual(result['expires_at']['remaining_seconds'], 3600)
        self.assertEqual(result['data_access_expires_at']['status'], 'expired')
        self.assertFalse(result['ok'])
        self.assertNotIn('secret-sentinel', json.dumps(result))
        self.assertNotIn('456', json.dumps(result))

    def test_unknown_and_unscheduled_expiry_are_distinct(self):
        result = self.inspect_token(expires_at=0)
        self.assertEqual(result['expires_at']['status'], 'no_scheduled_expiry')
        self.assertEqual(result['data_access_expires_at']['status'], 'unknown')
        self.assertTrue(result['ok'])

    def test_token_rejects_wrong_app_invalid_token_and_bad_metadata(self):
        self.assertFalse(self.inspect_token(app_id='789')['ok'])
        self.assertFalse(self.inspect_token(is_valid=False)['ok'])
        for value in (True, -1, 'secret-sentinel', 10**30):
            self.assertEqual(self.inspect_token(expires_at=value)['reason'], 'network_or_response')

    def test_token_network_failure_does_not_echo_request_secrets(self):
        self.config['META_APP_ID'] = '456'
        def failure(request, **kwargs):
            raise RuntimeError(request.full_url)
        result = token_check(self.config, opener=failure)
        self.assertEqual(result, {'ok': False, 'reason': 'network_or_response'})

    def test_token_requires_explicit_app_configuration(self):
        def unexpected(*args, **kwargs):
            self.fail('No network request should be made')
        self.assertEqual(token_check(self.config, opener=unexpected)['reason'], 'configuration')
