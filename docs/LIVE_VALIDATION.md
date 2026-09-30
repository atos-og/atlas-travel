# External validation — September 23, 2026, Brasília time

The check executed `atlas.flights.search`, the same 55-second-bounded subprocess path used by the bot. Source: Google Flights through the fli revision pinned in requirements.txt. The sample route was CNF → GRU, departing October 23, 2026 and returning October 30, 2026, economy, lowest-price preference. These were test queries, not booked trips.

| Adults | UTC query time | Normalized offers | Displayed offers | Lowest returned total | Links among displayed offers |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-24 01:05 | 37 | 4 | BRL 683.00 | 4 |
| 2 | 2026-09-24 01:06 | 36 | 4 | BRL 1,430.00 | 4 |

Formatted messages contained 971 and 979 characters. The adapter checked dates, airports, BRL currency, complete journeys, and positive prices. Returned links used HTTPS on a Google domain.

These prices are historical observations, not guaranteed offers. The two-adult total came from a separate query rather than multiplication of the one-adult result. Fare availability can change.

This check did not validate checkout totals, baggage/refund rules, ticket issuance, or end-to-end delivery of these particular results through a real WhatsApp conversation. A later owner-driven conversation succeeded separately, as recorded in [STATUS.md](STATUS.md).

Earlier queries returned no offers. No adapter change was required for the later successful response, so the cause of the earlier empty results was not established.

## September 24, 2026 — nearby-date provider check

A one-adult CNF–GRU round-trip test queried October 23–30, October 22–29, and October 24–31, 2026 through the existing bounded provider subprocesses. All three calls succeeded and returned 114 normalized offers in aggregate. Four ranked options had links and explicit actual dates; their returned total was BRL 823.00 for October 22–29 at the time of this test. This is historical provider output, not a current-price promise. No purchase or supplier checkout verification occurred. Native client rendering for this new flow remains unconfirmed.
# Destination comparison — September 24, 2026

At 22:42 UTC, the production provider boundary was queried concurrently for CNF–GRU and CNF–REC, departing October 23 and returning October 30, 2026, one adult, with a BRL 2,500 total round-trip budget. Both destination queries returned matching offers. The lowest returned totals were BRL 786 for GRU and BRL 947 for REC. These are historical observations, not current fare promises. No WhatsApp delivery, supplier checkout, reservation, or purchase was performed during this validation.
# Browser fare-link validation — September 25, 2026

A fresh CNF–GRU round trip for October 23–30, 2026, one adult, returned BRL 772 at 10:09 UTC. The generated booking link opened Google Flights with the same airports, dates, one adult, and flights G3 1497 outbound (06:15–07:40) and G3 1482 returning (09:20–10:35). Google displayed the same BRL 772 total.

Following the airline option opened Gol's passenger-details flow with matching route, dates, and flight times. Its displayed Light fare total was BRL 771.18, BRL 0.82 below the whole-real Google/Atlas quote. This is one observed rounding difference, not exact checkout-total parity or a guarantee for other offers. The inspection stopped before entering passenger data, selecting upgrades, payment, or purchasing. The temporary browsing tabs were closed.

The owner also confirmed that the WhatsApp capability menu opened the itinerary list with São Paulo, Bogotá, and the return-to-flights option. The complete itinerary acceptance sequence is still being checked.
# Owner itinerary acceptance — September 25, 2026

The owner reported that the WhatsApp sequence São Paulo → no date yet → three days → mixed interests → relaxed pace → generate itinerary → view sources appeared to work correctly. This confirms the reported conversation path and source response, not an independent audit of each source page. Editing, exclusions, returning to flights, and the balanced pace remain separate acceptance checks.

# Hosted interpretation extension — September 27, 2026

