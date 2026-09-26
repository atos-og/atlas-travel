# Product plan

Atlas helps people search and refine travel options through WhatsApp, compare alternatives, and open provider links. Its source is public for portfolio purposes; operation starts as a private, no-purchased-services experiment. Telegram remains a possible alternative channel.

## Milestones

1. **Private conversation — implemented:** webhooks, replies, persistent sessions, deduplication, and an allowlisted recipient.
2. **Flight search — in validation:** guided inputs, rankings, links, and failure handling are implemented. Live searches returned offers for one and two adults. The owner completed a search through WhatsApp. Supplier-page availability and checkout totals still need validation.
3. **Budget and refinement — partially implemented:** a total BRL cap, post-search adjustments, explicit over-budget messages, and consistent offer selection are implemented. An opt-in ±1-day comparison now queries up to three date pairs while preserving stay length. Comparing up to three explicit destination airports against one fare budget is now implemented. Whole-month searches and open-ended destination suggestions remain planned. Estimates must be distinguished from verified fares.
4. **Flights and buses:** select a viable bus data source before promising coverage. Compare total cost, duration, stops, terminals, and supplier-reported travel class. Include terminal transfers when reliable information is available.
5. **Personalized sightseeing itineraries — partially implemented:** an independent flow builds sourced 1–3-day drafts for São Paulo and Bogotá, with an explicit start date, interest, pace, regional grouping, edits, and exclusions. Broader coverage, spending preferences, complete opening calendars, travel times, and verified availability remain planned. See [itinerary rules](ITINERARIES.md).
6. **Preferences and alerts — partially implemented:** users can explicitly save, view, reuse, update, and delete origin/adult-count/ranking defaults. Monitoring requires a stable source and a cost assessment for proactive messaging.

## Conversation improvements — September 25, 2026

Implemented locally: explicit combined requests, contextual trip edits, price-objection clarification with native buttons, persisted search progress notices, context-preserving greetings, shared colloquial confirmations, and explicit relative weekdays. Offer details include duration in the URL-button message; long result summaries retain travel dates and query time. The newest conversation changes still need live WhatsApp acceptance.

An optional hosted NLU layer now translates varied wording into a strict, allowlisted intent. Deterministic parsing remains the fallback. Next: validate natural phrases through WhatsApp, broaden coverage using concrete regression examples, evaluate offer artwork and carousel feasibility against the test account and cost constraint, and extend nearby dates only after validating source reliability and query limits. Branded visuals must remain readable without images and must not invent baggage or fare guarantees. Capability suggestions should appear only when their underlying feature works.

## Intended differentiators

Cross-mode comparisons; budget-led searches; personalized itineraries; user-controlled preferences; and contextual suggestions that reveal useful capabilities. A native `menu` lists available capabilities, including the implemented itinerary flow. Fare-link messages focus on the selected offer and its next action to keep them readable. When prices are high, Atlas can refine the budget or compare nearby dates; alternative transport still needs a provider.

Planned capabilities must never be presented as already available. The help response distinguishes current features from future work. No audited competitor feature comparison has been completed, so these are product directions rather than verified exclusivity claims.

## Portfolio value

The project demonstrates real integrations, conversation state, fare normalization, webhook security, bounded language-model use, testing, and honest failure handling. The hosted model translates requests into validated criteria only. Prices and links still come from travel sources, and final product copy remains controlled by the application.

## Language

Documentation, contribution guidance, and commit descriptions use English. The current traveler conversation is in Portuguese. Future localization should be deliberate and tested; translating documentation does not change supported chat inputs.
