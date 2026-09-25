# Private WhatsApp test setup

1. Create a Meta app with the WhatsApp use case and the test resources available to the account.
2. Register/verify a test recipient and confirm the example message can be sent.
3. Copy `.env.example` to `.env`. Set the access token, sending phone-number ID, Graph API version, and App Secret. Generate a random verification token distinct from the access token.
4. Set `ATLAS_ALLOWED_WHATSAPP_USER` to the permitted sender's country code and number, digits only, matching the official incoming event.
5. Run `python -m atlas.webhook` in the virtual environment. Expose port 8787 through an HTTPS tunnel and configure the `/webhook` callback with the same verification token.
6. Subscribe to the application's `messages` field and subscribe the application to the WhatsApp Business Account (WABA). URL verification alone does not prove event delivery.
7. Set `ATLAS_WHATSAPP_REPLIES_ENABLED=true`. For flight search, install `requirements.txt` and set `ATLAS_LIVE_FLIGHTS_ENABLED=true`.
8. From the allowlisted recipient, send `cancelar` (the current Portuguese restart command) to begin a new session.

Meta screens and requirements vary by account. This guide describes Atlas configuration, not a guarantee of free service or production eligibility. This stage uses the test number without registering a production phone number. Meta labels that number `Test Number` and does not allow its WhatsApp profile, display name, or photo to be edited. A branded Atlas profile requires a production WhatsApp Business Account and a phone number registered there.

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

## Read-only readiness checks

Run `python -m atlas.check` with the project environment to check required setting presence and the local server. Add `--meta` to verify API access to the configured phone-number resource. Neither command sends messages, rotates tokens, changes subscriptions, or prints credentials, phone numbers, account identifiers, or raw API errors. The command exits nonzero when a required check fails. Disabled reply/provider flags are reported separately from readiness.

A successful check does not prove public tunnel reachability, callback configuration, message delivery, available fares, or a complete user journey. Check those independently. `token_expired` means a new token is needed; `access_or_permission_denied` calls for checking the Meta account and permissions; `network_or_response` does not by itself prove that a token is invalid. Do not infer the exact cause of a permission error without inspecting the account.

Keep the existing app, scope, and recipient restriction when refreshing a development token. Complete any account confirmation in Meta itself. Temporary tunnels can expire independently of the token, so verify and update the callback after replacing one. Do not commit token values or operational tunnel URLs.

### Token lifetime

Set `META_APP_ID` in the private environment and run `python -m atlas.check --meta --token` to inspect both token and data-access expiry. Dates are UTC; `expiring_soon` means 24 hours or less remain. A still-valid token with this warning does not fail the command. An expired deadline, invalid token, wrong app, or failed inspection does. Missing expiry metadata is `unknown`; zero is `no_scheduled_expiry`, which is not a promise that Meta cannot revoke access. This command never renews credentials.

The debug request sends the token only to Meta's official Graph endpoint. Do not enable HTTP URL logging around it: the inspection endpoint requires the inspected token in its query. Atlas prints only sanitized results and never raw exceptions.

Meta documents system-user tokens as an alternative to temporary user tokens, with durations up to 60 days or no scheduled expiry. This is a separate configuration decision, not automatic renewal. Prefer a bounded lifetime and the minimum required permissions; do not broaden business access just to avoid token expiry. See [Meta's WhatsApp Cloud API collection](https://www.postman.com/meta/whatsapp-business-platform/collection/wlk6lh4/whatsapp-cloud-api).
