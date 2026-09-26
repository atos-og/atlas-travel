# Private prototype acceptance checklist

This checklist separates implemented behavior from validation still needed. It is not a public-launch approval or a claim of complete travel-source coverage.

## Implemented and checked locally

- [x] Explicit combined requests and context-preserving corrections.
- [x] Natural date expressions with confirmation and ambiguity handling.
- [x] Native passenger, preference, confirmation, offer, and URL controls.
- [x] Total-ticket budget filtering and cached-result refinement.
- [x] Bounded nearby-date search preserving the stay length.
- [x] Opt-in preference save, view, reuse, update, and deletion.
- [x] Search progress attempts tracked independently from final replies.
- [x] Signed incoming events, recipient restriction, and duplicate handling.
- [x] 127 local tests, including hosted-language diagnostics, the sightseeing flow, natural-language safeguards, readable option formatting, and native choices persisted through the queue.
- [x] Synthetic Groq health check confirmed the configured `openai/gpt-oss-20b` model without using traveler data.
- [x] Sourced sightseeing drafts for São Paulo and Bogotá, with edits and preserved flight criteria.
- [x] Native capability menu with readable sections for the implemented features.
- [x] Budget-led comparison of up to three explicit destinations, preserving the original trip until selection.
- [x] Live nearby-date provider check: three successful date pairs; see [the evidence](LIVE_VALIDATION.md).
- [x] Approved brand reference and English identity guide committed.

## Restore the WhatsApp test environment

- [x] Complete the account confirmation currently required by Meta for Developers.
- [x] Renew the expired WhatsApp access token and validate its app and scopes locally.
- [x] Update and verify the callback against the current tunnel. Temporary tunnel addresses can expire.
- [x] Confirm the app remains subscribed to the test WhatsApp account.
- [x] Confirm a new authorized inbound message produces a sent reply and renders the revised capability experience correctly.

On September 24, 2026, account access was restored, a refreshed token was validated, and the callback and WhatsApp subscription were verified. The reconnection notice subsequently received a delivery confirmation. A new owner-driven feature test remains pending. The token and tunnel remain temporary; the owner is managing credential renewals while development continues.

## Owner-driven WhatsApp acceptance

Use future dates and the allowlisted test recipient. These checks should happen after account access is restored.

1. Send a combined route/date/adult request. Verify the interpreted summary before confirming.
2. Request a destination country without a city. Verify that Atlas asks for the airport and preserves the other answers.
3. Change only the adult count. Confirm that old offers are invalidated and dates remain unchanged.
4. Request nearby dates, choose the ±1-day option, and confirm. Verify the progress notice, attempted date pairs, actual offer dates, and URL summary.
5. Set a budget below every returned fare. Verify no over-budget offer appears as an available matching selection.
6. Use a price complaint. Verify the budget question; ambiguous wording should receive a short clarification.
7. Save preferences, start another trip, and explicitly reuse them. Confirm that dates, destination, and budget were not silently restored.
8. Delete preferences and inspect them again. Confirm that deletion does not claim to erase the current conversation.
9. Click an older menu after a trip change. Verify it cannot change the current trip.
10. Open a returned provider link and compare dates, passengers, total, baggage, and fare rules. A price difference is possible; record it rather than claiming a guaranteed fare.
11. Send `menu`, choose the itinerary flow, and complete a 1–3-day draft. Verify its city, interests, pace, dates, and sources.
12. Remove a place, confirm rebuilding, and verify that it does not return. Change the pace and confirm again.
13. Use `voltar aos voos` and verify the previous flight question or results are preserved; reopen with `meu roteiro`.
14. Use `explorar destinos`, provide a budget and up to three destinations, and confirm. Verify separate failures/no-matches, price order, and that selecting `destino 1` adopts exactly that destination without another search.

## Remaining product work

| Area | Next concrete outcome |
| --- | --- |
| Source reliability | Verify supplier links and totals; establish acceptable failure and query rates. |
| Language coverage | Validate hosted interpretation on WhatsApp and expand the regression corpus from real, sanitized phrasing while preserving the free-tier fallback. |
| Brand production | Obtain or produce faithful separate avatar and cover exports; then apply them to the intended account surfaces. |
| Bus travel | Select and validate a usable source before offering bus prices or cross-mode comparisons. |
| Sightseeing | Validate the implemented flow on WhatsApp; expand coverage and verify calendars, costs, and travel times. |
| Alerts | Establish stable execution, opt-in rules, source reliability, and messaging cost before promising monitoring. |
| Broader flexible dates | Define query limits and user-approved date ranges before offering whole-month exploration. |
| Operations | Replace fragile test credentials/tunnels with an appropriate stable setup when the project is ready. |

Continue private testing before public use. The portfolio repository can be public while credentials, conversations, recordings, and operational identifiers remain private.
