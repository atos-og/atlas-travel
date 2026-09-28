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
}

COMMANDS = {
    "menu": "menu",
    "help": "menu",
    "flights": "voos",
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
    "recomendar oferta", "comparar ofertas", "duvida bagagem", "duvida compra",
    "duvida precos", "duvida privacidade", "duvida onibus", "duvida alertas",
    "duvida cobertura", "duvida conforto", "obrigado atlas",
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
        # A capability question can use the controlled FAQ. A concrete bus trip
        # stays with the local parser, which explicitly refuses flight substitution.
        return bool(re.search(r"\b(?:tambem|pesquisa|consultar|consegue|pode|oferece|tem)\b", value))
    if step.startswith("itinerary:"):
        stage = step.split(":", 1)[1]
        if stage == "city" and value in {"sao paulo", "sp", "gru", "cgh", "bogota", "bog"}:
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
    overlay_rules = ""
    if step.startswith("itinerary:"):
        overlay_rules = """
Itinerary step answers:
- city: answer must be "sao paulo" or "bogota" and only when explicitly stated
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
- itinerary: start sightseeing planning; only Sao Paulo and Bogota are supported
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

Current guided step: {step}
Current date in Sao Paulo: {today.isoformat()}
Known departure date: {departure}
{overlay_rules}

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
12. Distinguish these common requests carefully:
    - "which option should I choose" is offer_recommendation; asking for differences is offer_comparison
    - asking where sightseeing information came from is itinerary_sources
    - asking whether a fare includes luggage is faq_baggage
    - asking whether Atlas supports buses is faq_bus
    - asking for a future notification when a price falls is faq_alerts
    - asking what Atlas supports today is faq_scope
    - thanking Atlas is gratitude

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
            "city": {"sao paulo", "bogota"},
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
    if step not in {"origin", "destination", "departure", "return", "adults", "priority", "budget", "flexibility"}:
        return text
    return answer.strip()
