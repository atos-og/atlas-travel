"""Read-only WhatsApp business-profile validation for the Atlas sender."""

import json
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .webhook import settings


EXPECTED_NAME = 'Atlas'


def check(config, *, opener=urlopen):
    version = config.get('META_GRAPH_API_VERSION', '')
    number = config.get('WHATSAPP_PHONE_NUMBER_ID', '')
    token = config.get('WHATSAPP_ACCESS_TOKEN', '')
    if not re.fullmatch(r'v\d+\.\d+', version) or not number.isdigit() or not token:
        return {'ok': False, 'reason': 'configuration'}
    headers = {'Authorization': 'Bearer ' + token}
    phone_request = Request(
        f'https://graph.facebook.com/{version}/{number}?' +
        urlencode({'fields': 'verified_name,name_status,quality_rating'}),
        headers=headers,
    )
    profile_request = Request(
        f'https://graph.facebook.com/{version}/{number}/whatsapp_business_profile?' +
        urlencode({'fields': 'about,description,email,profile_picture_url,vertical,websites'}),
        headers=headers,
    )
    try:
        with opener(phone_request, timeout=15) as response:
            phone = json.load(response)
        with opener(profile_request, timeout=15) as response:
            profile = json.load(response).get('data', [{}])[0]
        result = {
            'reachable': str(phone.get('id')) == number,
            'atlas_name_live': phone.get('verified_name') == EXPECTED_NAME,
            'name_status': phone.get('name_status') or 'unknown',
            'quality_rating': phone.get('quality_rating') or 'unknown',
            'profile_picture': bool(profile.get('profile_picture_url')),
            'about': bool(profile.get('about')),
            'description': bool(profile.get('description')),
            'website': bool(profile.get('websites')),
        }
        result['ok'] = result['reachable'] and result['atlas_name_live'] and result['profile_picture']
        return result
    except HTTPError as error:
        reason = 'credentials_or_access' if error.code in {400, 401, 403} else 'meta_api'
        return {'ok': False, 'reason': reason, 'code': error.code}
    except Exception:
        return {'ok': False, 'reason': 'network_or_response'}


def main():
    result = check(settings())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get('ok') else 1)


if __name__ == '__main__':
    main()
