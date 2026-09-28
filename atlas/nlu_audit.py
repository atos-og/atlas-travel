"""Evaluate the configured hosted interpreter with synthetic Portuguese phrases."""

import json
from datetime import date

from .language import clean
from .nlu import interpret
from .webhook import settings


CASES = (
    ('capabilities', 'pode me mostrar tudo que voce sabe fazer por aqui?', 'origin', {}, 'menu'),
    ('origin', 'eu embarco la pelo aeroporto de Confins', 'origin', {}, 'confins'),
    ('itinerary_days', 'acho que dois dias ficam de bom tamanho', 'itinerary:days', {}, '2'),
    ('itinerary_sources', 'de onde sairam as informacoes dos passeios?', 'itinerary:done', {}, 'fontes do roteiro'),
    ('offer_recommendation', 'qual dessas passagens faz mais sentido pra mim?', 'complete', {}, 'recomendar oferta'),
    ('baggage', 'essa tarifa ja vem com mala despachada?', 'complete', {}, 'duvida bagagem'),
    ('bus', 'voce tambem consegue pesquisar passagem rodoviaria?', 'origin', {}, 'duvida onibus'),
    ('alerts', 'tem como voce me avisar se esse valor baixar?', 'complete', {}, 'duvida alertas'),
    ('scope', 'ate onde vai o que voce consegue fazer hoje?', 'origin', {}, 'duvida cobertura'),
    ('thanks', 'valeu demais por ter me ajudado', 'complete', {}, 'obrigado atlas'),
)


def evaluate(config, *, interpreter=interpret, today=None):
    today = today or date.today()
    checks = []
    for label, phrase, step, values, expected in CASES:
        actual = interpreter(phrase, step, today, values, config)
        passed = clean(actual) == clean(expected)
        checks.append({'case': label, 'ok': passed,
                       **({} if passed else {'expected': expected, 'actual': actual})})
    return {'ok': all(item['ok'] for item in checks), 'passed': sum(item['ok'] for item in checks),
            'total': len(checks), 'checks': checks}


def main():
    result = evaluate(settings())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
