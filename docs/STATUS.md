# Implementation status — September 25, 2026

## WhatsApp

The owner confirmed receiving real replies from the test integration. The application and WhatsApp account subscriptions were configured. Access remains limited to the configured private recipient. A subsequent conversation reached `complete` with a successful search and 38 returned offers; recent conversation replies had delivery confirmations.

Native lists, confirmation buttons, and an offer URL button are implemented. Meta accepted real `list` and `cta_url` test messages. Acceptance alone is not proof that every client rendered the controls correctly or that every later message was delivered.

## Flights

The flow collects airports, dates, adults, preferences, an optional total budget, and confirmation. It normalizes complete round trips and displays up to four ranked offers with links. Searches run in a subprocess limited to 55 seconds without holding a SQLite transaction open.

Initial external searches returned no results. Later CNF–GRU queries for October 23–30, 2026 succeeded for one and two adults through the same subprocess used by the bot. Both produced four displayable offers with links. See [LIVE_VALIDATION.md](LIVE_VALIDATION.md). No purchase or checkout-total verification was performed.

## Conversation and budget

Supported Portuguese dates and preference/passenger phrases are parsed locally. An optional Groq-hosted GPT-OSS interpreter can map varied wording to an allowlisted command or current-step answer; confidence, state, value, and schema checks run before the deterministic conversation sees the result. External failures return the original message to local parsing. Explicit combined requests and later corrections retain unrelated details and require search confirmation. Incomplete month-only requests do not invent dates. Price objections can open budget refinement, with a short native clarification for ambiguous wording. Confirmed searches attempt a persisted, non-repeating progress notice before calling the provider. Ambiguous inputs require clarification. Native choices have session-bound IDs; old choices cannot silently change the trip.

The budget is a total BRL cap for all adults and both directions. Confirmation states its scope. Ranking, native lists, and link selection share the filter. Over-budget fares are not presented as matching offers. Refining the stored results does not trigger a new external search and is labeled accordingly.

## Validation and remaining work

The latest implementation run passed 123 local unit tests, including strict NLU schema handling, allowlisted mappings, confidence fallback, quota-preserving local parsing, overlay isolation, token expiry diagnostics, cent boundaries, removing a cap, ambiguous amounts, shared natural confirmations, explicit relative weekdays, abbreviated capability questions, readable vertical option lists, structured budget/results copy, stale interactive IDs, signed events, menus with up to ten rows, natural combined requests, and context-preserving greetings. A separate live Groq check mapped a natural help request, a colloquial origin, and a price objection while leaving an unsupported bus request unchanged. Unit tests and direct API checks do not replace WhatsApp validation. The budget feature has not yet completed a separately confirmed user-driven WhatsApp acceptance test. Combined requests, contextual edits, price clarification buttons, and search progress are validated locally with mocked delivery and providers; live acceptance of the newest budget, result copy, and hosted interpretation remains pending.

Remaining work includes supplier-page price verification, source reliability, child passengers, whole-month searches, bus fares, expanded sightseeing coverage and monitoring. There is no payment collection, ticket issuance, reservation service, or public bot deployment.

Runtime tokens and temporary tunnels can expire; this file records implementation evidence, not a live uptime guarantee.

## Nearby dates

An opt-in ±1-day comparison preserves stay length and performs at most three provider calls. It requires confirmation, labels actual offer dates, omits past departures, and reports partial failures. Unit tests cover year boundaries, query bounds, native payloads, and budget filtering. Live WhatsApp acceptance remains pending.

## Saved preferences

Explicit save/view/reuse/delete commands persist origin, adults, and ranking defaults in a separate per-user SQLite table. They never automatically apply to a new trip. Local tests cover restart persistence, traveler isolation, deletion scope, incomplete saves, and invalidated old fares. Live WhatsApp acceptance remains pending.

## Integration recovery and diagnostics

The owner is handling access configuration and token renewals while product development continues.

Account confirmation was completed by the owner. A new token was saved locally after app/scopes validation; the callback and account subscription were verified. The reconnection notice subsequently received a delivery confirmation. This does not complete acceptance of the latest conversation features.

The temporary token expired again and was renewed with the same WhatsApp permissions. Read-only checks passed after renewal, with expiry reported at 22:00 UTC on September 24, 2026. A durable credential strategy remains pending; this is not a claim of ongoing availability.

On September 25, the owner renewed the test token again. Atlas verified the token's app identity and WhatsApp scopes, replaced the expired quick-tunnel callback, subscribed the app to the test account, and passed independent local, public-tunnel, phone-number, and token checks. Meta reports this token expiring at 02:00 UTC on September 26, so another authorized inbound/outbound round trip is still required before the short-lived credential expires.

`python -m atlas.check` checks local readiness; `--meta` adds a read-only API check and `--token` inspects expiry using the optional `META_APP_ID` setting. No messages are sent and credentials are not printed. The expiry check distinguishes unknown metadata, no scheduled expiry, an upcoming deadline, and an expired deadline.

## Sightseeing and capability discovery

The expanded product suite now passes 115 local tests. Destination exploration compares up to three explicitly chosen airports against one total ticket budget, with exact dates, per-destination failures, confirmation, and explicit adoption into the original trip. See [comparison behavior](DESTINATION_DISCOVERY.md). It does not search every possible destination. Live WhatsApp acceptance remains pending.

A native `menu` exposes implemented features in spaced sections. Sightseeing runs alongside the saved flight flow, with explicit city, start date or no date, 1–3 days, interest, pace, and confirmation. The catalog contains four sourced places each for São Paulo and Bogotá. Plans group by editorial region, avoid repetitions and known recorded closures, and can be edited or have a place excluded. Empty days disclose catalog limits. Sources are accessible in the chat; live opening hours, costs, availability, and route times are not verified. Fare-link messages stay focused on the selected offer; sightseeing is suggested through the menu and help. All of this is tested locally, including persistence through the message queue; live WhatsApp acceptance of the latest copy remains pending.

The owner confirmed on September 25 that the abbreviated request `como vc pode me ajudar` opened the revised capability experience successfully after vertical option formatting replaced semicolon-separated choices. Webhook logs recorded the authorized inbound event and a sent reply outcome.
