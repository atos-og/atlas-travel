# Deployment boundary

Atlas can run in a container on a host that supplies a public HTTPS endpoint. This packaging removes the fixed local-port assumption; it does not by itself make the private prototype a public service.

## Container

Build and run locally from the repository root:

```powershell
docker build --tag atlas-travel:local .
docker run --rm --env-file .env --publish 8787:8787 --volume atlas-work:/app/work atlas-travel:local
```

The image runs as an unprivileged user, exposes port `8787`, and checks `/health`. `ATLAS_WEBHOOK_HOST` defaults to `0.0.0.0` in the image. A hosting platform may provide its own `PORT`; that value takes precedence over `ATLAS_WEBHOOK_PORT`.

The image was built locally on September 27, 2026 with the pinned provider revision. A temporary container started as UID `10001` and returned HTTP 200 from `/health` before being removed.

## Zero-cost persistent runtime

The repository includes `compose.yaml` for the current no-cost choice: run Atlas on the owner's computer, persist state in the ignored host `work/` directory, and place the existing HTTPS tunnel in front of `127.0.0.1:8787`.

```powershell
docker compose up --build --detach
docker compose ps
docker compose logs --tail 50 atlas
```

The service restarts unless explicitly stopped, runs with a read-only container filesystem, writes only to `/app/work` and a small temporary filesystem, and drops privilege inside the image. The host computer and Docker still need to remain running. The temporary tunnel URL can still change.

Free Render and Koyeb web instances were not selected because their official documentation says free web instances cannot attach persistent disks: [Render free-service limits](https://render.com/docs/free) and [Koyeb instance limits](https://www.koyeb.com/docs/reference/instances). Railway's current free plan provides a small monthly credit rather than a guaranteed always-on allowance: [Railway free trial and free plan](https://docs.railway.com/pricing/free-trial). Oracle documents Always Free compute-compatible block storage, but creating and securing that account and VM is a separate owner-operated infrastructure step: [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm). No external host has been provisioned by this repository.

The repository now includes optional Oracle VM service and Caddy examples. Combined with a free DuckDNS subdomain, they avoid a domain purchase while preserving the current SQLite design. See the [zero-cost external hosting guide](FREE_HOSTING.md). Account creation, resource selection, hostname registration, and secret entry remain owner-operated; no cloud resource has been created.

## Required platform behavior

- Terminate HTTPS before requests reach the container. Meta requires a public HTTPS callback.
- Keep exactly one application replica. Atlas uses SQLite and one message worker; multiple replicas would not coordinate the queue safely.
- Mount persistent storage at `/app/work`. Losing that directory loses sessions, saved preferences, delivery state, and deduplication records.
- Store every credential as a platform secret or environment variable. Never copy `.env` into the image.
- Route `/webhook` to the container and allow Meta's verification challenge and signed events.
- Use `/health` as a process check. Use `/ready` to check required local settings and writable, valid SQLite storage. Neither endpoint contacts Meta, Groq, the flight source, or message delivery.
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

## Retention, backups, and status

`ATLAS_RETENTION_DAYS` defaults to 30 and is bounded from 1 to 365. The worker checks for expired local records every six hours. `ATLAS_BACKUP_COPIES` defaults to seven and is bounded from 1 to 30. The worker creates integrity-checked SQLite snapshots at startup and every 24 hours, rotating each database independently.

`ATLAS_SESSION_IDLE_MINUTES` defaults to 30 and is bounded from 1 to 1,440. It controls only whether an active trip can resume after inactivity. It does not change message-record retention or automatically apply saved preferences.

```powershell
python -m atlas.maintenance status
python -m atlas.maintenance purge --days 30
python -m atlas.maintenance backup --keep 7
```

The status command reports aggregate queue state and database health without traveler identifiers or message text. Backups under `work/backups/` remain on the same host and contain private data. Copying encrypted backups off-device and sending alerts on readiness failures remain public-launch requirements.

Stable public hosting still requires a durable Meta credential strategy, external alerting and backups, supplier reliability, and completion of the owner acceptance script. Do not scale beyond one replica or advertise public availability until the SQLite and single-recipient boundaries are replaced deliberately.
