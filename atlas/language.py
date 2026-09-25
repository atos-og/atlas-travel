"""Deterministic Portuguese input parsing; ambiguous dates require clarification."""

import re
import unicodedata
from datetime import date, datetime, timedelta, timezone


def clean(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', text.lower())
                           if unicodedata.category(c) != 'Mn').strip(' .!?').split())


def local_today():
    return datetime.now(timezone(timedelta(hours=-3))).date()


MONTHS = {name: i for i, name in enumerate(
    'janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split(), 1)}


def parse_date(text, today, departure=None):
    value = clean(text)
    value = re.sub(r'^(?:(?:eu )?quero (?:ir|voltar|viajar)|(?:a )?(?:ida|volta)(?: sera| e)?|vou(?: viajar| voltar)?)(?: no| em)?\s+', '', value)
    value = re.sub(r'^em (?=\d{1,2}(?:/| de ))', '', value)
    value = re.sub(r'^(?:no )?(?:dia )?', '', value)
    relative = {'hoje': 0, 'amanha': 1, 'depois de amanha': 2}
    if value in relative:
        return today + timedelta(days=relative[value])
    match = re.fullmatch(r'(?:daqui a|em) (\d{1,3}|uma semana|duas semanas)(?: dias?)?', value)
    if match:
        amount = {'uma semana': 7, 'duas semanas': 14}.get(match[1])
        return today + timedelta(days=amount if amount is not None else int(match[1]))
    match = re.fullmatch(r'(\d{1,3}) dias? depois|(?:uma semana|7 dias) depois', value)
    if match and departure:
        return departure + timedelta(days=int(match[1]) if match[1] else 7)
    match = re.fullmatch(r'(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{4}))?', value)
    if match:
        return date(int(match[3] or today.year), int(match[2]), int(match[1]))
    match = re.fullmatch(r'(\d{1,2}) (?:de )?([a-z]+)(?: (?:de |do |desse |deste |no |nesse |neste )?(\d{4}|ano|ano que vem|proximo ano))?', value)
    if match and match[2] in MONTHS:
        year_text = match[3]
        year = today.year + 1 if year_text in {'ano que vem', 'proximo ano'} else int(year_text) if year_text and year_text.isdigit() else today.year
        return date(year, MONTHS[match[2]], int(match[1]))
    raise ValueError('Informe dia, mês e, se necessário, ano; não foi possível interpretar a data.')


def choice(text, step):
    value = clean(text)
    if step == 'priority':
        value = re.sub(r'^(?:quero |prefiro |a |o )+', '', value)
        return {'mais barata': '1', 'mais barato': '1', 'menor preco': '1', 'barata': '1',
                'mais em conta': '1', 'menor valor': '1', 'mais economica': '1', 'mais economico': '1',
                'mais rapida': '2', 'mais rapido': '2', 'menor duracao': '2',
                'menos tempo': '2', 'mais curta': '2', 'mais curto': '2',
                'sem escala': '3', 'sem escalas': '3', 'sem parada': '3', 'sem paradas': '3',
                'sem conexao': '3', 'sem conexoes': '3', 'direta': '3', 'direto': '3',
                'voo direto': '3', 'mais cara': '4', 'mais caro': '4', 'maior preco': '4'}.get(value, text)
    if step == 'adults':
        value = re.sub(r'^(?:somos|vai ser|serao) ', '', value)
        value = re.sub(r' (?:adultos?|pessoas?|passageiros?)$', '', value)
        return {'um': '1', 'uma': '1', 'so eu': '1', 'sozinho': '1', 'sozinha': '1',
                'vou sozinho': '1', 'vou sozinha': '1', 'um adulto': '1', 'uma adulta': '1',
                'casal': '2', 'um casal': '2', 'dois': '2', 'duas': '2', 'tres': '3',
                'quatro': '4', 'cinco': '5', 'seis': '6'}.get(value, value)
    return text
