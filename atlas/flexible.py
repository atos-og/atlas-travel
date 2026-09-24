"""Explicit, bounded nearby-date searches preserving the trip's stay length."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone


def date_pairs(values, today):
    departure = datetime.strptime(values['departure'], '%d/%m/%Y').date()
    returning = datetime.strptime(values['return'], '%d/%m/%Y').date()
    if returning < departure or departure < today:
        raise ValueError('Invalid travel dates')
    return [(start.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'))
            for offset in (0, -1, 1)
            for start, end in [(departure + timedelta(days=offset), returning + timedelta(days=offset))]
            if start >= today]


def search_nearby(provider, values, today):
    """At most three provider calls; each production call has its own 55s timeout."""
    pairs = date_pairs(values, today)

    def query(pair):
        request = {k: v for k, v in values.items() if k != 'flexibility'}
        request.update(departure=pair[0], **{'return': pair[1]})
        try:
            response = provider(request)
            if not isinstance(response, dict):
                raise ValueError('Invalid provider response')
            return response
        except Exception:
            return {'status': 'unavailable', 'offers': []}

    with ThreadPoolExecutor(max_workers=3) as pool:
        responses = list(pool.map(query, pairs))
    offers, queries = [], []
    for pair, response in zip(pairs, responses):
        queries.append({'departure': pair[0], 'return': pair[1], 'status': response.get('status', 'unavailable')})
        if response.get('status') == 'success':
            offers.extend(dict(offer, travel_dates={'departure': pair[0], 'return': pair[1]})
                          for offer in response.get('offers', []))
    complete = all(q['status'] in {'success', 'empty'} for q in queries)
    return {'status': 'success' if offers else 'empty' if complete else 'unavailable',
            'offers': offers, 'queries': queries, 'partial': not complete,
            'checked_at': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}


def coverage(result):
    queries = result.get('queries')
    if not queries:
        return ''
    dates = '; '.join(f"{q['departure']}–{q['return']}" for q in queries)
    suffix = ' Consulta parcial: uma ou mais combinações falharam.' if result.get('partial') else ''
    return f'Datas consultadas (ida–volta): {dates}. Duração da estadia mantida; não consultei o mês inteiro.{suffix}'


def label(values):
    return ('Datas próximas: original e ±1 dia, movendo ida e volta juntas, até 3 consultas.'
            if values.get('flexibility') == 'nearby' else 'Datas exatas.')
