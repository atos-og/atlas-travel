# Implementation status — September 30, 2026

## WhatsApp

The owner confirmed receiving real replies from the test integration. The application and WhatsApp account subscriptions were configured. Access remains limited to the configured private recipient. A subsequent conversation reached `complete` with a successful search and 38 returned offers; recent conversation replies had delivery confirmations.

Native lists, confirmation buttons, and an offer URL button are implemented. Meta accepted real `list` and `cta_url` test messages. Acceptance alone is not proof that every client rendered the controls correctly or that every later message was delivered.

## Flights

The flow collects airports, dates, adults, preferences, an optional total budget, and confirmation. It normalizes complete round trips and displays up to four ranked offers with links. Searches run in a subprocess limited to 55 seconds without holding a SQLite transaction open.

The older pinned provider transport became unreliable after Google blocked its batch endpoint. Atlas now pins reviewed fli revision `881aee5ff4321e81ea2157cb44be94ce6a21dc1b`, which reads the public results page. On September 29, bounded CNF–GRU audits for October 23–30 returned 45 normalized offers with 45 Google deep links for one adult and again for two adults. The two-adult link builder receives the searched passenger mix. See [LIVE_VALIDATION.md](LIVE_VALIDATION.md). No purchase or multi-adult checkout-total verification was performed.

## Conversation and budget

Supported Portuguese dates and preference/passenger phrases are parsed locally. An optional Groq-hosted GPT-OSS interpreter can map varied wording to an allowlisted command or current-step answer across flight, bus, itinerary, and destination-comparison flows; confidence, state, value, and schema checks run before the deterministic conversation sees the result. It also recognizes controlled questions about saved offers, baggage, buying, price freshness, privacy, bus support, alerts, product coverage, and comfort limits. External failures return the original message to local parsing. Explicit combined requests and later corrections retain unrelated details and require search confirmation. Incomplete month-only requests do not invent dates. Price objections can open budget refinement, with a short native clarification for ambiguous wording. Confirmed searches attempt a persisted, non-repeating progress notice before calling the provider. Ambiguous inputs require clarification. Native choices have session-bound IDs; old choices cannot silently change the trip.

The budget is a total BRL cap for all adults and both directions. Confirmation states its scope. Ranking, native lists, and link selection share the filter. Over-budget fares are not presented as matching offers. Refining the stored results does not trigger a new external search and is labeled accordingly.

## Validation and remaining work

The latest implementation run passed 183 local unit tests, including retention, backup rotation, readiness, sanitized flight, bus, and profile boundaries, strict NLU schema handling, confidence tiers, quota-preserving local parsing, bounded bus, itinerary, and destination answers, trip summaries and checklists, contextual feature suggestions, passenger-aware booking links, token expiry diagnostics, cent boundaries, readable option lists, stale interactive IDs, signed events, natural combined requests, and context-preserving greetings. A GitHub Actions workflow compiles the application and runs the offline suite on pushes and pull requests. On September 30, all thirteen synthetic language cases passed in bounded groups against the configured Groq-hosted `openai/gpt-oss-20b` model, including the new bus-start distinction. An unpaced full-corpus run reached the free-tier burst boundary after six successes, confirming why the documented audit uses small groups. Unit tests and direct API checks do not replace WhatsApp validation. The budget feature has not yet completed a separately confirmed user-driven WhatsApp acceptance test. Combined requests, contextual edits, price clarification buttons, search progress, summaries, and checklists are validated locally; live acceptance of the newest organization and bus copy remains pending.

Remaining product scope includes source reliability, child passengers, whole-month searches, ClickBus partner activation, cross-mode comparison, and expanded sightseeing coverage. There is no payment collection, ticket issuance, reservation service, or public bot deployment.

Runtime tokens and temporary tunnels can expire; this file records implementation evidence, not a live uptime guarantee.

## Deployment packaging

The webhook can bind to a constrained host and a platform-assigned port. On September 29, a clean Docker build fetched the exact new flight-provider revision and completed successfully. A network-disabled container inspection confirmed Atlas v11, unprivileged UID `10001`, and the passenger-aware provider API. `/app/work` remains reserved for persistent state. Single-replica hosting, durable storage, HTTPS, secrets, and release checks are documented in [DEPLOYMENT.md](DEPLOYMENT.md).

The zero-cost Compose runtime persists the ignored host `work/` directory, restarts the process, uses a read-only container filesystem, and keeps the public port bound to localhost for the tunnel. Render and Koyeb free web instances were rejected for this SQLite design because their free tiers do not support persistent volumes. Optional Oracle Always Free VM, DuckDNS, Caddy, and systemd instructions are now prepared without creating an external account or resource. No external host has been provisioned. `/ready` checks local configuration and storage, while aggregate status, 30-day retention, and seven-copy daily SQLite rotation are implemented. Off-device encrypted backups and active alerts remain public-launch work.

The v12 image was rebuilt after the bus integration. An offline container check ran as UID `10001` and confirmed that the ClickBus boundary returns the controlled unauthorized state without a credential.

## Bus travel boundary