Synthetic calls to the configured Groq-hosted `openai/gpt-oss-20b` model normalized natural itinerary phrases to two days, culture or nature, and a relaxed pace. Additional calls mapped natural requests to view itinerary sources, edit the itinerary, and reopen the generated plan. No traveler data was used. Candidate lists such as `quero comparar Guarulhos, Recife e Bogotá` are now handled locally, so this common structure does not consume hosted-model quota. These checks validate the interpretation boundary, not WhatsApp delivery.

# Provider availability audit — September 28, 2026

The sanitized provider-audit command queried CNF–GRU for October 23–30 and November 20–27, 2026, one adult. The source returned `empty` for both periods. No normalized offer, price, or booking link was available to inspect. This contrasts with earlier successful checks and confirms that the unofficial source can produce inconsistent availability without a code change. Atlas correctly avoids claiming that no flight exists.

# Expanded hosted-language audit — September 28, 2026

An initial ten-phrase synthetic evaluation passed two cases. After prompt, command-output, place-prefix, and confidence changes, a later run passed its first six cases: capabilities, origin, itinerary duration, itinerary sources, offer recommendation, and baggage. The remaining consecutive calls returned the original text, matching a free-tier burst/token-limit pattern. After the quota window reset, a focused run passed the four remaining cases: bus support, price alerts, current product scope, and gratitude. All ten fixtures therefore passed across two bounded runs. Informational intents use `0.80`, origin/destination extraction uses `0.85` plus airport resolution, and other trip changes and destructive actions retain `0.90`. No traveler data was used.

# Provider transport recovery — September 29, 2026

The project still pinned the older fli batch transport after upstream had moved to parsing the public Google Flights results page. Atlas reviewed and pinned revision `881aee5ff4321e81ea2157cb44be94ce6a21dc1b`. The production provider boundary then returned 45 normalized CNF–GRU round trips for October 23–30, 2026 for one adult, all with validated `www.google.com` deep links; the observed range was BRL 783–855. A separate two-adult call also returned 45 normalized offers and 45 validated links, with an observed range of BRL 1,565–1,710. Query times were 10:34 and 10:31 UTC, respectively. These are historical source observations, not fare promises.

The adapter now passes the searched passenger mix to the current deterministic link builder. Local regression coverage asserts that boundary. A real multi-adult Google Flights page and supplier checkout still require owner acceptance before claiming end-to-end parity.

A clean `atlas:validation` image build resolved the same pinned revision from scratch. A network-disabled container inspection reported UID `10001`, Atlas v11, and a `build_flight_booking_url` signature containing `passenger_info`. This validates packaging and the intended dependency surface; it does not validate live source availability inside a deployed container.

# Trip-organization language audit — September 29, 2026

Two additional fixed synthetic phrases mapped natural requests to the allowlisted `trip_summary` and `travel_checklist` actions. The focused Groq run passed both cases without traveler data. The model selects commands while deterministic Atlas copy builds the summary and checklist.

# Complete language audit — September 30, 2026

All thirteen fixed synthetic cases passed against the configured Groq-hosted `openai/gpt-oss-20b` model when run in documented bounded groups. The added bus-start phrase mapped to the guided bus flow, while the separate bus-capability phrase mapped to reviewed explanatory copy. The first unpaced full-corpus run reached the free-tier burst boundary after six successful cases; it was not recorded as a product interpretation failure. No traveler messages or stored conversation data were sent during this audit.

# Callback synchronization — September 29, 2026

With explicit owner approval for the named Cloudflare Quick Tunnel, Atlas updated the Meta app callback to `https://amounts-cables-empirical-scan.trycloudflare.com/webhook`. The sanitized readback reported an active `whatsapp_business_account` subscription containing the `messages` field and the exact callback URL. The public `/health` endpoint identified Atlas v11. No test message was sent during this check.

The first read immediately after Meta accepted the update briefly returned a verification mismatch; a second read returned the expected value. The callback utility now retries this non-secret readback twice with short bounded delays. Its regression test simulates stale-then-current metadata without network access.
