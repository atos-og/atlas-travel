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
- [x] 160 local tests, including hosted-language diagnostics, retention, rotating backups, readiness, provider/profile audits, guided itinerary and destination interpretation, callback synchronization boundaries, contextual feature suggestions, and native choices persisted through the queue.
- [x] Synthetic Groq health check confirmed the configured `openai/gpt-oss-20b` model without using traveler data.
- [x] Sourced sightseeing drafts for São Paulo and Bogotá, with edits and preserved flight criteria.
- [x] Native capability menu with readable sections for the implemented features.
- [x] Budget-led comparison of up to three explicit destinations, preserving the original trip until selection.
- [x] Live nearby-date provider check: three successful date pairs; see [the evidence](LIVE_VALIDATION.md).
- [x] Approved brand reference, standalone WhatsApp avatar, horizontal cover, and English identity guide committed; the avatar is applied to the test profile.
- [x] Container image built locally, started as an unprivileged user, and passed its health check.
- [x] Zero-cost Compose runtime, local readiness, aggregate status, 30-day retention, and bounded daily SQLite snapshots implemented.

## Restore the WhatsApp test environment

- [x] Complete the account confirmation currently required by Meta for Developers.
- [x] Renew the expired WhatsApp access token and validate its app and scopes locally.
- [x] Update and verify the callback against the current tunnel. Temporary tunnel addresses can expire.
- [x] Confirm the app remains subscribed to the test WhatsApp account.
- [x] Synchronize and verify a replacement tunnel callback without rotating the WhatsApp access token.
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
15. During an itinerary, use natural phrases for the day count, interest, pace, viewing sources, editing, and reopening the plan. Confirm that unsupported values are rejected and that the generated copy still comes from Atlas rather than the model.
16. After a flight result, open the native list and verify that nearby dates and sightseeing appear without exceeding ten rows. Trigger an ambiguous price objection and verify the three buttons for budget, nearby dates, and current offers.

## Remaining product work

| Area | Next concrete outcome |
| --- | --- |
| Source reliability | Repeat supplier audits over time; the September 28 sample returned no offers for two date pairs despite earlier successful results. |
| Language coverage | Validate hosted interpretation on WhatsApp and expand the regression corpus from real, sanitized phrasing while preserving the free-tier fallback. |
| Brand production | Apply the completed avatar and Atlas display name to the eventual production number, then run the sanitized profile check. |
| Bus travel | Select and validate a usable source before offering bus prices or cross-mode comparisons. |
| Sightseeing | Validate the implemented flow on WhatsApp; expand coverage and verify calendars, costs, and travel times. |
| Alerts | Establish stable execution, opt-in rules, source reliability, and messaging cost before promising monitoring. |
| Broader flexible dates | Define query limits and user-approved date ranges before offering whole-month exploration. |
| Operations | Keep the zero-cost local Compose runtime during private testing; later choose an external persistent host, durable Meta credential, off-device encrypted backup, and alerts. |

Continue private testing before public use. The portfolio repository can be public while credentials, conversations, recordings, and operational identifiers remain private.
