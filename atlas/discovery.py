"""Budget-led comparison of an explicit, bounded set of destination airports."""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from .budget import parse_budget, money
from .flights import resolve_airport, rank, format_results
from .language import clean, parse_date, choice

START = {'explorar destinos', 'destinos por orcamento', 'comparar destinos', 'refazer comparacao'}
FIELDS = ('origin', 'departure', 'return', 'adults', 'budget', 'candidates')
PROMPTS = {
    'origin': 'De qual cidade ou aeroporto você sai?',
    'departure': 'Qual é a data de ida para comparar os destinos?',
    'return': 'Qual é a data de volta? Pode escrever 7 dias depois.',
    'adults': 'Quantos adultos vão viajar? De 1 a 6.',
    'budget': 'Qual é o orçamento total em reais para as passagens de todos os adultos, ida e volta? Informe um limite, como R$ 2.000.',
    'candidates': 'Quais destinos quer comparar? Informe de 1 a 3 cidades ou aeroportos, separados por vírgula. Exemplo: GRU, BOG, REC. Não é uma busca de todos os destinos do mundo.',
}


def destinations(text, origin):
    parts = re.split(r'\s*[,;]\s*', text.strip())
    if not 1 <= len(parts) <= 3 or any(not part for part in parts):
        raise ValueError('Informe de 1 a 3 destinos separados por vírgula.')
    result = []
    for part in parts:
        code, error = resolve_airport(part)
        if error:
            raise ValueError(error)
        if code == origin:
            raise ValueError('Os destinos devem ser diferentes da origem.')
        if code not in result:
            result.append(code)
    return result


def compare(provider, values):
    candidates = values['candidates']
    if not candidates or len(candidates) > 3 or len(set(candidates)) != len(candidates):
        raise ValueError('Invalid destination count')
    def query(destination):
        request = {key: values[key] for key in ('origin', 'departure', 'return', 'adults', 'budget')}
        request.update(destination=destination, priority=values.get('priority', '1'))
        try:
            result = provider(request)
            if result.get('status') not in {'success', 'empty'}:
                return {'destination': destination, 'status': 'unavailable'}
            offers = result.get('offers', [])
            # Validate the fields used by ranking before storing the response.
            for offer in offers:
                if not Decimal(offer['price']).is_finite() or Decimal(offer['price']) <= 0:
                    raise ValueError('Invalid price')
            selected = rank(offers, values.get('priority', '1'), values['budget'])
            if not selected:
                return {'destination': destination, 'status': 'no_match'}
            return {'destination': destination, 'status': 'match', 'price': selected[0]['price'],
                    'result': dict(result, offers=selected)}
        except Exception:
            return {'destination': destination, 'status': 'unavailable'}
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(query, candidates))
    matches = sorted((r for r in results if r['status'] == 'match'), key=lambda r: Decimal(r['price']))
    return {'matches': matches, 'queries': results,
            'checked_at': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}


def next_prompt(state):
    for key in FIELDS:
        if key not in state or (key == 'budget' and state[key] is None):
            state['stage'] = key
            return PROMPTS[key]
    state['stage'] = 'confirm'
    stops = 'sem paradas nos dois sentidos' if state.get('priority') == '3' else 'com ou sem paradas'
    return (f"Comparar {', '.join(state['candidates'])}, saindo de {state['origin']}. "
            f"Ida {state['departure']}, volta {state['return']}; {state['adults']} adulto(s). "
            f"Até R$ {money(state['budget'])} no total de ida e volta, {stops}. "
            'Vou buscar a menor tarifa retornada por destino, em datas exatas, com até 3 consultas. '
            'Hospedagem e passeios não estão incluídos. Confirmar?')


def render(state):
    report = state['report']
    lines = [f"Destinos dentro de R$ {money(state['budget'])} • total das passagens",
             f"{state['origin']} • {state['adults']} adulto(s) • {state['departure']}–{state['return']}",
             'Google Flights • ' + report['checked_at']]
    for i, result in enumerate(report['matches'], 1):
        lines.append(f"{i}. {result['destination']}: a partir de R$ {money(result['price'])} entre as ofertas retornadas.")
    for result in report['queries']:
        if result['status'] != 'match':
            reason = 'consulta falhou' if result['status'] == 'unavailable' else 'nenhuma oferta retornada dentro dos critérios'
            lines.append(f"{result['destination']}: {reason}.")
    lines.append('A comparação cobre apenas os destinos informados. Não encontrar uma oferta não prova que ela não exista. Preços podem mudar.')
    lines.append('Escolha destino 1 (ou outro número) para ver as ofertas; explorar destinos para refazer ou voltar aos voos para sair.')
    return '\n'.join(lines)


