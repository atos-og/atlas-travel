# Bus travel

Atlas now contains a provider-neutral, one-way bus conversation and a disabled-by-default ClickBus partner adapter. This is portfolio-ready integration code, not a claim that the public bot currently returns live bus fares.

## Traveler flow

The traveler can type `ônibus`, use the native capability menu, or make a concrete request such as `quero ir de BH pra São Paulo de ônibus`. Atlas collects:

1. origin city or terminal;
2. destination city or terminal;
3. an exact future departure date;
4. one to six adults;
5. lowest price, shortest duration, fewest connections, or highest declared comfort class;
6. an optional total one-way budget for all adults; and
7. explicit confirmation before calling the source.

The bus state is an independent session overlay. Entering it does not overwrite an unfinished flight search, itinerary, or destination comparison. `voos` returns to the saved flight state. A successful bus result can also appear in the trip summary.

Results show no more than four validated options. Total price, local departure and arrival labels, duration, connection count, available seats, operator, and service class all come from the source response. The comfort ordering uses only the operator-reported class: `leito-cama`, `leito`, `semi-leito`, `executivo`, then `convencional`. It does not infer operator quality, punctuality, seat condition, safety, or included amenities.

## Source decision

The selected target is the official ClickBus partner API. Its documented flow provides place resolution and real-time trip availability, price, discount, seat count, schedule, operator, type, duration, and service class. ClickBus documents more than 250 connected operators and 300,000 routes. Access is not self-service: staging credentials are issued during partner onboarding through a ClickBus account representative.

Atlas uses only the search boundary. It does not block seats, create orders, collect passenger identity, or process payment. The documented partner search does not provide a public fare handoff URL, so Atlas intentionally leaves purchase links empty until ClickBus supplies an approved handoff contract. A generic or fabricated public URL would not identify the quoted trip and is therefore not exposed.

ANTT open data was also reviewed. It is useful for official route, schedule, operator, and historical or operational context. It does not provide live commercial availability, current discounts, or a booking handoff, so it cannot power Atlas fare results by itself.

## Activation

The public repository contains placeholders only:

```dotenv
ATLAS_LIVE_BUSES_ENABLED=false
CLICKBUS_ACCESS_TOKEN=
CLICKBUS_API_BASE_URL=https://platform-bff-partners.stg.clickbus.net/partners/api
```

After partner onboarding, save the staging token locally, validate the API contract, and only then set `ATLAS_LIVE_BUSES_ENABLED=true`. Readiness fails when the feature is enabled without a token. Diagnostics report only whether the source is enabled and configured; they never print the token.

The adapter restricts its base URL to the documented ClickBus staging host. A production hostname should be added only after ClickBus provides and validates it during onboarding. The access token, production hostname, rate limits, commercial terms, and purchase flow must never be guessed.

## Failure behavior

- Without credentials, the menu explains that live bus pricing requires partner access.
- Authorization failures, invalid places, empty results, and source outages have distinct controlled messages.
- No failure path estimates a price or silently substitutes a flight search.
- Results with invalid prices, times, duration, operator, class, or insufficient seats are discarded.
- The source price is multiplied by the requested adult count before Atlas applies the total budget.

## Remaining acceptance

1. Obtain explicit ClickBus staging access and confirm the current authentication contract.
2. Run documented staging routes and compare normalized values with the raw response.
3. Confirm city ambiguity behavior and terminal selection with real place results.
4. Confirm whether the commercial agreement provides an approved checkout or affiliate handoff URL.
5. Run the complete native WhatsApp flow with the allowlisted test user.
6. Record sanitized evidence without tokens, traveler identifiers, trip IDs, or booking links.

Until those checks pass, bus travel is an implemented, tested integration boundary with an honest unavailable state rather than a live product claim.
