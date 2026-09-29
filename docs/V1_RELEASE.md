# Version 1 release candidate

Status: **private acceptance in progress**, not a finished public service.

The v1 scope is round-trip economy flights for adults, total-ticket budget filtering, nearby dates, explicit destination comparisons, saved preferences, native WhatsApp controls, and sourced sightseeing drafts for São Paulo and Bogotá. A disabled-by-default one-way bus integration boundary is included for portfolio demonstration; live bus fares, proactive price alerts, worldwide sightseeing, and whole-month search are outside this release.

## Completed engineering checks

- 181 unit/integration tests pass locally, without paid services.
- GitHub Actions compiles the application and runs the offline suite on every push and pull request.
- The container image builds with the pinned provider dependency, starts as unprivileged UID `10001`, and answers its local health check.
- A synthetic hosted-language check validates the configured Groq key and GPT-OSS 20B model without using traveler data.
- Live flight-provider queries returned complete round-trip offers.
- Two-destination budget comparison succeeded against the real provider.
- Flow navigation preserves flight criteria and allows switching between destination comparison and sightseeing.
- Generic Google Flights fallback pages are no longer treated as specific offer links.
- The current provider revision encodes the searched adult count in its deterministic Google Flights deep link. Atlas still asks the traveler to verify the passenger count and final total because client rendering and checkout parity have not been accepted for multiple adults.
- Saved-trip summaries and domestic/international preparation checklists are available through typed requests, the bounded hosted interpreter, and native menus.
- The bus conversation, native controls, offer validation, and ClickBus staging adapter are implemented behind a credential gate; no live coverage or purchase-link claim is made.
- Credentials and private conversations remain excluded from the public repository.
- Replacement tunnel callbacks can be synchronized and read back through a sanitized command; WhatsApp access-token creation remains manual.
- Flight-result and price-objection controls suggest implemented follow-up features while respecting WhatsApp's native row and button limits.
- Bounded retention, rotating SQLite snapshots, aggregate status, liveness/readiness, a persistent local Compose runtime, and sanitized supplier/profile audits are implemented.
- A horizontal 2:1 Atlas cover joins the approved identity reference and WhatsApp avatar.

## Owner acceptance script

Use the allowed WhatsApp recipient. Record what actually happened; do not mark a scenario complete solely because its unit tests pass.

| Scenario | Messages/actions | Expected outcome | Status |
| --- | --- | --- | --- |
| Discovery | Send `menu` or `como vc pode me ajudar` | Readable native capability list opens | Owner confirmed September 25; revised vertical copy and abbreviated request also accepted live |
| Flight request | Send `cancelar`, then `Confins para Guarulhos, ida 23/10/2026, volta 30/10/2026, dois adultos, mais barata, sem limite` | Explicit summary with correct airports, dates, and two adults before searching | Pending |
| Fare selection | Confirm, select an offer, open its link | Correct route/dates; verify or adjust two adults; compare checkout total without buying | Pending |
| Refinement | Send `tá caro`, enter `R$ 500` | Cached-result filter; no over-budget fare offered as matching | Pending |
| Nearby dates | Choose `datas flexíveis`, ±1 day, confirm | At most three date pairs; actual dates and partial failures shown | Pending |
| Destination comparison | Send `refazer comparação`, complete criteria and choose `GRU, REC` | Confirmation, independent outcomes, and explicit adoption of one destination | Pending |
| Itinerary | São Paulo → no date → 3 days → mixed interests → relaxed pace → generate → view sources | Plan and source response appear | Owner reported success September 25; external source-page opening not separately confirmed |
| Itinerary edits | Remove a place, rebuild, then `voltar aos voos` | Exclusion respected and previous flight state preserved | Owner confirmed September 25; pace changes not separately confirmed |
| Preferences | Save, restart, inspect, explicitly reuse, then delete preferences | No implicit reuse; deletion scope accurately explained | Pending |
| Old menus | Click an older native menu after a change | Stale choice cannot change the trip | Pending |

Use future dates if repeating this script after the example dates have passed. No reservation or payment is part of acceptance.

## Remaining release gates

One one-adult fare-link inspection reached the airline passenger-details page with matching itinerary and a documented BRL 0.82 price difference. See [browser evidence](LIVE_VALIDATION.md). This does not complete multi-adult acceptance or establish parity across all sources.

Finish the owner script, record source-link/checkout discrepancies, resolve blocking defects, and prepare a sanitized demonstration. The standalone WhatsApp avatar and horizontal cover are complete; the avatar is applied to the test profile. Stable unattended operation is still limited by the current host computer, tunnel, and token lifetime; the validated container has not been deployed to an external host.

A portfolio release may honestly document these limits. Do not label it production-ready or claim automatic checkout parity until verified.
