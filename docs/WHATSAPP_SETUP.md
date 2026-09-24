# Private WhatsApp test setup

1. Create a Meta app with the WhatsApp use case and the test resources available to the account.
2. Register/verify a test recipient and confirm the example message can be sent.
3. Copy `.env.example` to `.env`. Set the access token, sending phone-number ID, Graph API version, and App Secret. Generate a random verification token distinct from the access token.
4. Set `ATLAS_ALLOWED_WHATSAPP_USER` to the permitted sender's country code and number, digits only, matching the official incoming event.
5. Run `python -m atlas.webhook` in the virtual environment. Expose port 8787 through an HTTPS tunnel and configure the `/webhook` callback with the same verification token.
6. Subscribe to the application's `messages` field and subscribe the application to the WhatsApp Business Account (WABA). URL verification alone does not prove event delivery.
7. Set `ATLAS_WHATSAPP_REPLIES_ENABLED=true`. For flight search, install `requirements.txt` and set `ATLAS_LIVE_FLIGHTS_ENABLED=true`.
8. From the allowlisted recipient, send `cancelar` (the current Portuguese restart command) to begin a new session.

Meta screens and requirements vary by account. This guide describes Atlas configuration, not a guarantee of free service or production eligibility. This stage uses the test number without registering a production phone number.

## Diagnosis

- `/health` identifies the local server version; it does not validate external sources.
- A verified callback means the GET challenge and verification token succeeded.
- An accepted signed POST means App Secret signature verification succeeded.
- Local `sent` means the API accepted the message; delivery is confirmed separately through status events.
- For `failed`, inspect the local error code. Country/account restrictions are not fixed by repeated sends.
- If replies stop, check the process, tunnel, token validity, subscriptions, allowlisted sender, and queue.

Temporary tunnels can expire or change their URL after restart. Update the callback when required. Keep one `atlas.webhook` instance using the virtual environment's Python. The server prevents port reuse. Settings are loaded for each event; changing `.env` does not require restarting the server solely to load a new token. Verify token validity with Meta without printing it.

## Local data

`work/conversations.db` contains messages, responses, sender IDs, offers, and state. `work/webhooks.db` contains event hashes. Both databases and `.env` are excluded from Git. Uncertain sends are not retried automatically. Use `cancelar` to recover a conversation.
