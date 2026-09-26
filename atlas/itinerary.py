"""Bounded, sourced sightseeing drafts with an independent conversation overlay."""

import re
from datetime import date, timedelta
from .language import clean, parse_date, is_greeting
from .destinations import ALIASES, CITIES, PLACES, REVIEWED, get_place

START = {'roteiro', 'montar roteiro', 'quero montar um roteiro', 'passeios'}
INTERESTS = {'1': 'cultura', '2': 'natureza', '3': 'misto',
             'cultura': 'cultura', 'museus': 'cultura', 'arte': 'cultura',
             'natureza': 'natureza', 'parques': 'natureza', 'misto': 'misto', 'um pouco de tudo': 'misto'}
PACES = {'1': 'tranquilo', '2': 'equilibrado', 'tranquilo': 'tranquilo',
         'sem pressa': 'tranquilo', 'equilibrado': 'equilibrado'}


def build_plan(city, days, interest, pace, start=None, excluded=()):
    """Prefer a single editorial region per day; never repeat or invent places."""
    if city not in CITIES or type(days) is not int or not 1 <= days <= 3:
        raise ValueError('Unsupported destination or duration')
    if interest not in {'cultura', 'natureza', 'misto'} or pace not in {'tranquilo', 'equilibrado'}:
        raise ValueError('Unsupported preference')
    remaining = [p for p in PLACES if p['city'] == city and p['id'] not in excluded
                 and (interest == 'misto' or p['interest'] == interest)]
    result = []
    for i in range(days):
        day = start + timedelta(days=i) if start else None
        eligible = [p for p in remaining if not day or
                    (day.weekday() not in p.get('closed_weekdays', [])
                     and day.strftime('%m-%d') not in p.get('closed_dates', []))]
        selected = []
        if eligible:
            # Favor the region with the most matching places, then catalog order.
            region = max((p['region'] for p in eligible),
                         key=lambda area: sum(p['region'] == area for p in eligible))
            selected = [p['id'] for p in eligible if p['region'] == region][:1 if pace == 'tranquilo' else 2]
            remaining = [p for p in remaining if p['id'] not in selected]
        result.append({'date': day.isoformat() if day else None, 'places': selected})
    return result


def prompt(state):
    return {
        'city': '*Vamos montar seu roteiro.*\n\nPor enquanto, tenho passeios em São Paulo e Bogotá. Sua busca de voos fica preservada.\n\n*Qual cidade você quer conhecer?*',
        'start': 'Qual será o primeiro dia disponível para passeios? Pode escrever uma data natural ou sem data. Não vou usar automaticamente o dia do voo.',
        'days': 'Quantos dias de passeios? Nesta versão, de 1 a 3 dias.',
        'interest': 'O que você prefere: cultura, natureza ou misto?',
        'pace': '*Qual ritmo combina com você?*\n\n• *Tranquilo:* até 1 local por dia.\n• *Equilibrado:* até 2 na mesma região.\n\nO tempo de deslocamento ainda precisa ser conferido.',
    }[state['stage']]


def summary(state):
    start = date.fromisoformat(state['start']).strftime('%d/%m/%Y') if state.get('start') else 'sem data definida'
    return (f"*Montar roteiro: {CITIES[state['city']]}*\n\n"
            f"• Duração: {state['days']} dia(s)\n• Início: {start}\n"
            f"• Interesses: {state['interest']}\n• Ritmo: {state['pace']}\n\n"
            'É uma proposta com fontes, sem reservas ou preços confirmados.\n\n'
            '*Posso montar?* Escolha abaixo ou digite montar.')


