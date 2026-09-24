# Implementation status — September 24, 2026

## WhatsApp

The owner confirmed receiving real replies from the test integration. The application and WhatsApp account subscriptions were configured. Access remains limited to the configured private recipient. A subsequent conversation reached `complete` with a successful search and 38 returned offers; recent conversation replies had delivery confirmations.

Native lists, confirmation buttons, and an offer URL button are implemented. Meta accepted real `list` and `cta_url` test messages. Acceptance alone is not proof that every client rendered the controls correctly or that every later message was delivered.

## Flights

The flow collects airports, dates, adults, preferences, an optional total budget, and confirmation. It normalizes complete round trips and displays up to four ranked offers with links. Searches run in a subprocess limited to 55 seconds without holding a SQLite transaction open.

Initial external searches returned no results. Later CNF–GRU queries for October 23–30, 2026 succeeded for one and two adults through the same subprocess used by the bot. Both produced four displayable offers with links. See [LIVE_VALIDATION.md](LIVE_VALIDATION.md). No purchase or checkout-total verification was performed.

## Conversation and budget

Supported Portuguese dates and preference/passenger phrases are parsed locally. Explicit combined requests and later corrections retain unrelated details and require search confirmation. Incomplete month-only requests do not invent dates. Price objections can open budget refinement, with a short native clarification for ambiguous wording. Confirmed searches attempt a persisted, non-repeating progress notice before calling the provider. Ambiguous inputs require clarification. Native choices have session-bound IDs; old choices cannot silently change the trip.

The budget is a total BRL cap for all adults and both directions. Confirmation states its scope. Ranking, native lists, and link selection share the filter. Over-budget fares are not presented as matching offers. Refining the stored results does not trigger a new external search and is labeled accordingly.

## Validation and remaining work

The latest implementation run passed 73 local unit tests, including token expiry diagnostics, cent boundaries, removing a cap, ambiguous amounts, confirmation, stale interactive IDs, signed events, and menus with up to ten rows. Unit tests do not replace external validation. The budget feature has not yet completed a separately confirmed user-driven WhatsApp acceptance test. Combined requests, contextual edits, price clarification buttons, and search progress are validated locally with mocked delivery and providers; live acceptance of this latest update remains pending.

Remaining work includes supplier-page price verification, source reliability, child passengers, whole-month searches, bus fares, sightseeing itineraries and monitoring. There is no payment collection, ticket issuance, reservation service, or public bot deployment.

Runtime tokens and temporary tunnels can expire; this file records implementation evidence, not a live uptime guarantee.

## Nearby dates

An opt-in ±1-day comparison preserves stay length and performs at most three provider calls. It requires confirmation, labels actual offer dates, omits past departures, and reports partial failures. Unit tests cover year boundaries, query bounds, native payloads, and budget filtering. Live WhatsApp acceptance remains pending.

## Saved preferences

Explicit save/view/reuse/delete commands persist origin, adults, and ranking defaults in a separate per-user SQLite table. They never automatically apply to a new trip. Local tests cover restart persistence, traveler isolation, deletion scope, incomplete saves, and invalidated old fares. Live WhatsApp acceptance remains pending.

## Integration recovery and diagnostics

Account confirmation was completed by the owner. A new token was saved locally after app/scopes validation; the callback and account subscription were verified. The reconnection notice subsequently received a delivery confirmation. This does not complete acceptance of the latest conversation features.

The temporary token expired again and was renewed with the same WhatsApp permissions. Read-only checks passed after renewal, with expiry reported at 22:00 UTC on September 24, 2026. A durable credential strategy remains pending; this is not a claim of ongoing availability.

`python -m atlas.check` checks local readiness; `--meta` adds a read-only API check and `--token` inspects expiry using the optional `META_APP_ID` setting. No messages are sent and credentials are not printed. The expiry check distinguishes unknown metadata, no scheduled expiry, an upcoming deadline, and an expired deadline.