def choices(state):
    stage = state['stage']
    if stage == 'adults':
        options = [(str(i), f'{i} adulto(s)') for i in range(1, 7)]
    elif stage == 'confirm':
        options = [('sim', 'Comparar destinos'), ('refazer comparacao', 'Refazer critérios')]
    elif stage == 'done':
        options = [(f'destino {i}', f"{r['destination']} • R$ {money(r['price'])}"[:24])
                   for i, r in enumerate(state['report']['matches'], 1)]
        options.append(('refazer comparacao', 'Nova comparação'))
    else:
        options = []
    return options + [('voltar aos voos', 'Voltar aos voos')]


def handle(session, text, today, provider, on_search=None):
    command = clean(text)
    state = session.values.get('_discovery')
    if command in START:
        if provider is None:
            return 'A comparação de destinos precisa da busca de voos habilitada. O simulador não consulta tarifas reais.'
        state = {} if command == 'refazer comparacao' else {k: session.values[k] for k in FIELDS[:-1] if k in session.values}
        state.update(active=True, priority='3' if session.values.get('priority') == '3' else '1')
        session.values['_discovery'] = state
        if session.values.get('_itinerary'):
            session.values['_itinerary']['active'] = False
        return 'Vamos comparar destinos. Confira os critérios antes de confirmar; refazer comparação permite preencher tudo novamente. ' + next_prompt(state)
    if not state or not state.get('active'):
        return None
    if command == 'ajuda':
        return 'Na comparação de destinos, informe os critérios pedidos e confirme antes de buscar. Use refazer comparação para alterar todos os critérios, voltar aos voos para retomar a viagem ou roteiro para planejar passeios. Nenhuma busca foi feita por este pedido de ajuda.'
    stage = state['stage']
    if stage == 'confirm':
        if command not in {'sim', 'confirmar', 'pode buscar', 'comparar'}:
            return next_prompt(state)
        if datetime.strptime(state['departure'], '%d/%m/%Y').date() < today:
            state.pop('departure', None)
            state.pop('return', None)
            return 'A data de ida passou. ' + next_prompt(state)
        if on_search:
            on_search('Estou comparando os destinos dentro do seu orçamento. São até 3 consultas nas mesmas datas.')
        state['report'] = compare(provider, state)
        state['stage'] = 'done'
        return render(state)
    if stage == 'done':
        match = re.fullmatch(r'(?:escolher )?destino ([1-3])', command)
        if not match or int(match[1]) > len(state['report']['matches']):
            return render(state)
        selected = state['report']['matches'][int(match[1])-1]
        for key in FIELDS[:-1]:
            session.values[key] = state[key]
        session.values.update(destination=selected['destination'], priority=state['priority'],
                              flexibility='exact', result=selected['result'])
        for key in ('_price_question', '_budget_refine', '_choices'):
            session.values.pop(key, None)
        state['active'] = False
        session.step = 'complete'
        return 'Selecionei esse destino usando a consulta anterior, sem buscar novamente.\n' + format_results(selected['result'], session.values)
    try:
        if stage == 'origin':
            value, error = resolve_airport(text)
            if error:
                raise ValueError(error)
        elif stage in {'departure', 'return'}:
            departure = datetime.strptime(state['departure'], '%d/%m/%Y').date() if stage == 'return' else None
            value = parse_date(text, today, departure)
            if value < today or (departure and value < departure):
                raise ValueError('A data deve ser futura e a volta não pode ser anterior à ida.')
            value = value.strftime('%d/%m/%Y')
        elif stage == 'adults':
            value = choice(text, 'adults')
            if value not in {str(i) for i in range(1, 7)}:
                raise ValueError(PROMPTS['adults'])
        elif stage == 'budget':
            value = parse_budget(text)
            if value is None:
                raise ValueError(PROMPTS['budget'])
        else:
            value = destinations(text, state['origin'])
    except ValueError as error:
        return str(error) or PROMPTS[stage]
    state[stage] = value
    return next_prompt(state)
