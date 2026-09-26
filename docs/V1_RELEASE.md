# Version 1 release candidate

Status: **private acceptance in progress**, not a finished public service.

The v1 scope is round-trip economy flights for adults, total-ticket budget filtering, nearby dates, explicit destination comparisons, saved preferences, native WhatsApp controls, and sourced sightseeing drafts for São Paulo and Bogotá. Bus fares, proactive price alerts, worldwide sightseeing, and whole-month search are outside this release.

## Completed engineering checks

- 108 unit/integration tests pass locally, without paid services.
- Live flight-provider queries returned complete round-trip offers.
- Two-destination budget comparison succeeded against the real provider.
- Flow navigation preserves flight criteria and allows switching between destination comparison and sightseeing.
- Generic Google Flights fallback pages are no longer treated as specific offer links.
- Multi-adult link messages explicitly require checking the passenger count on Google Flights. The upstream booking-link builder does not accept passenger counts; the displayed Atlas quote still reflects the searched count. This remains a provider limitation, not a verified checkout experience.
- Credentials and private conversations remain excluded from the public repository.

## Owner acceptance script

Use the allowed WhatsApp recipient. Record what actually happened; do not mark a scenario complete solely because its unit tests pass.

| Scenario | Messages/actions | Expected outcome | Status |
| --- | --- | --- | --- |
| Discovery | Send `menu` | Native capability list opens | Owner confirmed September 25; itinerary city list also opened |
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

Finish the owner script, record source-link/checkout discrepancies, resolve blocking defects, prepare a sanitized demonstration, and apply final standalone brand assets. The existing composite brand board is approved; it is not a finished avatar/cover export. Stable unattended operation is still limited by the local process, tunnel, and token lifetime.

A portfolio release may honestly document these limits. Do not label it production-ready or claim automatic checkout parity until verified.
