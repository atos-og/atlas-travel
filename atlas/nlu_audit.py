"""Evaluate the configured hosted interpreter with synthetic Portuguese phrases."""

import argparse
import json
from datetime import date

from .language import clean
from .nlu import SemanticMessage, interpret
from .webhook import settings


CASES = (
    ('capabilities', 'pode me mostrar tudo que voce sabe fazer por aqui?', 'origin', {}, 'menu'),
    ('origin', 'eu embarco la pelo aeroporto de Confins', 'origin', {}, 'confins'),
    ('flight_route', 'saio de Confins e quero ir para San Andres na Colombia',
     'origin', {}, 'Confins -> San Andres'),
    ('flight_fields', ('quero sair de Confins para San Andres dia 23 de outubro de 2027, '
                       'voltar dia 30, para dois adultos, priorizando o menor preco ate 3000 reais'),
     'origin', {}, {'kind': 'flight', 'fields': [
         'origin', 'destination', 'departure', 'return', 'adults', 'priority', 'budget']}),
    ('itinerary_fields', ('monte um roteiro no Rio de Janeiro por tres dias, sem data, '
                          'com natureza e num ritmo tranquilo'),
     'origin', {}, {'kind': 'itinerary', 'fields': [
         'city', 'start', 'days', 'interest', 'pace']}),
    ('bus_fields', ('quero ir de Belo Horizonte para Sao Paulo de onibus dia 23 de outubro de 2027, '
                    'com dois adultos, na viagem mais rapida e ate 500 reais'),
     'origin', {}, {'kind': 'bus', 'fields': [
         'origin', 'destination', 'departure', 'adults', 'priority', 'budget']}),
    ('itinerary_days', 'acho que dois dias ficam de bom tamanho', 'itinerary:days', {}, '2'),
    ('itinerary_sources', 'de onde sairam as informacoes dos passeios?', 'itinerary:done', {}, 'fontes do roteiro'),
    ('offer_recommendation', 'qual dessas passagens faz mais sentido pra mim?', 'complete', {}, 'recomendar oferta'),
    ('baggage', 'essa tarifa ja vem com mala despachada?', 'complete', {}, 'duvida bagagem'),
    ('bus', 'voce tambem consegue pesquisar passagem rodoviaria?', 'origin', {}, 'duvida onibus'),
    ('bus_search', 'preciso me deslocar pela estrada e queria uma passagem', 'origin', {}, 'onibus'),
    ('alerts', 'tem como voce me avisar se esse valor baixar?', 'complete', {}, 'duvida alertas'),
    ('scope', 'ate onde vai o que voce consegue fazer hoje?', 'origin', {}, 'duvida cobertura'),
    ('thanks', 'valeu demais por ter me ajudado', 'complete', {}, 'obrigado atlas'),
    ('trip_summary', 'junta tudo que ja planejei nessa viagem', 'complete', {}, 'resumo da viagem'),
    ('travel_checklist', 'o que eu preciso conferir antes de viajar?', 'complete', {}, 'checklist da viagem'),
)


def evaluate(config, *, cases=CASES, interpreter=interpret, today=None):
    today = today or date.today()
    checks = []
    for label, phrase, step, values, expected in cases:
        actual = interpreter(phrase, step, today, values, config)
        comparable = actual
        if isinstance(actual, SemanticMessage):
            if (not isinstance(expected, dict) and actual.kind == 'flight'
                    and set(actual.fields) == {'origin', 'destination'}):
                comparable = f"{actual.fields['origin']} -> {actual.fields['destination']}"
            else:
                comparable = {'kind': actual.kind, 'fields': actual.fields}
        if isinstance(expected, dict) and isinstance(actual, SemanticMessage):
            passed = actual.kind == expected['kind'] and set(actual.fields) == set(expected['fields'])
        else:
            passed = (comparable == expected if isinstance(expected, dict) else
                      isinstance(comparable, str) and clean(comparable) == clean(expected))
        checks.append({'case': label, 'ok': passed,
                       **({} if passed else {'expected': expected, 'actual': comparable})})
    return {'ok': all(item['ok'] for item in checks), 'passed': sum(item['ok'] for item in checks),
            'total': len(checks), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases', nargs='*', choices=[case[0] for case in CASES],
                        help='Optional case labels. Omit to run the full corpus.')
    args = parser.parse_args()
    selected = tuple(case for case in CASES if not args.cases or case[0] in args.cases)
    result = evaluate(settings(), cases=selected)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
