# Optional zero-cost external hosting

Atlas does not need a purchased domain. Permanent operation means a server, public HTTPS callback, persistent storage, and valid service credentials remain available while the owner's computer is off.

The practical zero-cost path for the current SQLite, single-worker design is an Oracle Cloud Infrastructure Always Free VM with an Always Free boot volume. A free DuckDNS subdomain can point to the VM, and Caddy can terminate HTTPS and renew its certificate automatically. The Atlas container remains bound to `127.0.0.1:8787`; only Caddy exposes ports 80 and 443.

This is optional infrastructure for private testing. The public GitHub portfolio does not require it.

## Why this path fits

- Oracle documents Always Free compute and block-volume allowances that do not expire while the account and selected resources remain eligible.
- A normal VM keeps the single worker running and preserves the existing SQLite databases on disk.
- DuckDNS provides a free subdomain, so no domain purchase is required.
- Caddy provides automatic HTTPS for a public hostname and proxies the exact webhook path to Atlas.

Capacity for an Always Free shape is not guaranteed in every Oracle region. Account creation may require identity and payment-method verification even when only free resources are used. The owner must select resources carrying the `Always Free-eligible` label and should configure account budget alerts. Atlas cannot create or verify the owner's cloud account from repository code.

## Prepared repository files

- `compose.yaml` runs one unprivileged Atlas container and persists `work/` on the host.
- `deploy/oracle/atlas-compose.service` starts the Compose project after the VM reboots.
- `deploy/oracle/Caddyfile.example` terminates HTTPS and forwards requests to the local Atlas port.
- `/health` checks the process; `/ready` also checks configuration and writable SQLite storage.

These files contain no token, phone number, hostname, IP address, or traveler data.

## Owner-operated setup

1. Create an Oracle Cloud account and choose the home region carefully. Confirm that the selected VM shape and boot volume are explicitly marked Always Free-eligible.
2. Create one Ubuntu VM with a reserved public IP. Open inbound TCP 22 only from the owner's address when possible, and TCP 80 and 443 publicly for HTTPS certificate issuance and Meta webhooks.
3. Create a free DuckDNS subdomain and point it to the reserved VM IP.
4. Install Git, Docker Engine with the Compose plugin, and Caddy from their official repositories.
5. Clone the public Atlas repository into `/opt/atlas`. Create `/opt/atlas/.env` locally on the VM with permissions `600`; never upload the development `.env` through Git.
6. Copy `deploy/oracle/atlas-compose.service` to `/etc/systemd/system/atlas-compose.service`. Verify that `/usr/bin/docker` is the actual Docker path, then enable and start it.
7. Replace the placeholder in `deploy/oracle/Caddyfile.example` with the DuckDNS hostname, copy it to `/etc/caddy/Caddyfile`, validate it, and reload Caddy.
8. Confirm `https://<hostname>/health` and `https://<hostname>/ready` before changing Meta.
9. Synchronize `https://<hostname>/webhook` with `python -m atlas.callback https://<hostname>` from a trusted environment.
10. Run the read-only checks and one owner-driven WhatsApp round trip. Keep replies allowlisted.

Example service commands on the VM:

```bash
sudo install -m 0644 deploy/oracle/atlas-compose.service /etc/systemd/system/atlas-compose.service
sudo systemctl daemon-reload
sudo systemctl enable --now atlas-compose.service
sudo systemctl status atlas-compose.service
```

Example Caddy preparation after replacing the hostname:

```bash
sudo install -m 0644 deploy/oracle/Caddyfile.example /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Cost and durability boundaries

“Always Free” is a provider offer, not a guarantee that every requested shape is available or that terms never change. Check the account's cost dashboard and current official limits before and after provisioning. Do not select a paid shape to work around a capacity error.

The VM solves the current host-computer and temporary-tunnel problem. It does not solve an expiring Meta token, Groq free-tier limits, flight-source changes, ClickBus partner access, off-device encrypted backups, or public-user support. The current product remains private and allowlisted.

Cloud Run was not selected for this version even though it has a usage-based free tier: its container filesystem is not persistent, and scale-to-zero does not fit the background SQLite queue without an external database and worker redesign. Free Render web services also cannot attach persistent disks. The VM path avoids that architecture migration for the portfolio prototype.
