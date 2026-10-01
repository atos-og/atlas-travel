"""Optional, bounded natural-language interpretation through Groq."""

import json
import re
from dataclasses import dataclass
from urllib.request import Request, urlopen


ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
MIN_CONFIDENCE = 0.90
LOW_RISK_CONFIDENCE = 0.80

INTENTS = {
    "unknown",
    "unchanged",
    "step_answer",
    "trip_route",
    "flight_request",
    "itinerary_request",
    "bus_request",
    "clarify_request",
    "unsupported_request",
    "social_reply",
    "faq_identity",
    "faq_how",
    "faq_sources",
    "menu",
    "help",
    "flights",
    "bus_search",
    "itinerary",
    "itinerary_show",
    "itinerary_sources",
    "itinerary_edit",
    "itinerary_remove",
    "itinerary_delete",
    "itinerary_new",
    "destination_discovery",
    "destination_discovery_restart",
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
    "offer_recommendation",
    "offer_comparison",
    "faq_baggage",
    "faq_purchase",
    "faq_prices",
    "faq_privacy",
    "faq_bus",
    "faq_alerts",
    "faq_scope",
    "faq_comfort",
    "gratitude",
    "trip_summary",
    "travel_checklist",
}

COMMANDS = {
    "menu": "menu",
    "help": "menu",
    "flights": "voos",
    "bus_search": "onibus",
    "itinerary": "roteiro",
    "itinerary_show": "meu roteiro",
    "itinerary_sources": "fontes do roteiro",
    "itinerary_edit": "ajustar roteiro",
    "itinerary_remove": "remover passeio",
    "itinerary_delete": "apagar roteiro",
    "itinerary_new": "novo roteiro",
    "destination_discovery": "explorar destinos",
    "destination_discovery_restart": "refazer comparacao",
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
    "offer_recommendation": "recomendar oferta",
    "offer_comparison": "comparar ofertas",
    "faq_baggage": "duvida bagagem",
    "faq_purchase": "duvida compra",
    "faq_prices": "duvida precos",
    "faq_privacy": "duvida privacidade",
    "faq_bus": "duvida onibus",
    "faq_alerts": "duvida alertas",
    "faq_scope": "duvida cobertura",
    "faq_comfort": "duvida conforto",
    "gratitude": "obrigado atlas",
    "trip_summary": "resumo da viagem",
    "travel_checklist": "checklist da viagem",
    "clarify_request": "esclarecer pedido",
    "unsupported_request": "recurso indisponivel",
    "social_reply": "conversa casual",
    "faq_identity": "duvida identidade",
    "faq_how": "duvida funcionamento",
    "faq_sources": "duvida fontes",
}

