"""Official WhatsApp payloads and session-bound choice IDs."""

import re
import uuid
from decimal import Decimal
from urllib.parse import urlsplit
from .flights import rank
from .budget import label

ACTION_PREFIX = '__atlas_action__:'


def incoming(message):
    if message.get('type') == 'text':
        text = message.get('text', {}).get('body')
        # Reserved internal prefix cannot be injected by typing it.
        return text if isinstance(text, str) and not text.startswith(ACTION_PREFIX) else None
    if message.get('type') == 'interactive':
        interactive = message.get('interactive', {})
        kind = interactive.get('type')
        if kind in {'button_reply', 'list_reply'}:
            action = interactive.get(kind, {}).get('id')
            if isinstance(action, str) and re.fullmatch(r'atlas:[a-f0-9]{32}:\d{1,2}', action):
                return ACTION_PREFIX + action
    return None


def text_payload(text):
    return {'type': 'text', 'text': {'preview_url': False, 'body': text}}


def money(value):
    return f'{Decimal(value):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def payload_for(session, reply):
    """Final response payload. Search progress is sent separately without choices."""
    session.values.pop('_choices', None)
    urls = re.findall(r'https://\S+', reply)
    if urls:
        url = urls[-1]
        parsed = urlsplit(url)
        offers = rank(session.values.get('result', {}).get('offers', []), session.values.get('priority', '1'), session.values.get('budget'))
        offer = next((o for o in offers if o.get('url') == url), None)
        if offer and len(url) <= 2048 and parsed.hostname in {'www.google.com', 'www.google.com.br', 'google.com'} and not parsed.username:
            lines = [f"{session.values['origin']} → {session.values['destination']}",
                     f"R$ {money(offer['price'])} • ida e volta • {session.values['adults']} adulto(s)"]
            for index, journey in enumerate(offer['journeys']):
                duration = journey['duration']
                lines.append(f"{'Ida' if index == 0 else 'Volta'}: {journey['departure']} → {journey['arrival']} | {duration//60}h{duration%60:02} | {journey['airlines']} | {journey['stops']} parada(s)")
            lines.append('Horários locais. Link para Google Flights; confira preço final, bagagem e regras. Para outras opções, escreva ofertas.')
            return {'type': 'interactive', 'interactive': {
                'type': 'cta_url', 'body': {'text': '\n'.join(lines)[:1024]},
                'action': {'name': 'cta_url', 'parameters': {'display_text': 'Abrir oferta', 'url': url}}}}
        return text_payload(reply)
    options = []
    if session.step == 'priority':
        options = [('1', 'Menor preço', 'Ordenar pelo total de ida e volta'),
                   ('2', 'Menor duração', 'Somar duração da ida e da volta'),
                   ('3', 'Sem paradas', 'Voos sem paradas nos dois sentidos'),
                   ('4', 'Maior preço', 'Entre as opções retornadas; não indica conforto')]
    elif session.step == 'adults':
        options = [(str(i), f'{i} adulto' + ('s' if i > 1 else ''), '') for i in range(1, 7)]
    elif session.step == 'confirm':
        options = [('sim', 'Confirmar busca', ''), ('cancelar', 'Recomeçar', '')]
    elif session.step == 'budget':
        options = [('sem limite', 'Sem limite', ''), ('cancelar', 'Recomeçar', '')]
    elif session.step == 'complete':
        values = session.values
        if values.get('_price_question'):
            nonce = uuid.uuid4().hex
            actions = [(f'atlas:{nonce}:0', 'sim', 'Sim, ajustar'),
                       (f'atlas:{nonce}:1', 'ofertas', 'Ver ofertas')]
            values['_choices'] = {action: command for action, command, _ in actions}
            return {'type': 'interactive', 'interactive': {
                'type': 'button', 'body': {'text': reply},
                'action': {'buttons': [{'type': 'reply', 'reply': {'id': action, 'title': title}}
                                       for action, _, title in actions]}}}
        offers = rank(values.get('result', {}).get('offers', []), values.get('priority', '1'), values.get('budget'))
        for i, offer in enumerate(offers, 1):
            options.append((f'link {i}', f'Oferta {i} • R$ {money(offer["price"])}'[:24],
                            f"Ida e volta | {offer['duration']//60}h{offer['duration']%60:02} total | até {offer['stops']} parada(s)"[:72]))
        options += [('filtros', 'Mudar preferência', ''), ('datas', 'Alterar datas', ''),
                    ('passageiros', 'Alterar passageiros', ''), ('orcamento', 'Alterar orçamento', ''), ('buscar', 'Atualizar busca', ''),
                    ('cancelar', 'Nova viagem', '')]
        if len(reply) > 1024:
            reply = (f"{values.get('origin')} → {values.get('destination')} | {values.get('adults')} adulto(s). "
                     f"Ida {values.get('departure')}, volta {values.get('return')}. "
                     f"Google Flights • consulta: {values.get('result', {}).get('checked_at', 'horário não disponível')}. "
                     f"{label(values.get('budget'))}. "
                     'Escolha uma oferta abaixo para ver os detalhes e abrir o link. Preços sujeitos a alteração; bagagem e regras precisam de confirmação no fornecedor.')
    if not options or len(reply) > 1024:
        return text_payload(reply)
    nonce = uuid.uuid4().hex
    rows = [{'id': f'atlas:{nonce}:{i}', 'title': title, **({'description': description} if description else {})}
            for i, (_, title, description) in enumerate(options)]
    session.values['_choices'] = {row['id']: option[0] for row, option in zip(rows, options)}
    if session.step in {'confirm', 'budget'}:
        action = {'buttons': [{'type': 'reply', 'reply': {'id': row['id'], 'title': row['title']}} for row in rows]}
        kind = 'button'
    else:
        action = {'button': 'Ver opções', 'sections': [{'title': 'Escolha uma opção', 'rows': rows}]}
        kind = 'list'
    return {'type': 'interactive', 'interactive': {'type': kind, 'body': {'text': reply}, 'action': action}}
