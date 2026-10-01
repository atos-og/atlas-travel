# Validated natural-language interpretation

Atlas can optionally use Groq-hosted `openai/gpt-oss-20b` to understand varied Portuguese wording. GPT-OSS is an open-weight model published by OpenAI; this integration calls Groq's infrastructure and API, not OpenAI's hosted API or a ChatGPT subscription.

## Model and inference environment

| Item | Selection |
| --- | --- |
| Model | OpenAI GPT-OSS 20B |
| API model ID | `openai/gpt-oss-20b` |
| Inference environment | GroqCloud |
| API provider and credential | Groq |
| Current prototype plan | Groq Free Tier |
| Product role | Intent classification and grounded travel-criteria extraction |

The model name identifies its publisher and weights. Groq runs those weights and serves the request. No request is sent to OpenAI by this integration.

## What the model does

For each authorized inbound text that local parsing cannot confidently handle, Atlas may send the current message, current conversation step, São Paulo date, and a short set of current travel criteria to Groq. The model must return one strict JSON object containing:

- one intent from a fixed allowlist;
- an empty command payload, one answer for the current guided step, or a compact object of explicitly stated travel fields;
- a confidence value.

The structured request types are:

- flight: origin, destination, departure, return, adults, ranking priority, and total ticket budget;
- bus: origin, destination, departure, adults, ranking priority, and total ticket budget;
- itinerary: supported city, start date or no-date choice, day count, interest, and pace.

The traveler can supply any subset in one message. Atlas stores only validated fields and asks for the first missing or invalid answer. A complete set reaches a readable confirmation; it never starts a supplier search by itself.

The model also maps varied help questions and corrections to implemented actions, recognizes product questions, distinguishes unsupported requests from unclear ones, and routes ordinary social messages to short reviewed copy. Examples include a price complaint, sightseeing source request, saved-offer comparison, trip summary, preparation checklist, and questions about baggage, buying, price freshness, privacy, buses, alerts, product coverage, identity, operation, sources, or comfort.

The active context may be a flight question, bus question, itinerary question, or destination-comparison question. Bus values remain bounded to cities or terminals, one exact future date, one to six adults, four reviewed rankings, and one total budget. Itinerary values remain bounded to São Paulo, Bogotá, and Rio de Janeiro, one to three days, the implemented interest categories, and the implemented pace options. Destination comparison remains bounded to one to three explicitly named places. Clear commands, dates, numbers, airport names, and candidate lists are parsed locally when possible, avoiding unnecessary hosted requests.

## What the model cannot do

The model does not write the operational WhatsApp reply, search fares, select an airport for an ambiguous city, choose an unstated date, generate itinerary places, create links, call tools, or add capabilities. Atlas discards model-written command copy and selects reviewed responses through an allowlisted intent. Structured values reject unknown keys, nested data, empty values, oversized values, unsupported choices, and places that are not grounded in the current message. Passenger, ranking, budget, and date fields require matching cues in that message before domain validation. A model-selected itinerary deletion is additionally rejected unless the original message explicitly asks to delete the itinerary and contains no negation.

Informational intents use a confidence floor of `0.80`; they can only show reviewed copy or explain already saved offers. Origin and destination extraction use `0.85`, followed by the airport catalog and explicit search confirmation. Other field extraction, confirmation, cancellation, preference deletion, and itinerary deletion retain `0.90` plus their existing validators.

Atlas keeps the original message when the feature is disabled, the key is missing, the API times out, the response is malformed, the intent is unknown, confidence is below its applicable threshold, or structured data fails grounding and value checks. The deterministic parser therefore remains the operational fallback. GPT-OSS runs with low reasoning effort and a 1,024-token output limit because Atlas needs a short classification object rather than a long generated answer.

The prompt contains no phone number, WhatsApp or Meta credential, Groq key, quoted fare, booking link, full conversation history, or stored message transcript. Current criteria are included only to help the model understand which field the traveler is correcting; the model is instructed not to copy those criteria into a structured result unless the current message repeats or changes them.

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

Run the bounded seventeen-case corpus when changing the prompt or model:

```powershell
python -m atlas.nlu_audit
python -m atlas.nlu_audit flight_fields itinerary_fields bus_fields
python -m atlas.nlu_audit bus bus_search alerts scope thanks trip_summary travel_checklist
```

All phrases are fixed project fixtures. The command does not read the conversation database. Structured cases verify both the request type and the exact set of extracted fields; Python separately validates their values. Each case can consume a free-tier request, so the full corpus can reach a burst or token limit. Pass one or more case labels to run a smaller group after the quota window resets. A quota fallback can fail an audit case without affecting the deterministic bot path.
