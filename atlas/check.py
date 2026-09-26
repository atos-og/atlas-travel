"""Read-only development diagnostics. Never print credentials or recipient IDs."""

import argparse
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from .nlu import DEFAULT_MODEL, interpret
from .webhook import settings


REQUIRED = ('WHATSAPP_VERIFY_TOKEN', 'META_APP_SECRET', 'WHATSAPP_ACCESS_TOKEN',
            'WHATSAPP_PHONE_NUMBER_ID', 'META_GRAPH_API_VERSION', 'ATLAS_ALLOWED_WHATSAPP_USER')


def groq_check(config, *, opener=urlopen):
    """Send one synthetic intent request without exposing credentials or traveler data."""
    enabled = config.get('ATLAS_NLU_ENABLED') == 'true'
    model = config.get('GROQ_MODEL') or DEFAULT_MODEL
    if not enabled:
        return {'enabled': False, 'configured': bool(config.get('GROQ_API_KEY')),
                'checked': False, 'model': model}
    if not config.get('GROQ_API_KEY'):
        return {'enabled': True, 'configured': False, 'checked': False,
                'ok': False, 'reason': 'configuration', 'model': model}
    failure = {}

    def tracked(request, **kwargs):
        try:
            return opener(request, **kwargs)
        except HTTPError as error:
            failure['reason'] = {
                400: 'request_or_model',
                401: 'invalid_key',
                403: 'access_denied',
                429: 'quota_or_rate_limit',
            }.get(error.code, 'api_error')
            failure['code'] = error.code
            raise
        except Exception:
            failure['reason'] = 'network_or_response'
            raise

    probe = 'como voce consegue me ajudar de um jeito melhor'
    result = interpret(probe, 'origin', datetime.now(timezone.utc).date(), {}, config, opener=tracked)
    if failure:
        return {'enabled': True, 'configured': True, 'checked': True, 'ok': False,
                'reason': failure['reason'], **({'code': failure['code']} if 'code' in failure else {}),
                'model': model}
    if result != 'menu':
        return {'enabled': True, 'configured': True, 'checked': True, 'ok': False,
                'reason': 'unexpected_response', 'model': model}
    return {'enabled': True, 'configured': True, 'checked': True, 'ok': True, 'model': model}


def token_check(config, *, opener=urlopen, now=None):
    """Inspect token metadata without returning identities, scopes, or credentials."""
    app = config.get('META_APP_ID', '')
    version = config.get('META_GRAPH_API_VERSION', '')
    secret = config.get('META_APP_SECRET', '')
    token = config.get('WHATSAPP_ACCESS_TOKEN', '')
    if not app.isdigit() or not re.fullmatch(r'v\d+\.\d+', version) or not secret or not token:
        return {'ok': False, 'reason': 'configuration'}
    request = Request(f'https://graph.facebook.com/{version}/debug_token?' +
                      urlencode({'input_token': token}),
                      headers={'Authorization': 'Bearer ' + app + '|' + secret})
    try:
        with opener(request, timeout=15) as response:
            data = json.load(response)['data']
        if data.get('is_valid') is not True or str(data.get('app_id')) != app:
            return {'ok': False, 'reason': 'invalid_or_wrong_app'}
        result = {'ok': True}
        instant = time.time() if now is None else now
        for field in ('expires_at', 'data_access_expires_at'):
            value = data.get(field)
            if value is None:
                result[field] = {'status': 'unknown'}
            elif type(value) is not int or value < 0:
                raise ValueError('Invalid expiry')
            elif value == 0:
                result[field] = {'status': 'no_scheduled_expiry'}
            else:
                remaining = int(value - instant)
                result[field] = {
                    'status': 'expired' if remaining <= 0 else 'expiring_soon' if remaining <= 86400 else 'valid',
                    'utc': datetime.fromtimestamp(value, timezone.utc).isoformat(),
                    'remaining_seconds': max(0, remaining),
                }
                if remaining <= 0:
                    result['ok'] = False
        return result
    except Exception:
        return {'ok': False, 'reason': 'network_or_response'}


def check(config, *, meta=False, groq=False, opener=urlopen, groq_opener=urlopen):
    missing = [key for key in REQUIRED if not config.get(key)]
    results = {'configuration': {'ok': not missing, 'missing_keys': missing},
               'replies_enabled': config.get('ATLAS_WHATSAPP_REPLIES_ENABLED') == 'true',
               'live_flights_enabled': config.get('ATLAS_LIVE_FLIGHTS_ENABLED') == 'true'}
    results['nlu'] = (groq_check(config, opener=groq_opener) if groq else
                      {'enabled': config.get('ATLAS_NLU_ENABLED') == 'true',
                       'configured': bool(config.get('GROQ_API_KEY')), 'checked': False,
                       'model': config.get('GROQ_MODEL') or DEFAULT_MODEL})
    try:
        with opener('http://127.0.0.1:8787/health', timeout=5) as response:
            results['local_server'] = {'ok': response.read(100).startswith(b'atlas-')}
    except Exception:
        results['local_server'] = {'ok': False, 'reason': 'unreachable'}
    if not meta:
        results['meta'] = {'checked': False}
        return results
    version = config.get('META_GRAPH_API_VERSION', '')
    number = config.get('WHATSAPP_PHONE_NUMBER_ID', '')
    token = config.get('WHATSAPP_ACCESS_TOKEN', '')
    if not re.fullmatch(r'v\d+\.\d+', version) or not number.isdigit() or not token:
        results['meta'] = {'checked': False, 'ok': False, 'reason': 'configuration'}
        return results
    request = Request(f'https://graph.facebook.com/{version}/{number}?fields=id',
                      headers={'Authorization': 'Bearer ' + token})
    try:
        with opener(request, timeout=15) as response:
            data = json.load(response)
        results['meta'] = {'checked': True, 'ok': str(data.get('id')) == number}
    except HTTPError as error:
        try:
            details = json.load(error).get('error', {})
            code, subcode = int(details.get('code', 0)), int(details.get('error_subcode', 0))
        except (ValueError, TypeError, AttributeError):
            code, subcode = error.code, 0
        reason = ('token_expired' if (code, subcode) == (190, 463) else
                  'token_invalid' if code == 190 else 'access_or_permission_denied' if code == 200 else 'api_error')
        results['meta'] = {'checked': True, 'ok': False, 'reason': reason, 'code': code, 'subcode': subcode}
    except Exception:
        results['meta'] = {'checked': True, 'ok': False, 'reason': 'network_or_response'}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meta', action='store_true', help='Also perform a read-only Meta API check; no messages are sent.')
    parser.add_argument('--token', action='store_true', help='Inspect token expiry; requires META_APP_ID. Does not renew tokens.')
    parser.add_argument('--groq', action='store_true', help='Send one synthetic Groq intent check; no traveler message is used.')
    args = parser.parse_args()
    result = check(settings(), meta=args.meta, groq=args.groq)
    if args.token:
        result['token'] = token_check(settings())
    print(json.dumps(result, indent=2))
    healthy = result['configuration']['ok'] and result['local_server']['ok']
    if args.meta:
        healthy = healthy and result['meta'].get('ok', False)
    if args.token:
        healthy = healthy and result['token']['ok']
    if args.groq:
        healthy = healthy and result['nlu'].get('ok', False)
    raise SystemExit(0 if healthy else 1)


if __name__ == '__main__':
    main()
