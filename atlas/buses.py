"""Guided one-way bus search with an injectable, provider-neutral boundary."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .budget import money, parse_budget
from .language import choice, clean, is_confirmation, is_greeting, parse_date


START = {
    'onibus', 'passagem de onibus', 'passagens de onibus',
    'consultar onibus', 'buscar onibus', 'viajar de onibus',
}

PRIORITIES = {
    '1': 'menor preço',
    '2': 'menor duração',
    '3': 'menos conexões',
    '4': 'mais conforto',
}

PRIORITY_PROMPT = (
    '*Como você quer comparar os ônibus?*\n\n'
    '1. *Menor preço*\n'
    '2. *Menor duração*\n'
    '3. *Menos conexões*\n'
    '4. *Mais conforto* pela classe informada pela viação\n\n'
    'Abra a lista abaixo ou responda com o número da opção.'
)

BUDGET_PROMPT = (
    '*Qual é o limite para as passagens de ônibus?*\n\n'
    'Informe o total em reais para somente ida de todos os adultos.\n\n'
    '*Exemplos*\n'
    '• R$ 300\n'
    '• 500\n'
    '• sem limite'
)

UNAVAILABLE = (
    '*Passagens de ônibus* 🚌\n\n'
    'O fluxo rodoviário já está sendo preparado, mas a fonte de preços ao vivo ainda não está ativa. '
    'A integração escolhida exige credenciamento de parceiro antes de consultar disponibilidade e tarifas reais.\n\n'
    'Atlas não vai inventar preços nem transformar essa viagem em uma busca de voos. '
    'Digite *menu* para usar os recursos disponíveis agora.'
)

_COMFORT = {
    'leito-cama': 5,
    'leito cama': 5,
    'leito': 4,
    'semi-leito': 3,
    'semi leito': 3,
    'executivo': 2,
    'convencional': 1,
}


def _route(text):
    """Extract only an explicit short city-to-city route from a bus request."""
    value = clean(text)
    value = re.sub(r'^(?:eu )?(?:quero|gostaria de|preciso) (?:ir|viajar) ', '', value)
    value = re.sub(r'^(?:uma |a )?passagem de onibus ', '', value)
    match = re.search(r'\bde (.{2,45}?) (?:para|pra|ate|->) (.{2,45}?)(?: de onibus| por onibus)?$', value)
    if not match:
        return None
    origin, destination = (part.strip(' ,') for part in match.groups())
    if origin == destination or any(token in destination for token in (' ida ', ' volta ', ' dia ')):
        return None
    return origin, destination


def starts(text):
    command = clean(text)
    return command in START or bool(
        re.search(r'\b(?:onibus|rodoviari[oa])\b', command)
        and re.search(r'\b(?:quero|gostaria|preciso|passagem|buscar|consultar|viajar|ir)\b', command)
    )


def _duration(value):
    if isinstance(value, int) and value > 0:
        return value
    match = re.fullmatch(r'(?:(\d+)h)?\s*(?:(\d+)m)?', str(value or '').strip())
    if not match or not any(match.groups()):
        return None
    return int(match.group(1) or 0) * 60 + int(match.group(2) or 0)


def normalize_offer(raw, adults):
    """Validate the provider-neutral offer contract used by the conversation."""
    try:
        price = Decimal(str(raw['price']))
        duration = _duration(raw['duration'])
        connections = int(raw.get('connections', 0))
        seats = int(raw.get('available_seats', adults))
        if not price.is_finite() or price <= 0 or not duration or connections < 0 or seats < adults:
            return None
        departure = raw['departure']
        arrival = raw['arrival']
        for point in (departure, arrival):
            if not isinstance(point, dict) or not point.get('place') or not point.get('time'):
                return None
        company = str(raw.get('company') or '').strip()
        service_class = str(raw.get('service_class') or '').strip()
        if not company or not service_class:
            return None
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return None
    return {
        'price': str(price.quantize(Decimal('.01'))),
        'duration': duration,
        'connections': connections,
        'available_seats': seats,
        'departure': {'place': str(departure['place']), 'time': str(departure['time'])},
        'arrival': {'place': str(arrival['place']), 'time': str(arrival['time'])},
        'company': company,
        'service_class': service_class,
        'url': raw.get('url') if isinstance(raw.get('url'), str) else None,
    }


def rank(offers, priority, budget=None, adults=1):
    cap = Decimal(str(budget)) if budget is not None else None
    valid = []
    for raw in offers or []:
        offer = normalize_offer(raw, int(adults))
        if offer and (cap is None or Decimal(offer['price']) <= cap):
            valid.append(offer)
    if priority == '2':
        key = lambda item: (item['duration'], Decimal(item['price']))
    elif priority == '3':
        key = lambda item: (item['connections'], item['duration'], Decimal(item['price']))
    elif priority == '4':
        key = lambda item: (-_COMFORT.get(clean(item['service_class']), 0), Decimal(item['price']))
    else:
        key = lambda item: (Decimal(item['price']), item['duration'])
    return sorted(valid, key=key)[:4]


def format_results(result, values):
    status = result.get('status') if isinstance(result, dict) else 'unavailable'
    if status != 'success':
        messages = {
            'empty': 'A fonte não retornou ônibus para esses critérios.',
            'invalid': 'A fonte recusou os critérios dessa busca.',
            'unavailable': 'A fonte rodoviária não respondeu agora.',
            'unauthorized': 'A fonte rodoviária ainda não está credenciada para esta instalação.',
        }
        return ('*Não consegui comparar os ônibus*\n\n' + messages.get(status, messages['unavailable']) +
                '\n\nNenhum preço foi estimado. Digite *nova busca de ônibus* para tentar outros critérios ou *voos* para voltar.')
    offers = rank(result.get('offers'), values['priority'], values.get('budget'), values.get('adults', 1))
    if not offers:
        return ('*Nenhuma opção cabe no limite informado*\n\n'
                'A consulta não encontrou uma oferta válida dentro do orçamento total. '
                'Isso não prova que não existam tarifas em outras fontes.\n\n'
                'Digite *orçamento de ônibus* para ajustar o total ou *nova busca de ônibus*.')
    lines = [f"*{values['origin']} → {values['destination']} de ônibus*",
             f"Somente ida • {values['adults']} adulto(s)",
             f"Consulta: {result.get('checked_at', 'horário não disponível')}",
             f"Ordenado por {PRIORITIES[values['priority']]} entre as opções retornadas."]
    if values.get('budget') is not None:
        lines.append(f"Limite total: R$ {money(values['budget'])}.")
    for index, offer in enumerate(offers, 1):
        duration = offer['duration']
        lines += ['', f"*{index}. R$ {money(offer['price'])} no total*",
                  f"{offer['company']} • {offer['service_class']}",
                  f"{offer['departure']['time']} → {offer['arrival']['time']} • {duration // 60}h{duration % 60:02}",
                  f"{offer['departure']['place']} → {offer['arrival']['place']}",
                  ('Direto' if offer['connections'] == 0 else f"{offer['connections']} conexão(ões)"),
                  f"Assentos informados pela fonte: {offer['available_seats']}"]
    lines += ['', 'Tarifas e assentos podem mudar. Classe e comodidades são informações da viação; confirme tudo antes de comprar.',
              '', '*Alguma opção atende?*\nAbra a lista para ver detalhes ou ajustar a busca.']
    return '\n'.join(lines)


def prompt(state):
    prompts = {
        'origin': '*De qual cidade você sai de ônibus?*\n\nInforme a cidade ou o terminal.',
        'destination': '*Para qual cidade você vai de ônibus?*\n\nInforme a cidade ou o terminal.',
        'departure': '*Qual é a data da viagem?*\n\nPode escrever “23/10/2026” ou “dia 23 de outubro desse ano”.',
        'adults': '*Quantos adultos vão viajar?*\n\nEscolha de 1 a 6.',
        'priority': PRIORITY_PROMPT,
        'budget': BUDGET_PROMPT,
    }
    return prompts[state['stage']]


def apply_request(session, fields, today, bus_search=None):
    """Prefill a bus request extracted by the hosted interpreter."""
    if bus_search is None:
        session.values['_bus'] = {'active': False, 'stage': 'unavailable'}
        session.values['_bus_notice'] = True
        return UNAVAILABLE
    state = {'active': True, 'stage': 'origin'}
    session.values['_bus'] = state
    for key in ('origin', 'destination'):
        if key in fields:
            value = fields[key].strip()
            if not 2 <= len(value) <= 100:
                state['stage'] = key
                return 'Informe uma cidade ou terminal com 2 a 100 caracteres.'
            state[key] = value
    if state.get('origin') and clean(state.get('destination', '')) == clean(state['origin']):
        state.pop('destination', None)
        state['stage'] = 'destination'
        return 'O destino precisa ser diferente da origem.'
    if 'departure' in fields:
        try:
            parsed = parse_date(fields['departure'], today)
            if parsed < today:
                raise ValueError
            state['departure'] = parsed.strftime('%d/%m/%Y')
        except ValueError:
            state['stage'] = 'departure'
            return 'Não consegui entender a data. Informe um dia futuro, por exemplo 23/10/2026.'
    if 'adults' in fields:
        if fields['adults'] not in {str(i) for i in range(1, 7)}:
            state['stage'] = 'adults'
            return 'Nesta primeira versão rodoviária, informe de 1 a 6 adultos.'
        state['adults'] = fields['adults']
    if 'priority' in fields:
        if fields['priority'] not in PRIORITIES:
            state['stage'] = 'priority'
            return PRIORITY_PROMPT
        state['priority'] = fields['priority']
    if 'budget' in fields:
        try:
            state['budget'] = parse_budget(fields['budget'])
        except ValueError:
            state['stage'] = 'budget'
            return BUDGET_PROMPT
    for key in ('origin', 'destination', 'departure', 'adults', 'priority', 'budget'):
        if key not in state:
            state['stage'] = key
            return prompt(state)
    state['stage'] = 'confirm'
    return _summary(state)


def choices(state):
    stage = state.get('stage')
    if stage == 'adults':
        return [(str(i), f'{i} adulto' + ('s' if i > 1 else ''), '') for i in range(1, 7)]
    if stage == 'priority':
        return [(key, label.title(), '') for key, label in PRIORITIES.items()]
    if stage == 'budget':
        return [('sem limite', 'Sem limite', ''), ('voos', 'Voltar aos voos', '')]
    if stage == 'confirm':
        return [('sim', 'Confirmar busca', ''), ('nova busca de onibus', 'Recomeçar', '')]
    if stage == 'done':
        result = state.get('result', {})
        offers = rank(result.get('offers'), state.get('priority', '1'), state.get('budget'), state.get('adults', 1))
        options = [(f'onibus oferta {index}', f'Ônibus {index} • R$ {money(offer["price"])}'[:24],
                    f'{offer["company"]} | {offer["service_class"]}'[:72])
                   for index, offer in enumerate(offers, 1)]
        return (options + [('nova busca de onibus', 'Nova busca', ''),
                           ('voos', 'Comparar voos', ''),
                           ('roteiro', 'Montar roteiro', '')])[:10]
    return []


def _summary(state):
    priority = PRIORITIES[state['priority']]
    budget = ('sem limite de preço' if state.get('budget') is None
              else f"limite total de R$ {money(state['budget'])}")
    return (f"*Confirmar ônibus: {state['origin']} → {state['destination']}*\n\n"
            f"• Data: {state['departure']}\n"
            f"• Passageiros: {state['adults']} adulto(s)\n"
            f"• Preferência: {priority}\n"
            f"• Orçamento: {budget}\n\n"
            '*Posso consultar a fonte rodoviária?*')


def handle(session, text, today, bus_search=None, on_search=None):
    """Handle an active bus overlay, start one, or return None for other features."""
    command = clean(text)
    state = session.values.get('_bus')
    active = bool(state and state.get('active'))
    if active and command in {
        'voos', 'consultar voos', 'voltar aos voos', 'roteiro', 'montar roteiro',
        'planejar passeios', 'passeios', 'explorar destinos', 'comparar destinos',
        'destinos por orcamento',
    }:
        state['active'] = False
        return None
    if not active and not starts(text):
        return None
    if not active:
        if bus_search is None:
            session.values['_bus'] = {'active': False, 'stage': 'unavailable'}
            session.values['_bus_notice'] = True
            return UNAVAILABLE
        state = {'active': True, 'stage': 'origin'}
        session.values['_bus'] = state
        route = _route(text)
        if route:
            state['origin'], state['destination'] = route
            state['stage'] = 'departure'
        return prompt(state)
    if is_greeting(text):
        return 'Olá! Continuamos sua busca rodoviária.\n\n' + (prompt(state) if state['stage'] != 'done' else format_results(state.get('result', {}), state))
    if command in {'nova busca de onibus', 'recomecar onibus', 'outra passagem de onibus'}:
        session.values['_bus'] = {'active': True, 'stage': 'origin'}
        return prompt(session.values['_bus'])
    if command.startswith('onibus oferta ') and state.get('stage') == 'done':
        try:
            index = int(command.rsplit(' ', 1)[1]) - 1
            offer = rank(state.get('result', {}).get('offers'), state['priority'], state.get('budget'), state.get('adults', 1))[index]
            if index < 0:
                raise IndexError
        except (ValueError, IndexError):
            return 'Escolha uma das opções rodoviárias exibidas na lista atual.'
        duration = offer['duration']
        return (f"*Ônibus {index + 1}: {state['origin']} → {state['destination']}*\n\n"
                f"• Total: R$ {money(offer['price'])}\n"
                f"• Viação: {offer['company']}\n"
                f"• Classe: {offer['service_class']}\n"
                f"• Horário: {offer['departure']['time']} → {offer['arrival']['time']}\n"
                f"• Duração: {duration // 60}h{duration % 60:02}\n"
                f"• {'Direto' if offer['connections'] == 0 else str(offer['connections']) + ' conexão(ões)'}\n\n"
                'A integração de compra ainda depende do credenciamento do parceiro. Nenhum link foi inventado.')
    if state.get('stage') == 'done':
        if command == 'orcamento de onibus':
            state['stage'] = 'budget'
            state['_refine_budget'] = True
            return BUDGET_PROMPT
        return ('Sua consulta rodoviária continua salva. Abra a lista para ver uma opção, '
                'digite *nova busca de ônibus* ou *voos*.')
    stage = state['stage']
    if stage in {'origin', 'destination'}:
        value = text.strip()
        if not 2 <= len(value) <= 100:
            return 'Informe uma cidade ou terminal com 2 a 100 caracteres.'
        if stage == 'destination' and clean(value) == clean(state['origin']):
            return 'O destino precisa ser diferente da origem.'
    elif stage == 'departure':
        try:
            parsed = parse_date(text, today)
            if parsed < today:
                raise ValueError
            value = parsed.strftime('%d/%m/%Y')
        except ValueError:
            return 'Não consegui entender a data. Informe um dia futuro, por exemplo 23/10/2026.'
    elif stage == 'adults':
        value = choice(text, 'adults')
        if value not in {str(i) for i in range(1, 7)}:
            return 'Nesta primeira versão rodoviária, informe de 1 a 6 adultos.'
    elif stage == 'priority':
        value = choice(text, 'priority')
        bus_words = {'menos conexoes': '3', 'direto': '3', 'mais conforto': '4', 'mais confortavel': '4'}
        value = bus_words.get(clean(str(value)), value)
        if value not in PRIORITIES:
            return PRIORITY_PROMPT
    elif stage == 'budget':
        try:
            value = parse_budget(text)
        except ValueError:
            return BUDGET_PROMPT
        if state.pop('_refine_budget', False):
            state['budget'] = value
            state['stage'] = 'done'
            return format_results(state.get('result', {}), state)
    elif stage == 'confirm':
        if not is_confirmation(text):
            return 'Escolha confirmar para consultar ou nova busca para recomeçar.'
        if on_search:
            on_search('Estou consultando as opções de ônibus. Isso pode levar alguns segundos.')
        request = {key: state[key] for key in ('origin', 'destination', 'departure', 'adults', 'priority', 'budget')}
        result = bus_search(request)
        state['result'] = result
        state['stage'] = 'done'
        return format_results(result, state)
    state[stage] = value
    order = ['origin', 'destination', 'departure', 'adults', 'priority', 'budget']
    next_index = order.index(stage) + 1
    if next_index == len(order):
        state['stage'] = 'confirm'
        return _summary(state)
    state['stage'] = order[next_index]
    return prompt(state)
