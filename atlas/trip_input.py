"""Conservative extraction of explicitly supplied Portuguese trip fields.

This is a local grammar, not unrestricted language understanding. Unrecognized
places and incomplete dates are passed to the existing validators, never guessed.
"""

import re
from .language import clean


MARKERS = re.compile(
    r'\b(?:ida(?: (?:em|no dia|dia))?|(?:e )?(?:volta|voltar|voltando)(?: (?:em|no dia|dia))?'
    r'|(?:para |somos |seremos )?(?:\d+|um|uma|dois|duas|tres|quatro|cinco|seis) (?:adultos?|pessoas?)'
    r'|(?:prefiro |quero )?(?:a )?(?:mais barata|mais barato|mais rapida|mais rapido|sem escalas?|sem paradas?|voo direto|mais cara|mais caro)'
    r'|(?:orcamento(?: de)?|ate r\$|ate (?=\d)|sem limite)'
    r'|(?:em |para )?(?:janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b)'
)


def extract_trip(text):
    value = clean(text)
    fields = {}
    def assign(key, value):
        if key in fields:
            raise ValueError('Encontrei mais de uma informação para o mesmo campo. Informe uma escolha por vez.')
        fields[key] = value
    matches = list(MARKERS.finditer(value))
    if matches and re.search(r'\b(?:nao|ou|talvez)\b', value):
        raise ValueError('Há alternativas ou uma negação na mensagem. Informe uma escolha por vez para eu não interpretar errado.')
    prefix = value[:matches[0].start()] if matches else value
    prefix = prefix.strip(' ,;')
    prefix = re.sub(r'\s*,?\s*(?:de aviao|encontre .*|busque .*)$', '', prefix)
    route = re.fullmatch(r'(?:(?:eu )?(?:quero ir|vou|quero viajar) de |de )?(.+?)\s*(?:->|→| para | pra )\s*(.+)', prefix)
    if route and not re.match(r'(?:(?:eu )?quero ir|mudar|trocar|alterar|eu gostaria)', route[1]):
        fields.update(origin=route[1], destination=route[2])
    else:
        for key, pattern in (
            ('origin', r'(?:(?:eu )?(?:saio|vou sair|quero sair) de|origem(?: e)?)[ :]+(.+)'),
            ('destination', r'(?:(?:eu )?quero ir (?:para|pra)|destino(?: e)?|(?:mudar|trocar|alterar) (?:o )?destino para)[ :]+(.+)'),
        ):
            match = re.fullmatch(pattern, prefix)
            if match:
                fields[key] = match[1]
    for i, match in enumerate(matches):
        marker = match[0]
        tail = value[match.end():matches[i+1].start() if i+1 < len(matches) else len(value)].strip(' ,;')
        tail = re.sub(r'\s+e$', '', tail).strip()
        if re.fullmatch(r'ida(?: (?:em|no dia|dia))?', marker):
            assign('departure', tail)
        elif re.match(r'(?:e )?(?:volta|voltar|voltando)\b', marker):
            assign('return', tail)
        elif re.search(r'\b(?:adultos?|pessoas?)$', marker):
            assign('adults', re.sub(r'^(?:para |somos |seremos )', '', marker))
        elif marker.startswith(('orcamento', 'ate ', 'sem limite')):
            assign('budget', 'sem limite' if marker == 'sem limite' else re.sub(r'^orcamento(?: de)?', '', marker + ' ' + tail).strip())
        elif re.search(r'(?:mais |sem escala|sem parada|voo direto)', marker):
            assign('priority', marker)
        else:
            # A month alone must trigger clarification, not an invented date.
            # If it follows a day, it belongs to the preceding date marker.
            if i and re.match(r'(?:ida|(?:e )?(?:volta|voltar|voltando))\b', matches[i-1][0]):
                key = 'departure' if matches[i-1][0].startswith('ida') else 'return'
                fields[key] += ' ' + marker + (' ' + tail if tail else '')
            else:
                if not re.search(r'\d\s*(?:de\s*)?$', value[:match.start()]):
                    assign('departure', marker + (' ' + tail if tail else ''))
    return fields
