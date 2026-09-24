# Destination comparison by budget

Send `explorar destinos`, `comparar destinos`, or `destinos por orçamento`, or choose destination exploration from the native capability menu. Atlas compares **one to three explicitly chosen destination airports** using the same origin, exact travel dates, adult count, and total BRL ticket budget.

This is a bounded comparison, not automatic worldwide destination discovery. Bus travel, hotels, airport transfers, baggage extras, and sightseeing expenses are excluded from the fare cap.

## Flow

1. Reuse any origin, dates, adults, and budget already supplied in the flight conversation; ask for missing fields.
2. Collect one to three destinations separated by commas. Recognized city aliases become airport codes. Ambiguous cities require clarification; duplicates are collapsed and the origin cannot be a destination.
3. Show the full criteria and ask for confirmation. `refazer comparação` restarts criteria collection without copying the prior trip.
4. Perform up to three concurrent provider calls, each subject to the production provider's existing 55-second subprocess timeout.
5. Display the cheapest matching returned fare per destination, ordered by total price. Preserve an existing nonstop preference, but replace duration/highest-price ordering with cheapest-first comparison.
6. Choose `destino 1` (or another displayed number) to adopt that destination and its cached offers in the main flight flow. No additional source request occurs on selection.

The comparison always uses exact dates. It does not multiply destination queries by nearby-date combinations. Selecting a destination switches the main trip to exact-date mode; this is stated in the confirmation before the comparison.

`voltar aos voos` or `menu` suspends exploration without changing the original flight criteria or result. Criteria and comparison results live in the existing private session storage. Only choosing a returned destination updates the main trip. Resetting the entire trip with `cancelar` also clears this comparison.

## Failure and fare integrity

Each destination has its own outcome: a matching offer, no returned offer meeting the criteria, or a failed query. A failure is never represented as proof of an expensive destination. Successful destinations remain usable when another query fails. No-result wording explicitly avoids claiming that cheaper fares do not exist elsewhere.

The cap covers the returned round-trip total for all requested adults. Decimal comparisons retain cent precision. The existing provider is responsible for normalizing complete routes and dates. Links, available offer details, and subsequent selection use the same cached results. Prices are not reserved or guaranteed, and no checkout or purchase occurs.

## Validation

Local tests cover candidate limits, deduplication, ambiguous airports, origin conflicts, budget ordering, nonstop filtering, malformed prices, partial failures, exact query counts, confirmation, expired dates, unchanged original trips, explicit adoption, reset, and the disabled-provider path. Live provider checks and WhatsApp acceptance are separate; see [the validation record](LIVE_VALIDATION.md).
