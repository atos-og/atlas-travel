# Bounded natural-language interpretation

Atlas can optionally use Groq-hosted `openai/gpt-oss-20b` to understand varied Portuguese wording. GPT-OSS is an open-weight model published by OpenAI; this integration calls Groq's infrastructure and API, not OpenAI's hosted API or a ChatGPT subscription.

## Model and inference environment

| Item | Selection |
| --- | --- |
| Model | OpenAI GPT-OSS 20B |
| API model ID | `openai/gpt-oss-20b` |
| Inference environment | GroqCloud |
| API provider and credential | Groq |
| Current prototype plan | Groq Free Tier |
| Product role | Intent classification and current-step answer normalization only |

The model name identifies its publisher and weights. Groq runs those weights and serves the request. No request is sent to OpenAI by this integration.

## What the model does

For each authorized inbound text, Atlas may send the current message, current conversation step, São Paulo date, and an already supplied departure date to Groq. The model must return one strict JSON object containing:

- one intent from a fixed allowlist;
- an empty command payload or one answer for the current guided step;
- a confidence value.

Examples include mapping a varied help question to `help`, extracting `Confins` from a colloquial origin answer, mapping a price complaint to the existing budget-refinement command, normalizing a sightseeing duration, opening an existing itinerary's source view, comparing or recommending saved offers, and recognizing questions about baggage, buying, price freshness, privacy, buses, alerts, product coverage, or comfort.

The active context may be a flight question, an itinerary question, or a destination-comparison question. Itinerary values remain bounded to the two catalog cities, one to three days, the implemented interest categories, and the implemented pace options. Destination comparison remains bounded to one to three explicitly named places. Lists such as `quero comparar Guarulhos, Recife e Bogotá` are parsed locally when possible, avoiding a hosted request.

## What the model cannot do

The model does not write the WhatsApp reply, search fares, select an airport for an ambiguous city, generate an itinerary, create links, call tools, or add capabilities. Atlas discards any model-written command payload and selects only reviewed response copy through an allowlisted intent. Step answers are accepted only for the active step and must pass bounded value checks before the existing conversation validators run. A model-selected itinerary deletion is additionally rejected unless the original message explicitly asks to delete the itinerary and contains no negation.

Informational intents use a confidence floor of `0.80`; they can only show reviewed copy or explain already saved offers. Origin and destination extraction use `0.85`, followed by the airport catalog and explicit search confirmation. Other field extraction, confirmation, cancellation, preference deletion, and itinerary deletion retain `0.90` plus their existing validators.

Atlas keeps the original message when the feature is disabled, the key is missing, the API times out, the response is malformed, the intent is unknown, confidence is below its applicable threshold, or a value violates the active step. The deterministic parser therefore remains the operational fallback.

## Configuration

Keep these values only in the ignored local `.env` file or an equivalent secret store:

```env
ATLAS_NLU_ENABLED=true
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
```

The free Groq tier is suitable for private development but has request and token quotas. It is not a guarantee of permanent free pricing, production capacity, latency, or availability. Public deployment requires a privacy notice, provider-term review, quota monitoring, and a deliberate data-retention decision.

## Safe diagnostics

Run the following command to make one synthetic intent request:

```powershell
python -m atlas.check --groq
```

The check does not use a traveler message and never prints the API key or provider response body. It reports whether hosted interpretation is enabled and configured, the public model ID, and a bounded reason for invalid credentials, denied access, quota/rate limits, request/model rejection, unexpected output, or network failure. Without `--groq`, the normal health command makes no Groq request.

Run the bounded ten-case corpus when changing the prompt or model:

```powershell
python -m atlas.nlu_audit
```

All phrases are fixed project fixtures. The command does not read the conversation database. Each case can consume a free-tier request, so a quota or rate limit can produce a fallback and a failed case without affecting the deterministic bot path.
