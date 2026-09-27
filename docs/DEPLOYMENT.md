# Deployment boundary

Atlas can run in a container on a host that supplies a public HTTPS endpoint. This packaging removes the fixed local-port assumption; it does not by itself make the private prototype a public service.

## Container

Build and run locally from the repository root:

```powershell
docker build --tag atlas-travel:local .
docker run --rm --env-file .env --publish 8787:8787 --volume atlas-work:/app/work atlas-travel:local
```

The image runs as an unprivileged user, exposes port `8787`, and checks `/health`. `ATLAS_WEBHOOK_HOST` defaults to `0.0.0.0` in the image. A hosting platform may provide its own `PORT`; that value takes precedence over `ATLAS_WEBHOOK_PORT`.

## Required platform behavior

- Terminate HTTPS before requests reach the container. Meta requires a public HTTPS callback.
- Keep exactly one application replica. Atlas uses SQLite and one message worker; multiple replicas would not coordinate the queue safely.
- Mount persistent storage at `/app/work`. Losing that directory loses sessions, saved preferences, delivery state, and deduplication records.
- Store every credential as a platform secret or environment variable. Never copy `.env` into the image.
- Route `/webhook` to the container and allow Meta's verification challenge and signed events.
- Use `/health` only as a process check. It does not validate Meta, Groq, the flight source, storage durability, or message delivery.
- Preserve graceful shutdown time so the worker can finish its current operation. A provider search can run for up to 55 seconds.

## Configuration

Use the same private settings described in [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md). For a hosted deployment, set `ATLAS_WEBHOOK_HOST=0.0.0.0`. Use `PORT` when the platform assigns it; otherwise set `ATLAS_WEBHOOK_PORT` explicitly.

The current allowlist permits one traveler. Keep `ATLAS_WHATSAPP_REPLIES_ENABLED=false` until the callback, number, recipient, storage, and token have been validated. Enabling replies does not remove the allowlist.

## Release checks

1. Run the offline test suite.
2. Build the image without injecting credentials.
3. Start the image with private runtime secrets and persistent storage.
4. Confirm `/health` through the platform's public URL.
5. Synchronize the exact callback with `python -m atlas.callback <HTTPS base URL>` from a trusted environment.
6. Run `python -m atlas.check --meta --token --groq` from a trusted environment.
7. Send one authorized inbound message and verify both the reply and delivery event.

Stable hosting still requires a durable Meta credential strategy, retention rules, monitoring, backups, supplier validation, and completion of the owner acceptance script. Do not scale beyond one replica or advertise public availability until the SQLite and single-recipient boundaries are replaced deliberately.
