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

The latest implementation run passed 47 local unit tests, including cent boundaries, removing a cap, ambiguous amounts, confirmation, stale interactive IDs, signed events, and menus with up to ten rows. Unit tests do not replace external validation. The budget feature has not yet completed a separately confirmed user-driven WhatsApp acceptance test. Combined requests, contextual edits, price clarification buttons, and search progress are validated locally with mocked delivery and providers; live acceptance of this latest update remains pending.

Remaining work includes supplier-page price verification, source reliability, child passengers, flexible dates, bus fares, sightseeing itineraries, saved preferences, and monitoring. There is no payment collection, ticket issuance, reservation service, or public bot deployment.

Runtime tokens and temporary tunnels can expire; this file records implementation evidence, not a live uptime guarantee.
