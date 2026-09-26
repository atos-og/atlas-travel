"""Optional, bounded natural-language interpretation through Groq."""

import json
import re
from urllib.request import Request, urlopen


ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
MIN_CONFIDENCE = 0.90

INTENTS = {
    "unknown",
    "unchanged",
    "step_answer",
    "menu",
    "help",
    "flights",
    "itinerary",
    "destination_discovery",
    "nearby_dates",
    "preferences_show",
    "preferences_save",
    "preferences_apply",
    "preferences_delete",
    "cancel",
    "confirm",
    "offers",
    "filters",
    "dates",
    "passengers",
    "budget",
    "search",
    "price_objection",
}

COMMANDS = {
    "menu": "menu",
    "help": "menu",
    "flights": "voos",
    "itinerary": "roteiro",
    "destination_discovery": "explorar destinos",
    "nearby_dates": "datas flexiveis",
    "preferences_show": "minhas preferencias",
    "preferences_save": "salvar preferencias",
    "preferences_apply": "usar preferencias",
    "preferences_delete": "apagar preferencias",
    "cancel": "cancelar",
    "confirm": "sim",
    "offers": "ofertas",
    "filters": "filtros",
    "dates": "datas",
    "passengers": "passageiros",
    "budget": "orcamento",
    "search": "buscar",
    "price_objection": "ta caro",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": sorted(INTENTS)},
        "answer": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["intent", "answer", "confidence"],
    "additionalProperties": False,
}

CANONICAL_INPUTS = set(COMMANDS.values()) | {
    "menu", "recursos", "quais recursos", "me mostre o menu",
    "o que voce faz", "o que vc faz", "oq vc faz", "o que voce pode fazer",
    "o que vc pode fazer", "o que da pra fazer", "oq da pra fazer",
    "como voce pode me ajudar", "como vc pode me ajudar", "como pode me ajudar",
    "como vc me ajuda", "ajuda",
    "voos", "consultar voos", "voltar aos voos", "sair do roteiro",
    "roteiro", "montar roteiro", "planejar passeios", "passeios", "meu roteiro",
    "fontes do roteiro", "ajustar roteiro", "apagar roteiro",
    "explorar destinos", "comparar destinos", "destinos por orcamento",
    "datas flexiveis", "datas proximas", "flexibilidade",
    "minhas preferencias", "salvar preferencias", "usar preferencias", "apagar preferencias",
    "ofertas", "filtros", "datas", "passageiros", "orcamento", "buscar", "cancelar",
    "ta caro", "esta caro", "muito caro", "achei caro", "achei bem caro", "ficou caro",
    "caro demais", "carinho em", "carinho hein", "caro hein", "caro em",
}


def needs_interpretation(text, step, today, values):
    """Avoid spending quota or changing input that local parsing already understands."""
    from .language import clean, is_confirmation, is_greeting, parse_date, choice
    from .trip_input import extract_trip

    value = clean(text)
    if value in CANONICAL_INPUTS or is_greeting(text) or is_confirmation(text):
        return False
    if re.search(r"\b(?:onibus|rodoviari[oa]|criancas?|bebes?)\b", value):
        return False
    try:
        if extract_trip(text):
            return False
    except ValueError:
        return False
    if step in {"origin", "destination"}:
        # Plain place names are resolved and disambiguated by the existing airport catalog.
        return not (1 <= len(value.split()) <= 3 and not re.search(
            r"\b(?:eu|quero|gostaria|parto|saio|moro|vou|pretendo|preciso)\b", value))
    if step in {"departure", "return"}:
        departure = None
        if step == "return" and values.get("departure"):
            from datetime import datetime
            try:
                departure = datetime.strptime(values["departure"], "%d/%m/%Y").date()
            except ValueError:
                pass
        try:
            parse_date(text, today, departure)
            return False
        except ValueError:
            return True
    if step == "adults" and choice(text, step) in {str(i) for i in range(1, 7)}:
        return False
    if step == "priority" and choice(text, step) in {"1", "2", "3", "4"}:
        return False
    if step == "flexibility" and value in {"comparar 1 dia", "manter datas", "datas proximas", "datas exatas", "1", "2"}:
        return False
    if step == "budget":
        from .budget import parse_budget
        try:
            parse_budget(text)
            return False
        except ValueError:
            return True
    return True


