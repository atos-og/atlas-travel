"""Read-only development diagnostics. Never print credentials or recipient IDs."""

import argparse
import json
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from .webhook import settings


REQUIRED = ('WHATSAPP_VERIFY_TOKEN', 'META_APP_SECRET', 'WHATSAPP_ACCESS_TOKEN',
            'WHATSAPP_PHONE_NUMBER_ID', 'META_GRAPH_API_VERSION', 'ATLAS_ALLOWED_WHATSAPP_USER')


def check(config, *, meta=False, opener=urlopen):
    missing = [key for key in REQUIRED if not config.get(key)]
    results = {'configuration': {'ok': not missing, 'missing_keys': missing},
               'replies_enabled': config.get('ATLAS_WHATSAPP_REPLIES_ENABLED') == 'true',
               'live_flights_enabled': config.get('ATLAS_LIVE_FLIGHTS_ENABLED') == 'true'}
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
    args = parser.parse_args()
    result = check(settings(), meta=args.meta)
    print(json.dumps(result, indent=2))
    healthy = result['configuration']['ok'] and result['local_server']['ok']
    if args.meta:
        healthy = healthy and result['meta'].get('ok', False)
    raise SystemExit(0 if healthy else 1)


if __name__ == '__main__':
    main()
