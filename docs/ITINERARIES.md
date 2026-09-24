# Sightseeing itineraries

Atlas can build a small sightseeing draft without an AI subscription or a live travel API. The initial editorial catalog covers **São Paulo and Bogotá**, with four places in each city. This is a bounded feature, not worldwide itinerary generation.

## Traveler flow

Send `menu` to discover the available features through a native WhatsApp list, or send `roteiro` (itinerary). A direct request such as `roteiro para Bogotá` selects the supported city explicitly. The bot asks for:

1. City.
2. First day available for sightseeing, or `sem data` (no date yet).
3. One to three sightseeing days.
4. Culture, nature, or a mixture.
5. Relaxed pace (at most one place per day) or balanced pace (at most two).
6. Confirmation before generating the draft.

Example messages: `roteiro para São Paulo` → `sem data` → `3 dias` → `misto` → `equilibrado` → `montar`.

The generated plan offers `fontes do roteiro` (sources), `ajustar roteiro` (edit), `remover passeio` (remove a place), and `voltar aos voos` (return to flights). Editing requires another confirmation. Removed places remain excluded when the plan is rebuilt; starting a new itinerary resets exclusions. `meu roteiro` reopens the generated plan. `apagar roteiro` removes the itinerary while preserving flight criteria; `cancelar` resets the entire current trip.

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

The sources below were reviewed on **September 24, 2026**. `atlas/destinations.py` stores the original short descriptions, classifications, and source links. The bot provides the sources for the places actually selected. It does not fetch their latest information during a conversation.

| Place | Primary source | Recorded closure rules |
| --- | --- | --- |
| MASP | [Museum visitor information](https://masp.com.br/pt-br/visite) | Mondays; December 24, 25 and 31; January 1 |
| Pina Luz | [Pinacoteca visitor information](https://pinacoteca.org.br/visita/como-chegar/) | Tuesdays |
| Trianon | [São Paulo municipal park information](https://prefeitura.sp.gov.br/web/meio_ambiente/w/parques/regiao_centrooeste/5773) | Not modeled |
| Ibirapuera | [São Paulo municipal park information](https://prefeitura.sp.gov.br/meio_ambiente/w/parques/regiao_sul/14062) | Not modeled |
| Museo Botero | [Visit Bogotá](https://visitbogota.co/es/que-hacer-en-bogota/cultura/museo-botero-en-bogota) | Not modeled |
| Museo del Oro | [Bogotá municipal tourism guide](https://bogota.gov.co/mi-ciudad/turismo/guia-turistica-de-bogota) | Not modeled |
| Monserrate | [Attraction visitor information](https://monserrate.co/es/preparar-visita/) | Not modeled |
| Jardín Botánico | [Garden website](https://jbb.gov.co/) | Not modeled |

“Not modeled” does not mean open every day. A source review date is not the publication date of the page and does not establish live availability. All drafts ask travelers to verify opening hours, tickets, and accessibility. No ticket price, free-admission claim, availability, reservation, transport duration, or complete holiday calendar is promised. Known closures improve a draft but do not turn it into a validated booking schedule.

## Tests and next work

Tests cover every supported city/day/interest/pace combination, no duplicates, region grouping, exclusions, known closures, year boundaries, message limits, explicit confirmation, past dates, preserved flights, separate users, JSON persistence, and native selections through the SQLite message queue. Live WhatsApp acceptance of the new itinerary flow remains pending.

Next work includes more destinations and interests, complete and maintained opening calendars, independently verified visit costs, travel-time estimates, arrival/departure constraints, and user-specific accessibility requirements. Bus fare comparison remains a separate data-source milestone.
