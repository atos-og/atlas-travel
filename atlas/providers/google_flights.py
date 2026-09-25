"""fli adapter adapted from Fly Club's verified round-trip price normalization."""

import contextlib
import io
import json
import logging
import sys
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlsplit, parse_qs


def normalize(raw, client, values):
    journeys = raw if isinstance(raw, tuple) else (raw,)
    if len(journeys) != 2:
        return None
    # fli's first journey price is the round-trip total; do not sum leg prices.
    price = Decimal(str(journeys[0].price))
    if not price.is_finite() or price <= 0:
        return None
    if any((getattr(j, 'currency', None) or 'BRL') != 'BRL' for j in journeys):
        return None
    parts = []
    for index, journey in enumerate(journeys):
        legs = journey.legs
        if not legs or journey.duration <= 0 or journey.stops < 0:
            return None
        code = lambda value: str(getattr(value, 'name', value)).lstrip('_')
        expected_origin = values['origin'] if index == 0 else values['destination']
        expected_destination = values['destination'] if index == 0 else values['origin']
        expected_date = datetime.strptime(values['departure' if index == 0 else 'return'], '%d/%m/%Y').date()
        if code(legs[0].departure_airport) != expected_origin or code(legs[-1].arrival_airport) != expected_destination:
            return None
        if legs[0].departure_datetime.date() != expected_date:
            return None
        parts.append({'departure': legs[0].departure_datetime.strftime('%d/%m %H:%M'),
                      'arrival': legs[-1].arrival_datetime.strftime('%d/%m %H:%M'),
                      'duration': int(journey.duration), 'stops': int(journey.stops),
                      'airlines': '/'.join(dict.fromkeys(code(leg.airline) for leg in legs)),
                      'flights': [code(leg.airline) + str(leg.flight_number) for leg in legs]})
    url = None
    try:
        candidate = client.build_flight_booking_url(raw, currency='BRL', language='pt-BR', country='BR')
        parsed = urlsplit(candidate)
        if (parsed.scheme == 'https' and parsed.hostname in {'www.google.com', 'www.google.com.br', 'google.com'}
                and not parsed.username and parsed.path == '/travel/flights/booking'
                and parse_qs(parsed.query).get('tfs')):
            url = candidate if len(candidate) <= 3500 else None
    except Exception:
        pass
    return {'price': str(price), 'currency': 'BRL', 'journeys': parts,
            'stops': max(p['stops'] for p in parts),
            'duration': sum(p['duration'] for p in parts), 'url': url,
            'link_requires_passenger_check': int(values['adults']) > 1}


def search(values):
    try:
        from fli.models import Airport, FlightSearchFilters, FlightSegment, PassengerInfo, SeatType, SortBy, TripType, MaxStops
        from fli.search import SearchFlights
        from fli.search.flights import SearchParseError
    except ImportError:
        return {'status': 'unavailable', 'offers': []}
    try:
        origin, destination = Airport[values['origin']], Airport[values['destination']]
        departure = datetime.strptime(values['departure'], '%d/%m/%Y').date()
        returning = datetime.strptime(values['return'], '%d/%m/%Y').date()
        adults = int(values['adults'])
        if not 1 <= adults <= 6 or returning < departure or origin == destination:
            raise ValueError('Invalid route')
        filters = FlightSearchFilters(
            trip_type=TripType.ROUND_TRIP, passenger_info=PassengerInfo(adults=adults),
            flight_segments=[FlightSegment(departure_airport=[[origin, 0]], arrival_airport=[[destination, 0]], travel_date=departure.isoformat()),
                             FlightSegment(departure_airport=[[destination, 0]], arrival_airport=[[origin, 0]], travel_date=returning.isoformat())],
            seat_type=SeatType.ECONOMY, stops=MaxStops.NON_STOP if values['priority'] == '3' else MaxStops.ANY,
            sort_by=SortBy.DURATION if values['priority'] == '2' else SortBy.CHEAPEST,
            show_all_results=False,
        )
    except (KeyError, ValueError, TypeError):
        return {'status': 'invalid', 'offers': []}
    try:
        client = SearchFlights()
        results = client.search(filters, top_n=8, currency='BRL', language='pt-BR', country='BR')
        if not results:
            return {'status': 'empty', 'offers': []}
        offers = []
        for raw in results:
            try:
                offer = normalize(raw, client, values)
                if offer and (values['priority'] != '3' or offer['stops'] == 0):
                    offers.append(offer)
            except Exception:
                continue
        return {'status': 'success' if offers else 'changed', 'offers': offers,
                'checked_at': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}
    except SearchParseError:
        return {'status': 'changed', 'offers': []}
    except Exception:
        return {'status': 'unavailable', 'offers': []}


def main():
    logging.disable(logging.CRITICAL)
    values = json.load(sys.stdin)
    # Provider diagnostics may contain routes; never forward them to bot logs.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = search(values)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