Atlas now has an independent one-way bus flow for one to six adults, exact dates, total budget, and ranking by price, duration, connections, or operator-declared service class. The official ClickBus partner adapter resolves places and normalizes trip results but is disabled by default. ClickBus requires partner onboarding and its documented search response does not supply a verified public fare handoff URL. Atlas therefore exposes neither live bus prices nor a purchase button until staging credentials and a handoff contract are accepted. ANTT open data was reviewed as a reference source but does not provide live commercial availability or booking links.

## Nearby dates

An opt-in ±1-day comparison preserves stay length and performs at most three provider calls. It requires confirmation, labels actual offer dates, omits past departures, and reports partial failures. Unit tests cover year boundaries, query bounds, native payloads, and budget filtering. Live WhatsApp acceptance remains pending.

## Saved preferences

Explicit save/view/reuse/delete commands persist origin, adults, and ranking defaults in a separate per-user SQLite table. They never automatically apply to a new trip. Local tests cover restart persistence, traveler isolation, deletion scope, incomplete saves, and invalidated old fares. Live WhatsApp acceptance remains pending.

## Integration recovery and diagnostics

The owner is handling access configuration and token renewals while product development continues.

Account confirmation was completed by the owner. A new token was saved locally after app/scopes validation; the callback and account subscription were verified. The reconnection notice subsequently received a delivery confirmation. This does not complete acceptance of the latest conversation features.

The temporary token expired again and was renewed with the same WhatsApp permissions. Read-only checks passed after renewal, with expiry reported at 22:00 UTC on September 24, 2026. A durable credential strategy remains pending; this is not a claim of ongoing availability.

On September 25, the owner renewed the test token again. Atlas verified the token's app identity and WhatsApp scopes, replaced the expired quick-tunnel callback, subscribed the app to the test account, and passed independent local, public-tunnel, phone-number, and token checks. Meta reports this token expiring at 02:00 UTC on September 26, so another authorized inbound/outbound round trip is still required before the short-lived credential expires.

On September 27, Atlas replaced another expired quick tunnel and updated the existing Meta app webhook subscription through the Graph API. Meta verified the new callback, reported the `whatsapp_business_account` subscription as active, and retained the `messages` field. The owner remains responsible for creating and renewing the short-lived WhatsApp access token; this recovery did not generate or rotate that credential.

The successful recovery path is now available as `python -m atlas.callback <HTTPS tunnel URL>`. The command validates the URL, updates the existing app subscription, and reads back the active callback and `messages` field without printing secrets. A live run against the current private Meta app succeeded.

On September 29, after explicit owner authorization for the named Quick Tunnel, the callback was synchronized to `https://amounts-cables-empirical-scan.trycloudflare.com/webhook`. Meta reported the subscription active with `messages`. The first immediate read returned a false verification failure while a subsequent read returned the exact saved URL; the synchronizer now performs two short bounded rereads to tolerate this observed Graph API consistency delay.

Later on September 29, the local webhook restarted on `atlas-conversation-v12`. The expired Quick Tunnel was replaced, and the new callback was synchronized and read back as active with the `messages` field. The saved WhatsApp token had already expired (`190/463`), so no owner-message acceptance was attempted or claimed for this runtime. The temporary callback hostname remains operational data and is intentionally omitted from the public documentation.

`python -m atlas.check` checks local readiness; `--meta` adds a read-only Meta API check, `--token` inspects expiry using the optional `META_APP_ID` setting, and `--groq` validates hosted interpretation with synthetic text. No WhatsApp messages are sent and credentials are not printed. The expiry check distinguishes unknown metadata, no scheduled expiry, an upcoming deadline, and an expired deadline. The Groq check distinguishes configuration, credentials, access, quota/rate limits, request/model rejection, output validation, and network failures without returning raw provider text.

## Sightseeing and capability discovery

Destination exploration compares up to three explicitly chosen airports against one total ticket budget, with exact dates, per-destination failures, confirmation, and explicit adoption into the original trip. Natural candidate lists can include a short request prefix and a final `e`. See [comparison behavior](DESTINATION_DISCOVERY.md). It does not search every possible destination. Live WhatsApp acceptance remains pending.

A native `menu` exposes implemented features in spaced sections. Sightseeing runs alongside the saved flight flow, with explicit city, start date or no date, 1–3 days, interest, pace, and confirmation. The catalog contains four sourced places each for São Paulo and Bogotá. Plans group by editorial region, avoid repetitions and known recorded closures, and can be edited or have a place excluded. Empty days disclose catalog limits. Sources are accessible in the chat; live opening hours, costs, availability, and route times are not verified. Fare-link messages stay focused on the selected offer; sightseeing is suggested through the menu and help. All of this is tested locally, including persistence through the message queue; live WhatsApp acceptance of the latest copy remains pending.

The native menu also exposes `resumo da viagem` and `checklist da viagem`. The summary reads only the current saved session and does not query a source. The checklist distinguishes implemented Brazilian airport codes from international destinations, directs official-rule checks to official sources, and makes no entry-eligibility decision. Both actions have deterministic final copy; Groq can only select their allowlisted commands.

The owner confirmed on September 25 that the abbreviated request `como vc pode me ajudar` opened the revised capability experience successfully after vertical option formatting replaced semicolon-separated choices. Webhook logs recorded the authorized inbound event and a sent reply outcome.
