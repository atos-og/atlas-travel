# Conversation behavior and native controls

Documentation is in English. Literal Portuguese phrases below are examples of the currently supported chat language; English equivalents are explanatory, not supported-input guarantees.

## Natural date and choice input

The flow is still guided by conversation state, but users can use alternatives to numeric scripts:

| Supported input | Meaning |
| --- | --- |
| `dia 23 de outubro desse ano` | October 23 this year |
| `23 de outubro de 2027`, `23/10/2027` | An explicit date |
| `23/10` | October 23 of the current year |
| `amanhã`, `depois de amanhã` | Tomorrow, the day after tomorrow |
| `daqui a 3 dias`, `em uma semana` | In three days, in one week |
| `7 dias depois`, `uma semana depois` | On the return step: seven days after departure |
| `somos duas pessoas`, `só eu` | Two adults, one adult |
| `prefiro a mais barata`, `sem escalas` | Lowest price, nonstop |
| `saio de Confins`, `quero ir para Bogotá` | Origin/destination phrases at the relevant step |
| `pode buscar` | Confirm the search |

Relative dates use Brasília time (UTC−3). Missing years mean the current year; past dates are rejected, never silently moved to the next year. Impossible dates, multiple alternatives, and incomplete phrases such as `dia 23` require clarification. Final confirmation always shows DD/MM/YYYY.

This is not unrestricted AI understanding. Bare weekdays and arbitrary corrections are not yet interpreted. Supported combined requests use explicit route, departure, return, passenger, preference, and budget phrases. Parsing is local and does not require a paid AI service.

## Combined requests and contextual changes

The live flow accepts, including as its first message:

`Confins para Guarulhos, ida 23/10/2027, volta 30/10/2027, dois adultos, mais barata, sem limite`

Route separators include `para`, `pra`, `->`, and `→`. Explicit `ida` and `volta` markers accept the supported natural date expressions, including a return relative to departure. Missing fields are requested one at a time; valid later fields are retained and skipped when the flow reaches them. A country or ambiguous city is never silently replaced with a specific airport.

Explicit corrections such as `somos três adultos`, `destino Bogotá`, or `ida 24/10/2027, volta 31/10/2027` preserve unrelated trip values. Trip changes invalidate previous fares and native choices and require confirmation before another search. Changing departure alone clears return so the traveler can choose the new duration. A month-only request asks for an exact date and clears the old dates; Atlas does not search the whole month or assume a seven-day stay.

Recognized invalid fields are cleared and clarified while other valid fields remain. Negated or alternative multi-field requests and repeated fields require clarification. This conservative local grammar does not understand arbitrary prose, negotiate conflicting constraints, or infer comfort from a price. The offline simulator remains separate from these live-flow capabilities.

Before a confirmed provider query, the worker sends a short progress notice. Its attempt is persisted separately from the final response. A duplicate or recovered event does not repeat the notice, and an uncertain notice send is not retried. This is not a guarantee of delivery or of a successful flight search.

## Native WhatsApp controls

- Passengers: a list of six adult-count options.
- Preferences: four ranking/filter choices; price is not treated as comfort.
- Ambiguous price complaints: a short clarification with native buttons.
- Budget: typed total or the `Sem limite` (No limit) button.
- Confirmation: `Confirmar busca` (Confirm search) and `Recomeçar` (Start over).
- Results: up to four offers plus refinement actions.
- Selected offer: a summary and `Abrir oferta` (Open offer), a native URL button using the returned Google Flights link. This is not an Atlas checkout or a guaranteed direct airline purchase link.
- `ofertas` redisplays options; typed commands remain supported.

Lists contain at most ten rows, with titles limited to 24 characters and descriptions to 72. Confirmation uses two short buttons. Interactive bodies are conservatively limited to 1,024 characters. URLs longer than the local CTA limit remain text links.

`list_reply` and `button_reply` events are handled by ID, not the submitted title. Random IDs are tied to the latest choice message in a session. Old or unknown choices do not change the trip; the bot offers current choices again. Message-ID deduplication covers clicks. Selecting an offer invalidates the previous menu; `ofertas` opens it again.

Delivery uses the official Graph API and the active test conversation. No paid template or additional service was purchased. This does not guarantee free production use.

## Total-trip budget

After the ranking preference, Atlas asks for a BRL cap covering round-trip tickets for every requested adult. Accepted examples include `até R$ 1.500,50`, `2 mil`, `1500`, and `sem limite`. Hotel costs, activities, and charges absent from the provider's fare are not included. Per-person amounts, multiple amounts, and other currencies require clarification.

The cap appears in confirmation. Decimal filtering happens before ranking and the four-offer limit. Text, lists, and link selection share the filtered set. Offers above the cap have no matching-offer purchase choice. If none fit, Atlas names the lowest returned fare for the criteria and explicitly says it exceeds the cap. This is not evidence that no cheaper fare exists elsewhere.

After searching, `orçamento`, `alterar orçamento`, or clear price complaints such as `tá caro` and `achei bem caro` open budget adjustment. The informal `carinho em` asks whether the traveler means the price is high before changing the budget step. This filters the stored result snapshot, keeps its query time, and states that no new search occurred. `buscar` refreshes the source; `sem limite` removes the filter. Changing passengers retains the total-budget concept and asks for confirmation again. Older sessions without a budget default to no cap.

## Nearby-date comparison

`datas flexíveis` opens a native choice between exact dates and a ±1-day comparison. Atlas shifts departure and return together, preserving the stay length. It queries the original pair and the preceding/following pair, omitting past departures. There are at most three calls, executed concurrently through the existing provider boundary; each production subprocess remains limited to 55 seconds. A separate confirmation is required after changing this setting.

The result identifies every attempted date pair, reports partial failures, and carries each offer's actual dates into its text, native row, and URL-button summary. Budget filtering and ranking still apply to all returned offers. This is a small nearby-date comparison, not a whole-month calendar or an exhaustive search across independent departure and return dates. Destination discovery by budget remains planned.

## Saved preferences

Preferences are opt-in. `salvar preferências` stores the current origin airport, adult count, and ranking preference only after all three are known. `minhas preferências` displays them, `usar preferências` explicitly applies them, and `apagar preferências` deletes the saved defaults for that traveler. Updating the profile requires another save command.

Dates, destination, fares, and budget are not copied into preferences. Starting another trip keeps the defaults but does not silently apply them. Reusing defaults invalidates old offers and requires confirmation; conflicting origin/destination values require clarification. The worker stores preferences separately from sessions in the existing local SQLite database, so they survive a server restart. Deleting preferences does not delete message history or the current trip; the response explains that distinction.

## Validation and references

The implementation passed 68 local unit tests covering dates, ambiguous amounts, confirmation, payloads, stale/fake IDs, persistence, signatures, rankings, and budgets. Meta accepted live `interactive.type=cta_url` and `interactive.type=list` messages for the private recipient.

References: [Meta's official list/button examples](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/messages/interactive/) (archived SDK documentation) and [CTA URL documentation](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-cta-url-messages). The CTA documentation endpoint returned HTTP 429 during research; its message format was also validated through a real API send.

## Intent safeguards

A request explicitly mentioning bus travel receives an unsupported-mode explanation and leaves the current trip unchanged. Price complaints such as `ficou mais caro` open budget refinement rather than selecting highest-price ranking. Result summaries suggest nearby dates and saving preferences only because both features are implemented.
