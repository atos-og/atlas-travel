# Sightseeing itineraries

Atlas can build a small sightseeing draft without a paid AI subscription or a live travel API. The editorial catalog covers **São Paulo, Bogotá, and Rio de Janeiro**, with four places in each city. This is a bounded feature, not worldwide itinerary generation.

## Traveler flow

Send `menu` to discover the available features through a native WhatsApp list, or send `roteiro` (itinerary). A direct request such as `roteiro para Rio de Janeiro` selects the supported city explicitly. Common explicit aliases such as `RJ`, `GIG`, and `SDU` select the Rio catalog. The bot asks for:

1. City.
2. First day available for sightseeing, or `sem data` (no date yet).
3. One to three sightseeing days.
4. Culture, nature, or a mixture.
5. Relaxed pace (at most one place per day) or balanced pace (at most two).
6. Confirmation before generating the draft.

Example messages: `roteiro para Rio` → `sem data` → `3 dias` → `misto` → `equilibrado` → `montar`.

The generated plan presents each selected place with its editorial region and a short catalog description. It offers `fontes do roteiro` (sources), `ajustar roteiro` (edit), `remover passeio` (remove a place), and `voltar aos voos` (return to flights). Editing requires another confirmation. Removed places remain excluded when the plan is rebuilt; starting a new itinerary resets exclusions. `meu roteiro` reopens the generated plan. `apagar roteiro` removes the itinerary while preserving flight criteria; `cancelar` resets the entire current trip.

The flight question, criteria, and results are preserved while sightseeing is active. Dates are collected explicitly rather than treating a flight departure date as an available sightseeing day. The existing SQLite session stores the itinerary, including across process restarts. No separate user profile or external sharing is introduced.

## Planning rules

- Filter the catalog by the selected city and interest.
- Exclude places the traveler removed and known cataloged closure dates.
- Prefer the editorial region with the most remaining matching places, using catalog order to break ties.
- Select at most one or two places from that region according to pace.
- Never repeat a place across days or invent places to fill empty days.
- State explicitly when no catalog entry can fill a day.

Regions are coarse editorial groupings, not calculated walking routes. A relaxed plan is a cap on the number of places, not an accessibility or physical-effort rating. Monserrate, for example, is not automatically suitable for every traveler's mobility needs.

## Sources and freshness

The original São Paulo and Bogotá entries were reviewed on **September 24, 2026**. Rio de Janeiro entries were reviewed on **October 1, 2026**. `atlas/destinations.py` stores the original short descriptions, classifications, source links, and per-place review date. The bot provides the sources and recorded review date for the places actually selected. It does not fetch their latest information during a conversation.

| Place | Primary source | Reviewed | Recorded closure rules |
| --- | --- | --- | --- |
| MASP | [Museum visitor information](https://masp.com.br/pt-br/visite) | 2026-09-24 | Mondays; December 24, 25 and 31; January 1 |
| Pina Luz | [Pinacoteca visitor information](https://pinacoteca.org.br/visita/como-chegar/) | 2026-09-24 | Tuesdays |
| Trianon | [São Paulo municipal park information](https://prefeitura.sp.gov.br/web/meio_ambiente/w/parques/regiao_centrooeste/5773) | 2026-09-24 | Not modeled |
| Ibirapuera | [São Paulo municipal park information](https://prefeitura.sp.gov.br/meio_ambiente/w/parques/regiao_sul/14062) | 2026-09-24 | Not modeled |
| Museo Botero | [Visit Bogotá](https://visitbogota.co/es/que-hacer-en-bogota/cultura/museo-botero-en-bogota) | 2026-09-24 | Not modeled |
| Museo del Oro | [Bogotá municipal tourism guide](https://bogota.gov.co/mi-ciudad/turismo/guia-turistica-de-bogota) | 2026-09-24 | Not modeled |
| Monserrate | [Attraction visitor information](https://monserrate.co/es/preparar-visita/) | 2026-09-24 | Not modeled |
| Jardín Botánico de Bogotá | [Garden website](https://jbb.gov.co/) | 2026-09-24 | Not modeled |
| Jardim Botânico do Rio | [Federal visitor information](https://www.gov.br/jbrj/pt-br/assuntos/visitacao/horarios-e-ingressos) | 2026-10-01 | December 25; January 1 |
| Parque Lage | [EAV visitor information](https://eavparquelage.rj.gov.br/o-parque) | 2026-10-01 | Not modeled |
| Museu do Amanhã | [Museum hours and tickets](https://museudoamanha.org.br/visite/horarios-e-ingressos/) | 2026-10-01 | Wednesdays |
| CCBB Rio de Janeiro | [CCBB visitor rules](https://ccbb.com.br/rio-de-janeiro/normas-de-visitacao/) | 2026-10-01 | Tuesdays |

“Not modeled” does not mean open every day. A source review date is not the publication date of the page and does not establish live availability. All drafts ask travelers to verify opening hours, tickets, and accessibility. No ticket price, free-admission claim, availability, reservation, transport duration, or complete holiday calendar is promised. Known closures improve a draft but do not turn it into a validated booking schedule.

## Tests and next work

Tests cover every supported city/day/interest/pace combination, no duplicates, region grouping, exclusions, known closures, year boundaries, message limits, explicit confirmation, past dates, preserved flights, separate users, JSON persistence, and native selections through the SQLite message queue. The owner confirmed the São Paulo flow, source response, place removal, regeneration, and return to flights on September 25, 2026. External source-page opening, pace changes, and the revised paragraph layout still need separate visual acceptance. See V1_RELEASE.md for the remaining scenarios.

Next work includes more destinations and interests, complete and maintained opening calendars, independently verified visit costs, travel-time estimates, arrival/departure constraints, and user-specific accessibility requirements. Bus fare comparison remains a separate data-source milestone.
