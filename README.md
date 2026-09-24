# Atlas

A conversational travel assistant built as a public portfolio project. The current private prototype uses Python, the official WhatsApp Cloud API, persistent conversations, and experimental flight search.

## Features

- Guided round-trip searches with explicit airports, dates, and 1–6 adults.
- Combined trip requests and explicit corrections that preserve unrelated details.
- Search progress notices and contextual price-objection clarification.
- Explicitly saved origin, adult count, and search preference, with view/reuse/delete commands.
- Opt-in nearby-date comparisons: at most three date pairs, shifting both legs by ±1 day.
- Supported Portuguese date expressions, such as `dia 23 de outubro desse ano` (October 23 this year), `amanhã` (tomorrow), and `7 dias depois` (seven days after departure).
- Native passenger, preference, and offer lists; confirmation buttons; an **Open offer** URL button, currently labeled `Abrir oferta` in the Portuguese conversation.
- Ranking by lowest price, shortest duration, nonstop service, or highest price among returned offers.
- An optional total budget in BRL for all adults and both directions, adjustable after a search.
- Up to four displayed offers with round-trip totals, local times, airlines, durations, and Google Flights links when valid data is available.
- Signed webhooks, an allowlisted recipient, a SQLite queue, deduplication, and delivery-status tracking.

**Experimental data source:** live CNF–GRU searches succeeded for one and two adults, producing ranked results and links. Earlier searches returned no results, so availability remains uncertain. Checkout prices and purchases have not been validated. See the [live validation record](docs/LIVE_VALIDATION.md).

Bus travel, sightseeing itineraries, whole-month date searches, and alerts are future milestones. The current conversation uses deterministic Portuguese phrase parsing, not an LLM or paid AI service. Ambiguous dates require clarification.

## Run locally

Python 3.12+ and Git are required. The offline simulator and unit tests have no third-party dependencies:

```sh
python -m atlas
python -m unittest discover -s tests -v
```

To run the webhook with the optional flight provider:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Fill in the private settings described in the setup guide.
.venv\Scripts\python.exe -m atlas.webhook
```

The server listens on `127.0.0.1:8787`. Meta needs a publicly reachable HTTPS callback. Outbound replies and external searches are disabled by default. Follow the [WhatsApp setup guide](docs/WHATSAPP_SETUP.md).

Example conversation, one message per step: `oi` → `Confins` → `Bogotá` → departure date → return date → `1` adult → `1` for lowest price → `sem limite` for no budget limit → `sim` to confirm. Alternatively, send `Confins para Guarulhos, ida 23/10/2027, volta 30/10/2027, dois adultos, mais barata, sem limite` as one message. The bot still requires confirmation before searching. Use future dates. Ambiguous places such as São Paulo or Colombia require a specific airport. `python -m atlas` remains an offline demonstration and does not query fares.

## Scope and limitations

The unofficial Google Flights provider may change or become unavailable. Atlas does not cover every source or guarantee the market's lowest price. Links open Google Flights, not an Atlas checkout. Baggage, refund rules, and comfort are not inferred from price. Only economy round trips for adults are supported.

The initial setup is a private test without purchased services. This does not guarantee free WhatsApp production usage. The computer, tunnel, and server must remain running. The prototype is not ready for public customer service.

## Documentation

- [Approved visual identity](docs/VISUAL_IDENTITY.md)
- [Brand and product brief — nontechnical](docs/BRAND_BRIEF.md)
- [Product plan and differentiators](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation and validation status](docs/STATUS.md)
- [Private prototype acceptance and remaining work](docs/ACCEPTANCE_CHECKLIST.md)
- [WhatsApp setup](docs/WHATSAPP_SETUP.md)
- [Conversation behavior and native controls](docs/CONVERSATION.md)
- [Security](SECURITY.md)
- [Contribution and language policy](CONTRIBUTING.md)

Repository documentation is written in English. Quoted Portuguese phrases document the current user-facing conversation; they are not English-language input support claims.

Selected provider behavior was adapted from [Fly Club](https://github.com/atos-og/flyclub), also by Atos Barros. See [third-party notices](THIRD_PARTY_NOTICES.md). Licensed under MIT.
