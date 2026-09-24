"""Explicit total-trip budgets in BRL, without floating point arithmetic."""

import re
from decimal import Decimal
from .language import clean

BUDGET_PROMPT = ('Qual é o limite total em reais para as passagens de ida e volta de todos os adultos? '
                 'Ex.: até R$ 1.500, 2 mil ou sem limite. Não inclui hotel e passeios.')


def parse_budget(text):
    value = clean(text)
    if value in {'sem limite', 'sem teto', 'nao sei', 'pular', 'qualquer valor'}:
        return None
    value = re.sub(r'^(?:ate|no maximo|meu limite e|meu orcamento e)\s+', '', value)
    value = re.sub(r'^r\$\s*', '', value)
    value = re.sub(r'\s*(?:reais|real)$', '', value)
    thousand = value.endswith(' mil')
    if thousand:
        value = value[:-4].strip()
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?', value):
        value = value.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d+(?:[,.]\d{1,2})?', value):
        value = value.replace(',', '.')
    else:
        raise ValueError('Informe um único valor total em reais ou sem limite.')
    amount = Decimal(value) * (1000 if thousand else 1)
    if not 0 < amount <= Decimal('10000000') or amount != amount.quantize(Decimal('.01')):
        raise ValueError('Informe um total positivo com até dois centavos decimais.')
    return str(amount.quantize(Decimal('.01')))


def money(value):
    return f'{Decimal(value):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def label(value):
    return 'sem limite de preço' if value is None else f'limite total R$ {money(value)} para todos os adultos (ida e volta)'
