"""ClickBus partner-search boundary. It stays disabled without partner credentials."""

import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from ..buses import normalize_offer
from ..language import clean


STAGING_BASE = 'https://platform-bff-partners.stg.clickbus.net/partners/api'
ALLOWED_HOSTS = {'platform-bff-partners.stg.clickbus.net'}


def _base(config):
    value = (config.get('CLICKBUS_API_BASE_URL') or STAGING_BASE).rstrip('/')
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username:
        raise ValueError('unsupported ClickBus API host')
    return value


def _request(config, path, query, *, opener=urlopen):
    token = config.get('CLICKBUS_ACCESS_TOKEN', '').strip()
    if not token:
        raise PermissionError('missing partner token')
    url = _base(config) + path + ('?' + urlencode(query) if query else '')
    headers = {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/json',
        'User-Agent': 'atlas-travel/0.1',
    }
    if path.endswith('/places/by-location'):
        headers.update({
            'cloudfront-viewer-city': '',
            'cloudfront-viewer-country-region': '',
            'cloudfront-viewer-latitude': '',
            'cloudfront-viewer-longitude': '',
        })
    with opener(Request(url, headers=headers), timeout=12) as response:
        return json.load(response)


def _items(payload, keys):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = _items(value, keys)
                if nested:
                    return nested
    return []


def resolve_place(name, config, *, opener=urlopen):
    payload = _request(config, '/v4/places/by-location', {
        'name': name,
        'limit': 10,
        'fields': 'id,name,slug,terminal,city,state,country,weight,useGroupByCity',
    }, opener=opener)
    places = [item for item in _items(payload, ('content', 'places', 'data'))
              if isinstance(item, dict) and isinstance(item.get('slug'), str)]
    if not places:
        return None
    requested = clean(name)
    exact = []
    for item in places:
        names = [item.get('name'), item.get('cityName')]
        city = item.get('city')
        if isinstance(city, dict):
            names.append(city.get('name'))
        if requested in {clean(str(value)) for value in names if value}:
            exact.append(item)
    candidates = exact or places
    candidates.sort(key=lambda item: int(item.get('weight') or 0), reverse=True)
    return candidates[0]['slug']


def _minutes(value):
    text = str(value or '').strip().lower()
    match = re.fullmatch(r'(\d{1,2}):(\d{2})', text)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    match = re.fullmatch(r'(?:(\d+)h)?\s*(?:(\d+)m)?', text)
    if match and any(match.groups()):
        return int(match.group(1) or 0) * 60 + int(match.group(2) or 0)
    return None


def _point(value):
    if not isinstance(value, dict):
        return None
    raw_time = value.get('datetime')
    station = value.get('station') or value.get('placeName')
    if not station and isinstance(value.get('place'), dict):
        station = value['place'].get('name')
    if not raw_time and isinstance(value.get('schedule'), dict):
        schedule = value['schedule']
        raw_time = f"{schedule.get('date', '')}T{schedule.get('time', '')}"
    try:
        parsed = datetime.fromisoformat(str(raw_time).replace('Z', '+00:00'))
        display = parsed.strftime('%d/%m %H:%M')
    except ValueError:
        return None
    return {'place': str(station or '').strip(), 'time': display}


def normalize(raw, adults):
    """Translate one documented ClickBus departure into Atlas' bus contract."""
    if not isinstance(raw, dict):
        return None
    try:
        unit = raw.get('discountedPrice')
        if unit is None or Decimal(str(unit)) <= 0:
            unit = raw['price']
        total = Decimal(str(unit)) * adults
    except (KeyError, InvalidOperation, TypeError):
        return None
    company = raw.get('company') or raw.get('travelCompany') or {}
    service = raw.get('serviceClass') or raw.get('bus') or {}
    kind = str(raw.get('type') or '').lower()
    parts = raw.get('parts') or raw.get('trips') or []
    connections = 0 if kind == 'direct' else max(1, len(parts) - 1) if kind in {'connection', 'one_stop'} else 0
    candidate = {
        'price': str(total),
        'duration': _minutes(raw.get('duration')),
        'connections': connections,
        'available_seats': raw.get('availableSeats', raw.get('available_seats', adults)),
        'departure': _point(raw.get('departure')),
        'arrival': _point(raw.get('arrival')),
        'company': company.get('name') if isinstance(company, dict) else company,
        'service_class': service.get('name') if isinstance(service, dict) else service,
        # The documented partner flow is transactional and does not publish a fare handoff URL.
        'url': None,
    }
    return normalize_offer(candidate, adults)


def search(values, config, *, opener=urlopen):
    """Search one-way fares without booking, blocking seats, or handling payment."""
    if not config.get('CLICKBUS_ACCESS_TOKEN'):
        return {'status': 'unauthorized', 'offers': []}
    try:
        adults = int(values['adults'])
        departure = datetime.strptime(values['departure'], '%d/%m/%Y').date()
        origin = resolve_place(values['origin'], config, opener=opener)
        destination = resolve_place(values['destination'], config, opener=opener)
        if not origin or not destination or origin == destination or not 1 <= adults <= 6:
            return {'status': 'invalid', 'offers': []}
        payload = _request(config, '/v5/trips', {
            'from': origin,
            'to': destination,
            'departureDate': departure.isoformat(),
        }, opener=opener)
        raw_offers = _items(payload, ('departures', 'trips', 'content', 'data'))
        offers = []
        seen = set()
        for raw in raw_offers:
            offer = normalize(raw, adults)
            if not offer:
                continue
            fingerprint = (offer['price'], offer['departure']['time'], offer['arrival']['time'],
                           offer['company'], offer['service_class'])
            if fingerprint not in seen:
                seen.add(fingerprint)
                offers.append(offer)
        return {
            'status': 'success' if offers else 'empty',
            'offers': offers,
            'checked_at': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC'),
            'source': 'ClickBus partner API',
        }
    except HTTPError as error:
        return {'status': 'unauthorized' if error.code in {401, 403} else 'unavailable', 'offers': []}
    except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
        return {'status': 'unavailable', 'offers': []}
