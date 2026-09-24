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

This is not unrestricted AI understanding. Bare weekdays, multi-field requests, and arbitrary corrections are not yet interpreted. Parsing is local and does not require a paid AI service.

## Native WhatsApp controls

- Passengers: a list of six adult-count options.
- Preferences: four ranking/filter choices; price is not treated as comfort.
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

After searching, `orçamento`, `alterar orçamento`, or `tá caro` opens budget adjustment. This filters the stored result snapshot, keeps its query time, and states that no new search occurred. `buscar` refreshes the source; `sem limite` removes the filter. Changing passengers retains the total-budget concept and asks for confirmation again. Older sessions without a budget default to no cap.

Flexible dates and destination discovery by budget are still planned. Atlas does not issue extra searches to guarantee exhaustive price coverage.

## Validation and references

The implementation passed 35 local unit tests covering dates, ambiguous amounts, confirmation, payloads, stale/fake IDs, persistence, signatures, rankings, and budgets. Meta accepted live `interactive.type=cta_url` and `interactive.type=list` messages for the private recipient.

References: [Meta's official list/button examples](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/messages/interactive/) (archived SDK documentation) and [CTA URL documentation](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-cta-url-messages). The CTA documentation endpoint returned HTTP 429 during research; its message format was also validated through a real API send.
