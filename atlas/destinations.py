"""Small editorial catalog. Sources establish places, not live availability.

Portuguese labels are traveler-facing content. Region and interest assignments
are Atlas editorial classifications, not route or accessibility guarantees.
"""

REVIEWED = '2026-09-24'
CITIES = {'sao_paulo': 'São Paulo', 'bogota': 'Bogotá', 'rio_de_janeiro': 'Rio de Janeiro'}
ALIASES = {'sao paulo': 'sao_paulo', 'sp': 'sao_paulo', 'gru': 'sao_paulo',
           'cgh': 'sao_paulo', 'bogota': 'bogota', 'bog': 'bogota',
           'rio de janeiro': 'rio_de_janeiro', 'rio': 'rio_de_janeiro',
           'rj': 'rio_de_janeiro', 'gig': 'rio_de_janeiro', 'sdu': 'rio_de_janeiro'}

PLACES = (
    {'id': 'masp', 'city': 'sao_paulo', 'name': 'MASP', 'region': 'Paulista',
     'interest': 'cultura', 'description': 'Arte na Avenida Paulista.',
     'source': 'https://masp.com.br/pt-br/visite', 'closed_weekdays': [0],
     'closed_dates': ['12-24', '12-25', '12-31', '01-01']},
    {'id': 'trianon', 'city': 'sao_paulo', 'name': 'Parque Trianon', 'region': 'Paulista',
     'interest': 'natureza', 'description': 'Área verde na região da Paulista.',
     'source': 'https://prefeitura.sp.gov.br/web/meio_ambiente/w/parques/regiao_centrooeste/5773'},
    {'id': 'pina', 'city': 'sao_paulo', 'name': 'Pinacoteca — Pina Luz', 'region': 'Luz',
     'interest': 'cultura', 'description': 'Museu de arte na Praça da Luz.',
     'source': 'https://pinacoteca.org.br/visita/como-chegar/', 'closed_weekdays': [1]},
    {'id': 'ibirapuera', 'city': 'sao_paulo', 'name': 'Parque Ibirapuera', 'region': 'Ibirapuera',
     'interest': 'natureza', 'description': 'Parque urbano para uma pausa ao ar livre.',
     'source': 'https://prefeitura.sp.gov.br/meio_ambiente/w/parques/regiao_sul/14062'},
    {'id': 'botero', 'city': 'bogota', 'name': 'Museo Botero', 'region': 'Centro histórico',
     'interest': 'cultura', 'description': 'Coleção de arte em La Candelaria.',
     'source': 'https://visitbogota.co/es/que-hacer-en-bogota/cultura/museo-botero-en-bogota'},
    {'id': 'oro', 'city': 'bogota', 'name': 'Museo del Oro', 'region': 'Centro histórico',
     'interest': 'cultura', 'description': 'Coleções ligadas às culturas pré-hispânicas.',
     'source': 'https://bogota.gov.co/mi-ciudad/turismo/guia-turistica-de-bogota'},
    {'id': 'monserrate', 'city': 'bogota', 'name': 'Monserrate', 'region': 'Monserrate',
     'interest': 'natureza', 'description': 'Mirante nos cerros de Bogotá.',
     'source': 'https://monserrate.co/es/preparar-visita/'},
    {'id': 'jardin', 'city': 'bogota', 'name': 'Jardín Botánico de Bogotá', 'region': 'Jardín Botánico',
     'interest': 'natureza', 'description': 'Jardim botânico e coleções vegetais.',
     'source': 'https://jbb.gov.co/'},
    {'id': 'jbrj', 'city': 'rio_de_janeiro', 'name': 'Jardim Botânico do Rio',
     'region': 'Jardim Botânico', 'interest': 'natureza',
     'description': 'Arboreto histórico e coleções vivas.',
     'source': 'https://www.gov.br/jbrj/pt-br/assuntos/visitacao/horarios-e-ingressos',
     'closed_dates': ['12-25', '01-01'], 'reviewed': '2026-10-01'},
    {'id': 'parque_lage', 'city': 'rio_de_janeiro', 'name': 'Parque Lage',
     'region': 'Jardim Botânico', 'interest': 'natureza',
     'description': 'Parque público aos pés do Corcovado.',
     'source': 'https://eavparquelage.rj.gov.br/o-parque', 'reviewed': '2026-10-01'},
    {'id': 'museu_amanha', 'city': 'rio_de_janeiro', 'name': 'Museu do Amanhã',
     'region': 'Centro', 'interest': 'cultura',
     'description': 'Museu de ciências na Praça Mauá.',
     'source': 'https://museudoamanha.org.br/visite/horarios-e-ingressos/',
     'closed_weekdays': [2], 'reviewed': '2026-10-01'},
    {'id': 'ccbb_rio', 'city': 'rio_de_janeiro', 'name': 'CCBB Rio de Janeiro',
     'region': 'Centro', 'interest': 'cultura',
     'description': 'Centro cultural no coração histórico da cidade.',
     'source': 'https://ccbb.com.br/rio-de-janeiro/normas-de-visitacao/',
     'closed_weekdays': [1], 'reviewed': '2026-10-01'},
)


def get_place(place_id):
    return next(place for place in PLACES if place['id'] == place_id)


def reviewed_on(place):
    """Return the editorial review date recorded for one catalog entry."""
    return place.get('reviewed', REVIEWED)
