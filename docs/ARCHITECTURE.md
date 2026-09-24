# Architecture

```text
WhatsApp → Meta → HTTPS tunnel → signed webhook → SQLite inbox
                                                       ↓ single worker
                                              conversation + session
                                                       ↓ confirmation
                                              fli subprocess (55s)
                                                       ↓
                                              normalize, filter, rank
                                                       ↓
                                              WhatsApp Graph API
```

## Responsibilities

- `webhook.py`: challenge verification, HMAC validation, request limits, and event acknowledgment after persistence.
- `messaging.py`: sender and message-age checks, deduplication, queue processing, outbound delivery, and delivery-status updates.
- `conversation.py`: channel-independent conversation states and an injectable search function.
- `trip_input.py`: conservative multi-field extraction with explicit ambiguity checks.
- `language.py`: supported Portuguese dates and short phrases, interpreted locally.
- `preferences.py`: explicit per-user defaults, stored separately from conversation sessions.
- `itinerary.py`: bounded sightseeing planner and an independent session overlay; no external API calls.
- `destinations.py`: an editorial catalog with primary-source links and selected closure rules.
- `budget.py`: explicit total BRL parsing and formatting with Decimal arithmetic.
- `flexible.py`: at most three concurrent nearby-date queries, actual-date attribution, and partial-failure reporting.
- `flights.py`: airport resolution, bounded provider execution, budget filtering, deduplication, ranking, and result presentation.
- `providers/google_flights.py`: the unofficial provider boundary.
- `interactive.py`: text/list/button/URL payloads, session-bound choice IDs, and inbound click normalization.

## Persistence and delivery

The worker releases its SQLite transaction before querying the provider. On restart, `processing` items return to the queue; `sending` items become `uncertain` to avoid repeating possibly delivered messages. This is not an exactly-once delivery guarantee. The prototype has one worker, so cancellation waits for an ongoing query to finish.

Choice IDs are stored before sending the response. The system sends one final response per processed event. Confirmed flight searches also attempt a short progress message before querying. A separate `progress` table records the attempt before network I/O and tracks its outbound ID and delivery status. A recovered processing event skips an already attempted notice. Search and outbound sends run without holding a write transaction. An API acceptance and a delivery confirmation are separate states. Ambiguous sends are not automatically retried.

## Fare integrity

Normalization requires a complete outbound and return journey, matching airports and dates, BRL currency, and a positive price. In the pinned fli representation, the first journey's price represents the round-trip total; journey prices must not be added together.

The optional cap applies to the total for all requested adults, before sorting and limiting the display to four options. Text, lists, and link selection use the same filter. Highest-price ranking only reorders returned options and makes no claim about comfort or full-market coverage.

Budget refinement uses the existing result snapshot and retains its query time. A new search must be requested explicitly. Travel-source coverage remains limited to the provider's returned sample.

## Privacy and operational limits

Secrets stay in `.env`; conversations and offers stay in local SQLite files. Logs omit tokens, phone numbers, and message payloads. The optional fli dependency is pinned to a Git revision. Domain tests do not require network access.

This is a development HTTP server with one permitted recipient, a temporary tunnel, and local storage without application-level encryption or automatic retention expiry. Before public use, address consent, deletion and retention, limits, observability, stable hosting, and provider terms.