LOW_RISK_INTENTS = {
    'menu', 'help', 'offer_recommendation', 'offer_comparison',
    'faq_baggage', 'faq_purchase', 'faq_prices', 'faq_privacy',
    'faq_bus', 'faq_alerts', 'faq_scope', 'faq_comfort', 'gratitude',
    'trip_summary', 'travel_checklist',
    'clarify_request', 'unsupported_request', 'social_reply',
    'faq_identity', 'faq_how', 'faq_sources',
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


@dataclass(frozen=True)
class SemanticMessage:
    """Validated structured meaning passed to the deterministic conversation."""
    kind: str
    fields: dict


SEMANTIC_INTENTS = {'flight_request', 'itinerary_request', 'bus_request'}
FLIGHT_FIELDS = {'origin', 'destination', 'departure', 'return', 'adults', 'priority', 'budget'}
ITINERARY_FIELDS = {'city', 'start', 'days', 'interest', 'pace'}
BUS_FIELDS = {'origin', 'destination', 'departure', 'adults', 'priority', 'budget'}


def _decode_fields(answer, allowed):
    """Read the model's inner JSON without accepting extra or empty values."""
    try:
        fields = json.loads(answer)
    except (TypeError, ValueError):
        return None
    if not isinstance(fields, dict) or not fields or not set(fields) <= allowed:
        return None
    normalized = {}
    for key, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            return None
        value = str(value).strip()
        if not value or len(value) > 100:
            return None
        normalized[key] = value
    return normalized


def _semantic_message(intent, answer, text, step):
    """Validate structured extractions before they can change conversation state."""
    from .language import clean

    source = clean(text)
    passenger_cue = re.search(r'\b(?:adultos?|pessoas?|passageiros?|viajantes?|somos|casal|eu e|minha esposa|meu marido|nos dois)\b', source)
    priority_cue = re.search(r'\b(?:barat|econom|preco|valor|rapid|duracao|tempo|sem escala|sem parada|diret|conexao|car|confort)\w*', source)
    budget_cue = re.search(r'\b(?:orcamento|limite|ate|reais|r\$|sem limite)\b|\d', source)
    date_cue = re.search(
        r'\b(?:hoje|amanha|depois de amanha|dia|dias?|sem data|janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b|\d',
        source)
    if intent == 'flight_request':
        if step.startswith(('itinerary:', 'bus:', 'discovery:')):
            return None
        fields = _decode_fields(answer, FLIGHT_FIELDS)
        if not fields:
            return None
        for key in ('origin', 'destination'):
            if key in fields and clean(fields[key]) not in source:
                return None
        if 'adults' in fields and fields['adults'] not in {str(i) for i in range(1, 7)}:
            return None
        if 'adults' in fields and not passenger_cue:
            return None
        if 'priority' in fields and fields['priority'] not in {'1', '2', '3', '4'}:
            return None
        if 'priority' in fields and not priority_cue:
            return None
        if 'budget' in fields and not budget_cue:
            return None
        if 'departure' in fields and not date_cue:
            return None
        if 'return' in fields and (not date_cue or not re.search(
                r'\b(?:volta|voltar|retorno|retornar|regresso|regressar)\w*\b', source)):
            return None
        return SemanticMessage('flight', fields)
    if intent == 'itinerary_request':
        fields = _decode_fields(answer, ITINERARY_FIELDS)
        if not fields or 'city' not in fields:
            return None
        from .destinations import ALIASES
        city_key = ALIASES.get(clean(fields['city']))
        if not city_key or not any(mapped == city_key and re.search(
                rf'\b{re.escape(alias)}\b', source) for alias, mapped in ALIASES.items()):
            return None
        if fields.get('days') and fields['days'] not in {'1', '2', '3'}:
            return None
        if fields.get('days') and not re.search(r'\b(?:um|dois|tres|1|2|3) dias?\b', source):
            return None
        if fields.get('interest') and fields['interest'] not in {'cultura', 'natureza', 'misto'}:
            return None
        if fields.get('interest') and not re.search(r'\b(?:cultura|museu|arte|natureza|parque|misto|de tudo)\w*', source):
            return None
        if fields.get('pace') and fields['pace'] not in {'tranquilo', 'equilibrado'}:
            return None
        if fields.get('pace') and not re.search(r'\b(?:tranquil|sem pressa|equilibrad)\w*', source):
            return None
        if 'start' in fields and not date_cue:
            return None
        return SemanticMessage('itinerary', fields)
    if intent == 'bus_request':
        fields = _decode_fields(answer, BUS_FIELDS)
        if not fields:
            return None
        for key in ('origin', 'destination'):
            if key in fields and clean(fields[key]) not in source:
                return None
        if 'adults' in fields and fields['adults'] not in {str(i) for i in range(1, 7)}:
            return None
        if 'adults' in fields and not passenger_cue:
            return None
        if 'priority' in fields and fields['priority'] not in {'1', '2', '3', '4'}:
            return None
        if 'priority' in fields and not priority_cue:
            return None
        if 'budget' in fields and not budget_cue:
            return None
        if 'departure' in fields and not date_cue:
            return None
        return SemanticMessage('bus', fields)
    return None

CANONICAL_INPUTS = set(COMMANDS.values()) | {
    "menu", "recursos", "quais recursos", "me mostre o menu",
    "o que voce faz", "o que vc faz", "oq vc faz", "o que voce pode fazer",
    "o que vc pode fazer", "o que da pra fazer", "oq da pra fazer",
    "como voce pode me ajudar", "como vc pode me ajudar", "como pode me ajudar",
    "como vc me ajuda", "ajuda",
    "voos", "consultar voos", "voltar aos voos", "sair do roteiro",
    "onibus", "consultar onibus", "buscar onibus", "passagem de onibus", "passagens de onibus",
    "roteiro", "montar roteiro", "planejar passeios", "passeios", "meu roteiro",
    "fontes do roteiro", "ajustar roteiro", "apagar roteiro",
    "explorar destinos", "comparar destinos", "destinos por orcamento",
    "datas flexiveis", "datas proximas", "flexibilidade",
    "minhas preferencias", "salvar preferencias", "usar preferencias", "apagar preferencias",
    "ofertas", "filtros", "datas", "passageiros", "orcamento", "buscar", "cancelar",
    "ta caro", "esta caro", "muito caro", "achei caro", "achei bem caro", "ficou caro",
    "caro demais", "carinho em", "carinho hein", "caro hein", "caro em",
    "recomendar oferta", "comparar ofertas", "duvida bagagem", "duvida compra",
    "duvida precos", "duvida privacidade", "duvida onibus", "duvida alertas",
    "duvida cobertura", "duvida conforto", "obrigado atlas",
    "resumo da viagem", "resumo viagem", "checklist da viagem", "checklist viagem",
}


def needs_interpretation(text, step, today, values):
    """Avoid spending quota or changing input that local parsing already understands."""
    from .language import clean, is_confirmation, is_greeting, parse_date, choice
    from .trip_input import extract_trip

    value = clean(text)
    if value in CANONICAL_INPUTS or is_greeting(text) or is_confirmation(text):
        return False
    if re.search(r"\b(?:criancas?|bebes?)\b", value):
        return False
    if re.search(r"\b(?:onibus|rodoviari[oa])\b", value):
        # Natural bus requests may contain several criteria at once. The model
        # extracts only explicit fields; Python keeps control of validation.
        return True
    if re.search(r'\b(?:roteiro|passeios?|programacao da viagem)\b', value):
        return True
    if (len(value.split()) >= 7 and
            re.search(r'\b(?:viaj|voo|passagem|embar|saio|sair|parto|partir|ir|vou|destino|chegada)\w*\b', value) and
            re.search(r'\b(?:de|do|da)\b.+\b(?:para|pra|ate)\b', value)):
        # Long requests frequently combine route, dates, passengers and budget.
        # Let the semantic extractor separate them before the narrow regex parser.
        return True
    if step.startswith("bus:"):
        stage = step.split(":", 1)[1]
        if stage in {'origin', 'destination'} and 1 <= len(value.split()) <= 5:
            return False
        if stage == 'departure':
            try:
                parse_date(text, today)
                return False
            except ValueError:
                return True
        if stage == 'adults' and choice(text, 'adults') in {str(i) for i in range(1, 7)}:
            return False
        if stage == 'priority' and (choice(text, 'priority') in {'1', '2'} or value in {
                'menos conexoes', 'direto', 'mais conforto', 'mais confortavel'}):
            return False
        if stage == 'budget':
            from .budget import parse_budget
            try:
                parse_budget(text)
                return False
            except ValueError:
                return True
        if stage == 'confirm':
            return not is_confirmation(text)
        return True
    if step.startswith("itinerary:"):
        stage = step.split(":", 1)[1]
        if stage == "city" and value in {"sao paulo", "sp", "gru", "cgh", "bogota", "bog",
                                          "rio de janeiro", "rio", "rj", "gig", "sdu"}:
            return False
        if stage == "start":
            if value in {"sem data", "ainda sem data"}:
                return False
            try:
                parse_date(text, today)
                return False
            except ValueError:
                return True
        if stage == "days" and value in {"1", "2", "3", "1 dia", "2 dias", "3 dias",
                                          "um", "dois", "tres", "um dia", "dois dias", "tres dias"}:
            return False
        if stage == "interest" and value in {"1", "2", "3", "cultura", "museus", "arte",
                                              "natureza", "parques", "misto", "um pouco de tudo"}:
            return False
        if stage == "pace" and value in {"1", "2", "tranquilo", "sem pressa", "equilibrado"}:
            return False
        if stage in {"confirm", "done", "remove"}:
            return not is_confirmation(text)
        if stage == "edit" and value in {"mudar dias", "dias", "mudar inicio", "inicio",
                                          "mudar interesses", "interesses", "mudar ritmo", "ritmo"}:
            return False
        return True
    if step.startswith("discovery:"):
        stage = step.split(":", 1)[1]
        if stage == "origin" and 1 <= len(value.split()) <= 3:
            return False
        if stage in {"departure", "return"}:
            departure = None
            if stage == "return" and values.get("departure"):
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
        if stage == "adults" and choice(text, "adults") in {str(i) for i in range(1, 7)}:
            return False
        if stage == "budget":
            from .budget import parse_budget
            try:
                return parse_budget(text) is None
            except ValueError:
                return True
        if stage == "candidates":
            from .discovery import destinations
            try:
                destinations(text, values.get("origin", ""))
                return False
            except ValueError:
                return True
        if stage == "confirm":
            return not is_confirmation(text)
        if stage == "done" and re.fullmatch(r"(?:escolher )?destino [1-3]", value):
            return False
        return True
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
    known = {key: values[key] for key in (
        'origin', 'destination', 'departure', 'return', 'adults', 'priority',
        'budget', 'city', 'start', 'days', 'interest', 'pace')
             if key in values and isinstance(values[key], (str, int, float, type(None)))}
    overlay_rules = ""
    if step.startswith("itinerary:"):
        overlay_rules = """
Itinerary step answers:
- city: answer must be "sao paulo", "bogota", or "rio de janeiro" and only when explicitly stated
- start: preserve the explicit Portuguese date expression, or "sem data"
- days: answer must be 1, 2, or 3
- interest: answer must be "cultura", "natureza", or "misto"
- pace: answer must be "tranquilo" or "equilibrado"
- edit: answer may be "mudar dias", "mudar inicio", "mudar interesses", or "mudar ritmo"
Do not use step_answer for removing a place or selecting a place that was not named explicitly.
"""
    elif step.startswith("discovery:"):
        overlay_rules = """
Destination-comparison step answers:
- origin: copy only the explicit place; never resolve it to an airport code
- departure or return: preserve the explicit Portuguese date expression
- adults: answer must be a digit from 1 through 6
- budget: copy only the explicit amount
- candidates: copy 1 to 3 explicitly named places separated by commas; never add or resolve a place
- done: answer may be "destino 1", "destino 2", or "destino 3" only when explicitly selected
"""
    return f"""You are a narrow intent translator for Atlas, a Portuguese travel assistant.
You never answer the traveler. Return only the required JSON object.

Implemented actions:
- menu: show capabilities
- help: explain commands
- flights: return to flight planning
- itinerary: start sightseeing planning; only Sao Paulo, Bogota, and Rio de Janeiro are supported
- bus_search: start the implemented guided bus flow; live prices still require configured partner access
- itinerary_show: display an itinerary that was already generated
- itinerary_sources: show sources for an itinerary that was already generated
- itinerary_edit: enter the existing itinerary editing flow
- itinerary_remove: enter the existing place-removal flow
- itinerary_delete: delete the saved itinerary after an explicit request
- itinerary_new: restart the itinerary questions after an explicit request
- destination_discovery: compare up to three user-selected flight destinations
- destination_discovery_restart: restart the destination-comparison questions
- nearby_dates: compare exact dates with plus or minus one day
- preferences_show, preferences_save, preferences_apply, preferences_delete
- cancel, confirm, offers, filters, dates, passengers, budget, search, price_objection
- offer_recommendation: explain the first currently ranked offer without inventing a new option
- offer_comparison: compare only the offers already returned by Atlas
- faq_baggage: questions about baggage or included luggage
- faq_purchase: questions about buying, booking, payment, or ticket issuance
- faq_prices: questions about price freshness, guarantees, or why a quoted price changed
- faq_privacy: questions about stored conversation data or the hosted language model
- faq_bus: questions about searching or comparing bus tickets
- faq_alerts: questions about monitoring prices or receiving future price alerts
- faq_scope: questions about supported cities, airports, itinerary coverage, or product limits
- faq_comfort: questions about ranking by comfort, seats, cabin quality, or service quality
- gratitude: a short thank-you directed to Atlas
- trip_summary: show a summary of flight and itinerary data already stored in the current session
- travel_checklist: show a deterministic preparation checklist for the current trip
- trip_route: extract two explicitly stated flight places from one message; answer exactly "origin -> destination"
- flight_request: extract one or more explicit flight criteria into a JSON string
- itinerary_request: start or prefill a sightseeing plan from explicit details in one message
- bus_request: start or prefill a bus search from explicit details in one message
- clarify_request: the traveler appears to want an Atlas feature, but the requested action or required detail is unclear
- unsupported_request: the request is understandable but Atlas does not implement it
- social_reply: ordinary social conversation that does not ask for travel data or a product action
- faq_identity, faq_how, faq_sources: questions about Atlas, how it works, or where travel results come from

Current guided step: {step}
Current date in Sao Paulo: {today.isoformat()}
Known departure date: {departure}
Known current criteria: {json.dumps(known, ensure_ascii=False)}
{overlay_rules}

Rules:
1. Choose only an implemented intent. Use unknown when uncertain or when the user asks for an unsupported feature.
2. Never invent a capability, place, airport, date, passenger count, budget, preference, price, or link.
3. Use step_answer only when the message clearly answers the current flight step.
   Use trip_route when both an origin and a destination are explicitly present, even during the origin or destination step.
4. For origin or destination, copy only the place stated by the traveler. Never resolve a city or country to an airport code.
5. For departure or return, keep the explicit date expression in Portuguese; do not add a missing day or month.
6. For adults, answer must be a digit from 1 through 6.
7. For priority, answer must be 1 for cheapest, 2 for shortest duration, 3 for nonstop, or 4 for highest price.
8. For budget, answer must contain only the explicit amount or "sem limite".
9. For flexibility, answer must be "comparar 1 dia" or "manter datas".
10. For trip_route, copy the two explicit place names and format the answer exactly as "origin -> destination". Never replace a place with an airport code or infer a city from a country.
11. For flight_request, bus_request, or itinerary_request, put a compact JSON object inside answer. Include only fields explicitly stated in the current message:
    - flight_request keys: origin, destination, departure, return, adults, priority, budget
    - bus_request keys: origin, destination, departure, adults, priority, budget
    - itinerary_request keys: city, start, days, interest, pace
    Copy place and date wording instead of resolving it. Normalize adults to 1-6; priority to 1=cheapest, 2=shortest, 3=nonstop/fewer connections, 4=highest price for flights or comfort for buses; itinerary interest to cultura/natureza/misto and pace to tranquilo/equilibrado. Use "sem data" or "sem limite" only when explicitly stated.
12. Prefer a structured request when one message provides multiple criteria, corrects a criterion that is not the current guided step, or starts an itinerary/bus request with details. Do not copy known criteria into answer unless the traveler repeats or changes them now.
13. For command intents, answer must be empty. For unchanged, unknown, clarify_request, unsupported_request, social_reply, and FAQ intents, answer must be empty.
14. A greeting, ordinary place name, date, number, or already clear command may be unchanged.
15. Distinguish these common requests carefully:
    - "qual dessas passagens faz mais sentido pra mim?" is offer_recommendation
    - "me explica a diferenca entre elas" is offer_comparison
    - "de onde sairam as informacoes dos passeios?" is itinerary_sources
    - "essa tarifa ja vem com mala despachada?" is faq_baggage
    - "voce tambem pesquisa passagem rodoviaria?" is faq_bus
    - "quero cotar uma passagem rodoviaria" is bus_search
    - "tem como voce me avisar se esse valor baixar?" is faq_alerts
    - "ate onde vai o que voce consegue fazer hoje?" is faq_scope
    - "valeu demais por ter me ajudado" is gratitude
    - "junta tudo que ja planejei" is trip_summary
    - "o que eu preciso conferir antes de viajar?" is travel_checklist

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
        "max_completion_tokens": 1024,
        "reasoning_effort": "low",
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
    if intent in LOW_RISK_INTENTS:
        minimum = LOW_RISK_CONFIDENCE
    elif intent == 'step_answer' and (step in {'origin', 'destination'} or
                                      step in {'bus:origin', 'bus:destination'}):
        # Airport resolution and the explicit pre-search confirmation remain
        # authoritative after this low-impact extraction.
        minimum = 0.85
    else:
        minimum = MIN_CONFIDENCE
    if not 0 <= confidence <= 1 or confidence < minimum:
        return text
    if intent in {"unknown", "unchanged"}:
        return text
    if intent in SEMANTIC_INTENTS:
        return _semantic_message(intent, answer, text, step) or text
    if intent == 'trip_route':
        match = re.fullmatch(r'\s*(.{2,100}?)\s*->\s*(.{2,100}?)\s*', answer)
        if not match or step not in {'origin', 'destination'}:
            return text
        from .language import clean
        source = clean(text)
        origin, destination = (part.strip() for part in match.groups())
        # The model may remove harmless grammar around a place, but every
        # returned place must still occur explicitly in the traveler message.
        if clean(origin) not in source or clean(destination) not in source:
            return text
        return f'{origin} -> {destination}'
    if intent in COMMANDS:
        if intent == "itinerary_delete":
            from .language import clean
            value = clean(text)
            if "nao" in value or not re.search(
                    r"\b(?:apaga|apagar|delete|deletar|exclua|excluir)\b.*\broteiro\b", value):
                return text
        # The free hosted model occasionally repeats a harmless label in
        # `answer`. Command payloads are never executed or shown, so discard it
        # and rely only on the allowlisted intent and confidence checks.
        return COMMANDS[intent]
    if intent != "step_answer" or not answer or len(answer) > 100:
        return text
    if step == "adults" and answer not in {str(i) for i in range(1, 7)}:
        return text
    if step == "priority" and answer not in {"1", "2", "3", "4"}:
        return text
    if step == "flexibility" and answer not in {"comparar 1 dia", "manter datas"}:
        return text
    if step.startswith("itinerary:"):
        stage = step.split(":", 1)[1]
        allowed = {
            "city": {"sao paulo", "bogota", "rio de janeiro"},
            "days": {"1", "2", "3"},
            "interest": {"cultura", "natureza", "misto"},
            "pace": {"tranquilo", "equilibrado"},
            "edit": {"mudar dias", "mudar inicio", "mudar interesses", "mudar ritmo"},
        }
        if stage in allowed and answer not in allowed[stage]:
            return text
        if stage == "start" and not answer:
            return text
        if stage not in set(allowed) | {"start"}:
            return text
        return answer.strip()
    if step.startswith("discovery:"):
        stage = step.split(":", 1)[1]
        if stage == "adults" and answer not in {str(i) for i in range(1, 7)}:
            return text
        if stage == "done" and answer not in {"destino 1", "destino 2", "destino 3"}:
            return text
        if stage == "candidates":
            parts = re.split(r"\s*[,;]\s*", answer)
            if not 1 <= len(parts) <= 3 or any(not part.strip() for part in parts):
                return text
        if stage not in {"origin", "departure", "return", "adults", "budget", "candidates", "done"}:
            return text
        return answer.strip()
    if step.startswith('bus:'):
        stage = step.split(':', 1)[1]
        if stage == 'adults' and answer not in {str(i) for i in range(1, 7)}:
            return text
        if stage == 'priority' and answer not in {'1', '2', '3', '4'}:
            return text
        if stage not in {'origin', 'destination', 'departure', 'adults', 'priority', 'budget'}:
            return text
        return answer.strip()
    if step not in {"origin", "destination", "departure", "return", "adults", "priority", "budget", "flexibility"}:
        return text
    if step in {'origin', 'destination'}:
        answer = re.sub(r'^(?:aeroporto|cidade)\s+(?:de|do|da)\s+', '', answer,
                        flags=re.IGNORECASE)
    return answer.strip()
