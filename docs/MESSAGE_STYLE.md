# WhatsApp message style

Atlas messages should be easy to scan on a narrow phone screen. The reference conversation informed spacing and hierarchy, not promises of competitor capabilities.

- Use blank lines between ideas, not only single line breaks.
- Use WhatsApp single-asterisk bold for short headings, prices, and the next question.
- Put route, dates, passenger count, and preferences on separate lines.
- Keep each sightseeing day and each flight direction visually separate.
- End with one clear next action. Put secondary actions in the native menu or help response.
- Place qualifications next to the information they qualify. Never remove budget scope, date coverage, partial failures, or passenger-count warnings for visual simplicity.
- Use emojis sparingly. Do not add generic enthusiasm or repeat availability statements.
- Keep source URLs intact and separated by place name.

Native interactive bodies must fit the supported 1,024-character limit. The itinerary combination tests exercise all supported catalog, day-count, interest, and pace combinations against this limit. Longer flight summaries use a structured compact summary and the offer list. A URL-button body that exceeds the limit falls back to complete text with its URL instead of silently truncating fare information.

The change preserves one final response per incoming message. It does not introduce several untracked outgoing bubbles; delivery and replay behavior remain unchanged. Search progress remains the separately tracked message already implemented.

## Implemented coverage

Greeting, help, the capability menu, saved-preference summaries and actions, flight confirmation, itinerary confirmation and day-by-day plans, itinerary sources, destination-comparison confirmation/results, flight-result text, compact offer menus, and URL-button fare details.

## Visual acceptance

After deploying, inspect `meu roteiro`, `fontes do roteiro`, a flight confirmation, a long offer list, and a selected offer on WhatsApp. Confirm readable paragraphs, balanced emphasis, intact source URLs, and visible controls. Automated size checks do not replace phone-client visual review.