def render(state):
    lines = [f"*Seu roteiro sugerido — {CITIES[state['city']]}*",
             f"{state['interest'].capitalize()} • ritmo {state['pace']}"]
    for i, day in enumerate(state['plan'], 1):
        stamp = ' — ' + date.fromisoformat(day['date']).strftime('%d/%m/%Y') if day['date'] else ''
        lines.append(f'\n*Dia {i}{stamp}*')
        if not day['places']:
            lines.append('Livre: não há outro local no catálogo que atenda a esse dia e aos seus filtros.')
        for pid in day['places']:
            p = get_place(pid)
            lines.append(f"• {p['name']} ({p['region']})")
    lines.append('\n*Antes de sair*\nConfira abertura, ingressos e acessibilidade nas fontes. A disponibilidade nas suas datas não foi verificada. Reserve tempo para refeições e deslocamentos.')
    lines.append(f'\nCatálogo revisado em {REVIEWED}.')
    lines.append('\n*Quer ajustar alguma coisa?*\nUse as opções abaixo ou digite ajustar roteiro. Para os links, fontes do roteiro.')
    return '\n'.join(lines)


def sources(state):
    ids = dict.fromkeys(pid for day in state.get('plan', []) for pid in day['places'])
    return '\n\n'.join([f'*Fontes do roteiro*\nRevisão editorial: {REVIEWED}'] +
                       [f"*{get_place(pid)['name']}*\n{get_place(pid)['source']}" for pid in ids] +
                       ['Para continuar, digite *meu roteiro* ou *voltar aos voos*.'])


def choices(state):
    stage = state.get('stage')
    options = {
        'city': [('São Paulo', 'São Paulo'), ('Bogotá', 'Bogotá')],
        'start': [('sem data', 'Ainda sem data')],
        'days': [(str(i), f'{i} dia' + ('s' if i > 1 else '')) for i in range(1, 4)],
        'interest': [('cultura', 'Cultura'), ('natureza', 'Natureza'), ('misto', 'Um pouco de tudo')],
        'pace': [('tranquilo', 'Tranquilo'), ('equilibrado', 'Equilibrado')],
        'confirm': [('montar', 'Montar roteiro'), ('novo roteiro', 'Alterar dados')],
        'done': [('fontes do roteiro', 'Ver fontes'), ('ajustar roteiro', 'Ajustar roteiro'),
                 ('remover passeio', 'Remover passeio'), ('meu roteiro', 'Ver roteiro')],
        'edit': [('mudar dias', 'Quantidade de dias'), ('mudar inicio', 'Data inicial'),
                 ('mudar interesses', 'Interesses'), ('mudar ritmo', 'Ritmo'), ('novo roteiro', 'Trocar cidade')],
    }.get(stage, [])
    if stage == 'remove':
        ids = dict.fromkeys(pid for day in state.get('plan', []) for pid in day['places'])
        options = [(f'remover {pid}', get_place(pid)['name'][:24]) for pid in ids]
    return options + [('voltar aos voos', 'Voltar aos voos')]


def resume(state):
    """Repeat the current itinerary context without advancing it."""
    stage = state['stage']
    if stage == 'done':
        return render(state)
    if stage == 'confirm':
        return summary(state)
    if stage == 'edit':
        return 'O que deseja ajustar no roteiro? Dias, início, interesses, ritmo ou cidade?'
    if stage == 'remove':
        return 'Escolha um passeio para remover. Vou reorganizar usando apenas os outros locais do catálogo.'
    return prompt(state)


