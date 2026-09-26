# Bounded natural-language interpretation

Atlas can optionally use Groq-hosted `openai/gpt-oss-20b` to understand varied Portuguese wording. GPT-OSS is an open-weight model published by OpenAI; this integration calls Groq's infrastructure and API, not OpenAI's hosted API or a ChatGPT subscription.

## What the model does

For each authorized inbound text, Atlas may send the current message, current conversation step, São Paulo date, and an already supplied departure date to Groq. The model must return one strict JSON object containing:

- one intent from a fixed allowlist;
- an empty command payload or one answer for the current guided step;
- a confidence value.

Examples include mapping a varied help question to `help`, extracting `Confins` from a colloquial origin answer, or mapping a price complaint to the existing budget-refinement command.

## What the model cannot do

The model does not write the WhatsApp reply, search fares, select an airport for an ambiguous city, generate an itinerary, create links, call tools, or add capabilities. Command intents must have an empty answer. Step answers are accepted only for the active step and must pass bounded value checks before the existing conversation validators run.

Atlas keeps the original message when the feature is disabled, the key is missing, the API times out, the response is malformed, the intent is unknown, confidence is below `0.90`, or a value violates the active step. The deterministic parser therefore remains the operational fallback.

## Configuration

Keep these values only in the ignored local `.env` file or an equivalent secret store:

```env
ATLAS_NLU_ENABLED=true
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
```

The free Groq tier is suitable for private development but has request and token quotas. It is not a guarantee of permanent free pricing, production capacity, latency, or availability. Public deployment requires a privacy notice, provider-term review, quota monitoring, and a deliberate data-retention decision.
