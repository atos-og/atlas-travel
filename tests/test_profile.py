import io
import json
import unittest

from atlas.profile import check


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.config = {'META_GRAPH_API_VERSION': 'v26.0',
                       'WHATSAPP_PHONE_NUMBER_ID': '123',
                       'WHATSAPP_ACCESS_TOKEN': 'secret-sentinel'}

    def test_profile_check_reports_only_branding_facts(self):
        replies = iter((
            {'id': '123', 'verified_name': 'Atlas', 'name_status': 'APPROVED',
             'quality_rating': 'GREEN'},
            {'data': [{'about': 'Travel', 'description': 'Assistant',
                       'profile_picture_url': 'https://private.example/photo',
                       'websites': ['https://example.com']}]},
        ))

        def opener(request, **kwargs):
            self.assertEqual(request.headers['Authorization'], 'Bearer secret-sentinel')
            self.assertNotIn('secret-sentinel', request.full_url)
            return io.BytesIO(json.dumps(next(replies)).encode())

        result = check(self.config, opener=opener)
        self.assertTrue(result['ok'])
        self.assertTrue(result['atlas_name_live'])
        rendered = json.dumps(result)
        self.assertNotIn('secret-sentinel', rendered)
        self.assertNotIn('private.example', rendered)
        self.assertNotIn('123', rendered)

    def test_incomplete_or_test_profile_is_not_ready(self):
        replies = iter((
            {'id': '123', 'verified_name': 'Test Number', 'name_status': 'AVAILABLE_WITHOUT_REVIEW'},
            {'data': [{}]},
        ))
        result = check(self.config, opener=lambda *args, **kwargs:
                       io.BytesIO(json.dumps(next(replies)).encode()))
        self.assertFalse(result['ok'])
        self.assertFalse(result['atlas_name_live'])
        self.assertFalse(result['profile_picture'])
        self.assertEqual(check({}, opener=lambda *args: self.fail())['reason'], 'configuration')


if __name__ == '__main__':
    unittest.main()
