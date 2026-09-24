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
- [x] 63 local tests; GitHub Actions passed for commit `b2cea9c`.
- [x] Live nearby-date provider check: three successful date pairs; see [the evidence](LIVE_VALIDATION.md).
- [x] Approved brand reference and English identity guide committed.

## Restore the WhatsApp test environment

- [ ] Complete the account confirmation currently required by Meta for Developers.
- [ ] Renew the expired WhatsApp access token and validate its app and scopes locally.
- [ ] Update and verify the callback against the current tunnel. Temporary tunnel addresses can expire.
- [ ] Confirm the app remains subscribed to the test WhatsApp account.
- [ ] Confirm a new authorized inbound message produces a delivered reply.

The local server has been reloaded with the implemented features. As of the latest check on September 24, 2026, account confirmation and the expired token block external acceptance. The previous callback's tunnel expired; starting a replacement tunnel alone does not update Meta's callback.

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

## Remaining product work

| Area | Next concrete outcome |
| --- | --- |
| Source reliability | Verify supplier links and totals; establish acceptable failure and query rates. |
| Language coverage | Expand a regression corpus; evaluate a language model only against the zero-cost/private-use constraint. |
| Brand production | Obtain or produce faithful separate avatar and cover exports; then apply them to the intended account surfaces. |
| Bus travel | Select and validate a usable source before offering bus prices or cross-mode comparisons. |
| Sightseeing | Build sourced destination content and itinerary rules for dates, interests, pace, and geographic proximity. |
| Alerts | Establish stable execution, opt-in rules, source reliability, and messaging cost before promising monitoring. |
| Broader flexible dates | Define query limits and user-approved date ranges before offering whole-month exploration. |
| Operations | Replace fragile test credentials/tunnels with an appropriate stable setup when the project is ready. |

Continue private testing before public use. The portfolio repository can be public while credentials, conversations, recordings, and operational identifiers remain private.
