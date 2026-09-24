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
