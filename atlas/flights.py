"""Provider-neutral flight results, explicit airport resolution and ranking."""

import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from .budget import money, label


def plain(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold().strip())
                   if unicodedata.category(c) != 'Mn')


AIRPORTS = {
    'bh': 'CNF', 'belo horizonte': 'CNF', 'confins': 'CNF',
    'guarulhos': 'GRU', 'congonhas': 'CGH', 'campinas': 'VCP',
    'galeao': 'GIG', 'santos dumont': 'SDU', 'brasilia': 'BSB',
    'salvador': 'SSA', 'recife': 'REC', 'fortaleza': 'FOR',
    'florianopolis': 'FLN', 'porto alegre': 'POA', 'curitiba': 'CWB',
    'bogota': 'BOG', 'medellin': 'MDE', 'cartagena': 'CTG',
    'san andres': 'ADZ', 'lima': 'LIM', 'santiago': 'SCL',
    'lisboa': 'LIS', 'porto': 'OPO', 'madrid': 'MAD',
}
AMBIGUOUS = {
    'sao paulo': 'Escolha GRU (Guarulhos), CGH (Congonhas) ou VCP (Campinas).',
    'sp': 'Escolha GRU (Guarulhos), CGH (Congonhas) ou VCP (Campinas).',
    'rio': 'Escolha GIG (Galeão) ou SDU (Santos Dumont).',
    'rio de janeiro': 'Escolha GIG (Galeão) ou SDU (Santos Dumont).',
    'colombia': 'Qual destino na Colômbia? Bogotá (BOG), Medellín (MDE), Cartagena (CTG) ou San Andrés (ADZ)?',
    'buenos aires': 'Escolha EZE (Ezeiza) ou AEP (Aeroparque).',
}


def resolve_airport(text):
    name = plain(text)
    if name in AMBIGUOUS:
        return None, AMBIGUOUS[name]
    if name in AIRPORTS:
        return AIRPORTS[name], None
    if re.fullmatch('[A-Za-z]{3}', text.strip()):
        return text.strip().upper(), None
    return None, 'Ainda não reconheço essa cidade. Informe o código de três letras do aeroporto (ex.: CNF, GRU, BOG).'


def search(values):
    """Run the unofficial provider in an isolated, time-bounded child process."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'atlas.providers.google_flights'],
            input=json.dumps(values), capture_output=True, text=True,
            encoding='utf-8', timeout=55,
        )
        if result.returncode != 0:
            return {'status': 'unavailable', 'offers': []}
        payload = json.loads(result.stdout)
        return payload if isinstance(payload, dict) else {'status': 'changed', 'offers': []}
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'offers': []}
    except (OSError, ValueError):
        return {'status': 'unavailable', 'offers': []}


def rank(offers, priority, budget=None):
    unique = {}
    for offer in offers:
        if budget is not None and Decimal(offer['price']) > Decimal(budget):
            continue
        if priority == '3' and offer['stops'] != 0:
            continue
        key = json.dumps(offer['journeys'], sort_keys=True)
        if key not in unique or Decimal(offer['price']) < Decimal(unique[key]['price']):
            unique[key] = offer
    candidates = list(unique.values())
    def key(o):
        price = Decimal(o['price'])
        if priority == '2':
            return o['duration'], price, o['stops']
        if priority == '4':
            return -price, o['duration'], o['stops']
        return price, o['stops'], o['duration']
    return sorted(candidates, key=key)[:4]


def format_results(result, values):
    from .flexible import coverage
    note = coverage(result)
    message = _format_results(result, values)
    if note:
        return note + '\n' + message + '\nDigite salvar preferências para reutilizar origem, adultos e ordenação em outra viagem.'
    return message + '\nDicas: datas flexíveis compara ±1 dia; salvar preferências guarda origem, adultos e ordenação para outra viagem.'


def _format_results(result, values):
    messages = {
        'empty': 'A fonte não retornou opções para esses critérios. Isso não prova ausência de voos.',
        'timeout': 'A consulta demorou além do limite. Não tenho tarifas confirmadas para mostrar.',
        'invalid': 'A fonte não aceitou os aeroportos ou as datas. Confira os códigos e tente novamente.',
        'changed': 'A fonte retornou dados que não consegui validar. Não vou apresentar preços incompletos.',
        'unavailable': 'A fonte de voos está indisponível no momento. Não consegui consultar tarifas.',
    }
    if result.get('status') != 'success':
        return messages.get(result.get('status'), messages['unavailable']) + '\nUse buscar para tentar novamente, datas para ajustar ou cancelar para recomeçar.'
    selected = rank(result['offers'], values['priority'], values.get('budget'))
    if not selected:
        eligible = rank(result['offers'], '3' if values['priority'] == '3' else '1')
        if values.get('budget') is not None and eligible:
            cheapest = eligible[0]['price']
            return (f"Nenhuma das ofertas retornadas cabe no {label(values['budget'])}. "
                    f"A menor tarifa encontrada para os critérios foi R$ {money(cheapest)}, acima do limite. "
                    f"Consulta: {result.get('checked_at', 'horário não disponível')}. "
                    'Isso não prova ausência de tarifas mais baratas em outras fontes. '
                    'Use orçamento para ajustar o total, datas para mudar a viagem ou buscar para atualizar.')
        return messages['empty'] + '\nUse filtros para mudar a preferência ou cancelar para recomeçar.'
    stamp = result.get('checked_at', datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC'))
    order = {'1': 'menor preço', '2': 'menor duração total', '3': 'sem paradas', '4': 'maior preço'}[values['priority']]
    lines = [f"{values['origin']} → {values['destination']} | ida e volta | {values.get('adults', '1')} adulto(s) | econômica",
             f"Google Flights • {stamp}", f"Ordem: {order}, entre as opções retornadas."]
    if values.get('budget') is not None:
        lines.append(label(values['budget']) + '.')
    for i, offer in enumerate(selected, 1):
        price = f"{Decimal(offer['price']):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
        lines.append(f"\n{i}. R$ {price} no total • até {offer['stops']} parada(s) por sentido")
        if offer.get('travel_dates'):
            lines.append(f"Datas: {offer['travel_dates']['departure']} → {offer['travel_dates']['return']}")
        for j, journey in enumerate(offer['journeys']):
            duration = journey['duration']
            lines.append(f"{'Ida' if j == 0 else 'Volta'}: {journey['departure']} → {journey['arrival']} | {duration//60}h{duration%60:02} | {journey['airlines']}")
        lines.append('Ver oferta: link ' + str(i) if offer.get('url') else 'Link indisponível para esta opção.')
    lines.append('\nHorários locais dos aeroportos. Bagagem e regras tarifárias não confirmadas. Preço sujeito a alteração no fornecedor.')
    lines.append('Digite link 1 (ou 2, 3, 4), filtros, datas, passageiros, orçamento, buscar ou cancelar.')
    return '\n'.join(lines)
