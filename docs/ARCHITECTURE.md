# Architecture

```text
WhatsApp → Meta → HTTPS tunnel → signed webhook → SQLite inbox
                                                       ↓ single worker
                              optional GroqCloud / GPT-OSS 20B translation
                                                       ↓ validation/fallback
                                              conversation + session
                                                       ↓ confirmation
                         fli subprocess (55s) or gated ClickBus partner search
                                                       ↓
                                              normalize, filter, rank
                                                       ↓
                                              WhatsApp Graph API
```

## Responsibilities

- `webhook.py`: challenge verification, HMAC validation, request limits, and event acknowledgment after persistence.
- `callback.py`: strict callback URL validation and verified Meta app-subscription synchronization without access-token rotation.
- `messaging.py`: sender and message-age checks, deduplication, queue processing, outbound delivery, and delivery-status updates.
- `conversation.py`: channel-independent conversation states and an injectable search function.
- `trip_input.py`: conservative multi-field extraction with explicit ambiguity checks.
- `language.py`: supported Portuguese dates and short phrases, interpreted locally.
- `nlu.py`: optional Groq request, strict intent schema, grounded multi-field extraction, confidence gate, allowlisted command mapping, and fail-open return to the original message.
- `nlu_audit.py`: seventeen fixed synthetic phrases for measuring command and structured-request interpretation without traveler data.
- `preferences.py`: explicit per-user defaults, stored separately from conversation sessions.
- `itinerary.py`: bounded sightseeing planner and an independent session overlay; no external API calls.
- `destinations.py`: an editorial catalog with primary-source links and selected closure rules.
- `discovery.py`: bounded destination comparisons using a separate session overlay, with explicit adoption of a selected fare snapshot.
- `buses.py`: independent one-way bus overlay, source-neutral offer validation, total-budget filtering, and declared-class ranking.
- `budget.py`: explicit total BRL parsing and formatting with Decimal arithmetic.
- `flexible.py`: at most three concurrent nearby-date queries, actual-date attribution, and partial-failure reporting.
- `flights.py`: airport resolution, bounded provider execution, budget filtering, deduplication, ranking, and result presentation.
- `providers/google_flights.py`: the unofficial provider boundary.
- `providers/clickbus.py`: a disabled-by-default official partner boundary for place and trip search; it performs no booking or payment action.
- `provider_audit.py`: sanitized live-source evidence containing no booking URLs.
- `interactive.py`: text/list/button/URL payloads, session-bound choice IDs, and inbound click normalization.
- `maintenance.py`: retention, integrity-checked rotating backups, and aggregate local status.
- `profile.py`: read-only Meta business-profile branding checks with identifiers removed from output.

## Hosted model boundary

Atlas uses `openai/gpt-oss-20b`, an open-weight model published by OpenAI, through the GroqCloud API. Groq supplies the hosted inference environment and API key. This is separate from OpenAI's hosted API and from ChatGPT subscriptions.

The model is an optional interpreter inside the application boundary. It returns a strict intent object. For richer messages, the object can contain explicit flight, bus, or itinerary fields encoded as structured data. Python verifies that places and supporting cues occur in the current message, rejects unknown keys, enforces confidence and value bounds, resolves airports, parses dates and money, and requires confirmation before a search. Informational intents use `0.80` because their output only selects reviewed copy. Origin and destination text use `0.85`. Structured requests, other trip changes, and destructive actions retain `0.90`.

## Persistence and delivery

The worker releases its SQLite transaction before querying the provider. On restart, `processing` items return to the queue; `sending` items become `uncertain` to avoid repeating possibly delivered messages. This is not an exactly-once delivery guarantee. The prototype has one worker, so cancellation waits for an ongoing query to finish.

Choice IDs are stored before sending the response. The system sends one final response per processed event. Confirmed flight searches also attempt a short progress message before querying. A separate `progress` table records the attempt before network I/O and tracks its outbound ID and delivery status. A recovered processing event skips an already attempted notice. Search and outbound sends run without holding a write transaction. An API acceptance and a delivery confirmation are separate states. Ambiguous sends are not automatically retried.

## Fare integrity

Normalization requires a complete outbound and return journey, matching airports and dates, BRL currency, and a positive price. In the pinned fli representation, the first journey's price represents the round-trip total; journey prices must not be added together. The reviewed provider revision reads the public Google Flights results page rather than the older blocked batch endpoint. Atlas passes the searched passenger mix into the deterministic deep-link builder and still validates the resulting HTTPS host, path, query token, and length before exposing it.

The optional cap applies to the total for all requested adults, before sorting and limiting the display to four options. Text, lists, and link selection use the same filter. Highest-price ranking only reorders returned options and makes no claim about comfort or full-market coverage.

Budget refinement uses the existing result snapshot and retains its query time. A new search must be requested explicitly. Travel-source coverage remains limited to the provider's returned sample.

## Privacy and operational limits

Secrets stay in `.env`; conversations and offers stay in local SQLite files. Runtime logs are ignored by Git and omit tokens, phone numbers, and message payloads. Callback synchronization sends the App ID credential, verification token, and public callback only to Meta's Graph endpoint and prints sanitized status. When NLU is enabled, the current message, conversation step, current date, and a short set of current travel criteria are sent to Groq. Phone numbers, Meta credentials, fare results, full session history, and the Groq key are not placed in the prompt. The optional fli dependency is pinned to a Git revision. Domain tests do not require network access.

Records expire after a bounded local retention period. SQLite online backups run daily and keep a bounded number of copies. `/health` checks only the process; `/ready` additionally checks required local configuration and writable, valid storage without calling Meta, Groq, or the fare source. `python -m atlas.maintenance status` emits only counts and storage state.

This is a development HTTP server with one permitted recipient, a temporary tunnel, and local storage without application-level encryption or automatic retention expiry. Before public use, address consent, deletion and retention, limits, observability, stable hosting, and provider terms.

The webhook binds to `127.0.0.1:8787` by default. A hosted process can select `0.0.0.0` and a bounded port through environment settings. The container image preserves the one-process, one-worker design and therefore must run as a single replica with persistent `/app/work` storage. See [DEPLOYMENT.md](DEPLOYMENT.md).
