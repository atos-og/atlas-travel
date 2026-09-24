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
