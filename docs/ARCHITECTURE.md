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
- `language.py`: supported Portuguese dates and short phrases, interpreted locally.
- `budget.py`: explicit total BRL parsing and formatting with Decimal arithmetic.
- `flights.py`: airport resolution, bounded provider execution, budget filtering, deduplication, ranking, and result presentation.
- `providers/google_flights.py`: the unofficial provider boundary.
- `interactive.py`: text/list/button/URL payloads, session-bound choice IDs, and inbound click normalization.

## Persistence and delivery

The worker releases its SQLite transaction before querying the provider. On restart, `processing` items return to the queue; `sending` items become `uncertain` to avoid repeating possibly delivered messages. This is not an exactly-once delivery guarantee. The prototype has one worker, so cancellation waits for an ongoing query to finish.

Choice IDs are stored before sending the response. The system sends one response message per processed event. An API acceptance and a delivery confirmation are separate states. Ambiguous sends are not automatically retried.

## Fare integrity

Normalization requires a complete outbound and return journey, matching airports and dates, BRL currency, and a positive price. In the pinned fli representation, the first journey's price represents the round-trip total; journey prices must not be added together.

The optional cap applies to the total for all requested adults, before sorting and limiting the display to four options. Text, lists, and link selection use the same filter. Highest-price ranking only reorders returned options and makes no claim about comfort or full-market coverage.

Budget refinement uses the existing result snapshot and retains its query time. A new search must be requested explicitly. Travel-source coverage remains limited to the provider's returned sample.

## Privacy and operational limits

Secrets stay in `.env`; conversations and offers stay in local SQLite files. Logs omit tokens, phone numbers, and message payloads. The optional fli dependency is pinned to a Git revision. Domain tests do not require network access.

This is a development HTTP server with one permitted recipient, a temporary tunnel, and local storage without application-level encryption or automatic retention expiry. Before public use, address consent, deletion and retention, limits, observability, stable hosting, and provider terms.