def handle(session, text, today):
    """Return None when this message belongs to the existing flight flow."""
    command = clean(text)
    state = session.values.get('_itinerary')
    if command in {'voltar aos voos', 'sair do roteiro'}:
        if state:
            state['active'] = False
        return 'Voltei à sua busca de passagens. Digite ofertas se já tiver resultados, ou continue respondendo à etapa anterior. Seu roteiro fica salvo; use meu roteiro para retomá-lo.'
    if command == 'apagar roteiro':
        session.values.pop('_itinerary', None)
        return 'Roteiro apagado. Sua busca de passagens foi preservada.'
    if command == 'meu roteiro':
        if state and state.get('plan') is not None:
            state.update(active=True, stage='done')
            return render(state)
        return 'Você ainda não montou um roteiro. Digite roteiro para começar.'
    direct = re.fullmatch(r'(?:quero (?:um |montar um )?)?roteiro (?:para|em|pra) (.+)', command)
    if command in START | {'novo roteiro'} or direct:
        state = {'active': True, 'stage': 'city'}
        session.values['_itinerary'] = state
        if direct:
            city = ALIASES.get(direct[1])
            if city:
                state.update(city=city, stage='start')
            else:
                return 'Ainda não tenho um catálogo para essa cidade. ' + prompt(state)
        return prompt(state)
    if not state or not state.get('active'):
        return None
    if is_greeting(text):
        return 'Olá! Continuamos de onde paramos.\n\n' + resume(state)
    if command == 'ajuda':
        return 'No roteiro: meu roteiro, fontes do roteiro, ajustar roteiro, remover passeio, novo roteiro, apagar roteiro ou voltar aos voos. Cancelar reinicia toda a viagem.'
    if command == 'fontes do roteiro':
        return sources(state) if state.get('plan') is not None else 'Monte o roteiro primeiro para ver as fontes selecionadas.'
    if command == 'ajustar roteiro' and state.get('plan') is not None:
        state['stage'] = 'edit'
        return 'O que deseja ajustar no roteiro? Dias, início, interesses, ritmo ou cidade?'
    if command == 'remover passeio' and state.get('plan') is not None:
        state['stage'] = 'remove'
        return 'Escolha um passeio para remover. Vou reorganizar usando apenas os outros locais do catálogo.'
    stage = state['stage']
    if stage == 'edit':
        target = {'mudar dias': 'days', 'dias': 'days', 'mudar inicio': 'start', 'inicio': 'start',
                  'mudar interesses': 'interest', 'interesses': 'interest',
                  'mudar ritmo': 'pace', 'ritmo': 'pace'}.get(command)
        if not target:
            return 'Escolha mudar dias, mudar início, mudar interesses, mudar ritmo ou novo roteiro.'
        state['stage'] = target
        return prompt(state)
    if stage == 'remove':
        ids = {pid for day in state['plan'] for pid in day['places']}
        pid = command.removeprefix('remover ')
        if pid not in ids:
            return 'Escolha um passeio do menu atual ou digite meu roteiro.'
        state.setdefault('excluded', []).append(pid)
        state.pop('plan', None)
        state['stage'] = 'confirm'
        return summary(state)
    if stage == 'city':
        city = ALIASES.get(command)
        if not city:
            return 'A cobertura de roteiros por enquanto é São Paulo ou Bogotá. Qual delas?'
        state['city'] = city
    elif stage == 'start':
        try:
            start = None if command in {'sem data', 'ainda sem data'} else parse_date(text, today)
            if start and (start < today or start > date.max - timedelta(days=2)):
                raise ValueError()
            state['start'] = start.isoformat() if start else None
        except ValueError:
            return 'Informe uma data futura completa para começar os passeios ou escreva sem data.'
    elif stage == 'days':
        match = re.fullmatch(r'([1-3])(?: dias?)?', command)
        words = {'um': 1, 'dois': 2, 'tres': 3, 'um dia': 1, 'dois dias': 2, 'tres dias': 3}
        days = int(match[1]) if match else words.get(command)
        if not days:
            return 'Posso montar de 1 a 3 dias nesta versão. Quantos dias de passeios?'
        state['days'] = days
    elif stage == 'interest':
        if command not in INTERESTS:
            return 'Escolha cultura, natureza ou misto. Outros interesses ainda não têm catálogo nesta versão.'
        state['interest'] = INTERESTS[command]
    elif stage == 'pace':
        if command not in PACES:
            return prompt(state)
        state['pace'] = PACES[command]
    elif stage == 'confirm':
        if command not in {'montar', 'sim', 'confirmar', 'pode montar'}:
            return summary(state)
        start = date.fromisoformat(state['start']) if state.get('start') else None
        if start and start < today:
            state['stage'] = 'start'
            return 'A data inicial passou. ' + prompt(state)
        state['plan'] = build_plan(state['city'], state['days'], state['interest'], state['pace'], start, state.get('excluded', []))
        state['stage'] = 'done'
        return render(state)
    else:
        return 'Digite ajustar roteiro, remover passeio, fontes do roteiro ou voltar aos voos.'
    state.pop('plan', None)
    for key in ('city', 'start', 'days', 'interest', 'pace'):
        if key not in state:
            state['stage'] = key
            return prompt(state)
    state['stage'] = 'confirm'
    return summary(state)
