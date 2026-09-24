# Contributing

## Language policy

Write repository documentation, new code comments, identifiers, commit subjects, and pull-request descriptions in English. Keep traveler-facing wording separate from documentation language. The current WhatsApp conversation intentionally supports Portuguese; quote actual commands and examples faithfully, with English explanations. Do not claim English chat support until it is implemented and tested.

## Changes

Keep changes focused and update the relevant documentation with behavior, validation evidence, and limitations. Keep current capabilities separate from planned features. Use synthetic examples and never commit `.env`, databases, tokens, phone numbers, or private event logs.

Run `python -m unittest discover -s tests -v` for behavior changes. Unit tests do not require the flight dependency or network access. External tests require the private configuration and must not invent fares, imply a purchase, or send messages outside the authorized test recipient.

Documentation-only changes should be checked for accuracy, valid relative links, and accidental disclosure. Preserve third-party attribution. The brand brief is a creative draft, not an approved identity or an assertion that roadmap features are already available.