def _prompt(text, step, today, values):
    departure = values.get("departure", "not supplied")
    return f"""You are a narrow intent translator for Atlas, a Portuguese travel assistant.
You never answer the traveler. Return only the required JSON object.

Implemented actions:
- menu: show capabilities
- help: explain commands
- flights: return to flight planning
- itinerary: start sightseeing planning; only Sao Paulo and Bogota are supported
- destination_discovery: compare up to three user-selected flight destinations
- nearby_dates: compare exact dates with plus or minus one day
- preferences_show, preferences_save, preferences_apply, preferences_delete
- cancel, confirm, offers, filters, dates, passengers, budget, search, price_objection

Current flight step: {step}
Current date in Sao Paulo: {today.isoformat()}
Known departure date: {departure}

Rules:
1. Choose only an implemented intent. Use unknown when uncertain or when the user asks for an unsupported feature.
2. Never invent a capability, place, airport, date, passenger count, budget, preference, price, or link.
3. Use step_answer only when the message clearly answers the current flight step.
4. For origin or destination, copy only the place stated by the traveler. Never resolve a city or country to an airport code.
5. For departure or return, keep the explicit date expression in Portuguese; do not add a missing day or month.
6. For adults, answer must be a digit from 1 through 6.
7. For priority, answer must be 1 for cheapest, 2 for shortest duration, 3 for nonstop, or 4 for highest price.
8. For budget, answer must contain only the explicit amount or "sem limite".
9. For flexibility, answer must be "comparar 1 dia" or "manter datas".
10. For command intents, answer must be empty. For unchanged or unknown, answer must be empty.
11. A greeting, ordinary place name, date, number, or already clear command may be unchanged.

Traveler message:
{json.dumps(text, ensure_ascii=False)}"""


def interpret(text, step, today, values, config, *, opener=urlopen):
    """Return a validated canonical utterance, or the original text on any doubt."""
    if config.get("ATLAS_NLU_ENABLED") != "true" or not config.get("GROQ_API_KEY"):
        return text
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        return text
    if not needs_interpretation(text, step, today, values):
        return text
    body = json.dumps({
        "model": config.get("GROQ_MODEL") or DEFAULT_MODEL,
        "messages": [{"role": "user", "content": _prompt(text, step, today, values)}],
        "temperature": 0,
        "max_completion_tokens": 512,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "atlas_intent", "strict": True, "schema": SCHEMA},
        },
    }).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": "Bearer " + config["GROQ_API_KEY"],
            "Content-Type": "application/json",
            "User-Agent": "atlas-travel/0.1",
        },
    )
    try:
        with opener(request, timeout=6) as response:
            payload = json.load(response)
        content = payload["choices"][0]["message"]["content"]
        result = json.loads(content)
    except Exception:
        return text
    if not isinstance(result, dict) or set(result) != {"intent", "answer", "confidence"}:
        return text
    intent = result.get("intent")
    answer = result.get("answer")
    confidence = result.get("confidence")
    if intent not in INTENTS or not isinstance(answer, str) or not isinstance(confidence, (int, float)):
        return text
    if not 0 <= confidence <= 1 or confidence < MIN_CONFIDENCE:
        return text
    if intent in {"unknown", "unchanged"}:
        return text
    if intent in COMMANDS:
        return COMMANDS[intent] if not answer else text
    if intent != "step_answer" or not answer or len(answer) > 100:
        return text
    if step == "adults" and answer not in {str(i) for i in range(1, 7)}:
        return text
    if step == "priority" and answer not in {"1", "2", "3", "4"}:
        return text
    if step == "flexibility" and answer not in {"comparar 1 dia", "manter datas"}:
        return text
    if step not in {"origin", "destination", "departure", "return", "adults", "priority", "budget", "flexibility"}:
        return text
    return answer.strip()
