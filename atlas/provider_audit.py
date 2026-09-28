"""Run a bounded flight-source audit and print only non-sensitive evidence."""

import argparse
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from .flights import search


def audit(values, *, provider=search):
    """Summarize normalized provider output without printing booking URLs."""
    result = provider(dict(values))
    offers = result.get('offers', []) if isinstance(result, dict) else []
    prices = []
    hosts = set()
    complete = 0
    for offer in offers:
        try:
            price = Decimal(str(offer['price']))
            journeys = offer['journeys']
            if price.is_finite() and price > 0 and len(journeys) == 2:
                prices.append(price)
                complete += 1
            url = offer.get('url')
            if url:
                host = urlsplit(url).hostname
                if host:
                    hosts.add(host)
        except (KeyError, TypeError, InvalidOperation):
            continue
    success = result.get('status') == 'success' and complete > 0
    return {
        'ok': success,
        'status': result.get('status', 'invalid_response') if isinstance(result, dict) else 'invalid_response',
        'route': f"{values['origin']}->{values['destination']}",
        'departure': values['departure'],
        'return': values['return'],
        'adults': int(values['adults']),
        'normalized_offers': complete,
        'offers_with_links': sum(1 for offer in offers if offer.get('url')),
        'link_hosts': sorted(hosts),
        'lowest_brl': str(min(prices)) if prices else None,
        'highest_brl': str(max(prices)) if prices else None,
        'checked_at': result.get('checked_at') if isinstance(result, dict) else None,
    }


def _date(value):
    try:
        return datetime.strptime(value, '%d/%m/%Y').strftime('%d/%m/%Y')
    except ValueError as error:
        raise argparse.ArgumentTypeError('use DD/MM/YYYY') from error


def _airport(value):
    value = value.upper()
    if len(value) != 3 or not value.isalpha():
        raise argparse.ArgumentTypeError('use a three-letter airport code')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('origin', type=_airport)
    parser.add_argument('destination', type=_airport)
    parser.add_argument('departure', type=_date)
    parser.add_argument('return_date', type=_date)
    parser.add_argument('--adults', type=int, choices=range(1, 7), default=1)
    args = parser.parse_args()
    values = {'origin': args.origin, 'destination': args.destination,
              'departure': args.departure, 'return': args.return_date,
              'adults': str(args.adults), 'priority': '1'}
    result = audit(values)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
