"""Development webhook with opt-in private WhatsApp replies."""

import hashlib
import hmac
import json
import os
import sqlite3
import socket
import threading
from .messaging import ingest, worker
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
MAX_BODY = 256 * 1024


def settings():
    values = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    for key in ("WHATSAPP_VERIFY_TOKEN", "META_APP_SECRET", "META_APP_ID", "WHATSAPP_ACCESS_TOKEN",
                "WHATSAPP_PHONE_NUMBER_ID", "META_GRAPH_API_VERSION",
                "ATLAS_ALLOWED_WHATSAPP_USER", "ATLAS_WHATSAPP_REPLIES_ENABLED", "ATLAS_LIVE_FLIGHTS_ENABLED"):
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def verify_challenge(query, token):
    params = parse_qs(query)
    if not token or params.get("hub.mode") != ["subscribe"]:
        return None
    supplied = params.get("hub.verify_token", [])
    challenge = params.get("hub.challenge", [])
    if len(supplied) != 1 or len(challenge) != 1:
        return None
    if not hmac.compare_digest(supplied[0].encode(), token.encode()):
        return None
    return challenge[0]


def valid_signature(body, signature, secret):
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.encode(), signature.encode())


def record_receipt(body, database):
    """Persist only a payload hash and time; no phone numbers or message text."""
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database, timeout=5)) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS receipts "
            "(digest TEXT PRIMARY KEY, received_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        cursor = connection.execute(
            "INSERT OR IGNORE INTO receipts(digest) VALUES (?)",
            (hashlib.sha256(body).hexdigest(),),
        )
        connection.commit()
        return cursor.rowcount == 1


class Handler(BaseHTTPRequestHandler):
    server_version = "AtlasDev"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Default access logs expose verification tokens in query strings.
        pass

    def respond(self, status, message):
        body = message.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/health":
            return self.respond(200, "atlas-conversation-v7")
        if url.path != "/webhook":
            return self.respond(404, "not found")
        challenge = verify_challenge(url.query, settings().get("WHATSAPP_VERIFY_TOKEN", ""))
        if challenge is None:
            return self.respond(403, "verification rejected")
        print("Webhook verification accepted.", flush=True)
        self.respond(200, challenge)

    def do_POST(self):
        if urlsplit(self.path).path != "/webhook":
            return self.respond(404, "not found")
        secret = settings().get("META_APP_SECRET", "")
        if not secret:
            return self.respond(503, "receiver configuration incomplete")
        if self.headers.get("Transfer-Encoding"):
            return self.respond(400, "unsupported encoding")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond(400, "invalid length")
        if not 0 < length <= MAX_BODY:
            return self.respond(413, "invalid body size")
        try:
            body = self.rfile.read(length)
        except TimeoutError:
            return self.respond(408, "request timeout")
        if len(body) != length:
            return self.respond(400, "incomplete body")
        if not valid_signature(body, self.headers.get("X-Hub-Signature-256", ""), secret):
            return self.respond(403, "signature rejected")
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, "invalid json")
        if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
            return self.respond(400, "unsupported event")
        try:
            queued = ingest(payload, settings(), ROOT / "work" / "conversations.db")
            fresh = record_receipt(body, ROOT / "work" / "webhooks.db")
        except (sqlite3.Error, OSError):
            return self.respond(503, "storage unavailable")
        except (TypeError, AttributeError, KeyError):
            return self.respond(400, "invalid event structure")
        if queued:
            print(f"Authorized messages queued: {queued}", flush=True)
        print("Signed webhook received." if fresh else "Duplicate webhook received.", flush=True)
        self.respond(200, "EVENT_RECEIVED")


class ExclusiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    if not settings().get("WHATSAPP_VERIFY_TOKEN"):
        raise SystemExit("Set WHATSAPP_VERIFY_TOKEN in the local .env file first.")
    server = ExclusiveHTTPServer(("127.0.0.1", 8787), Handler)
    stop = threading.Event()
    thread = threading.Thread(target=worker, args=(settings, ROOT / "work" / "conversations.db", stop), daemon=True)
    thread.start()
    print("Atlas private webhook: http://127.0.0.1:8787", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        thread.join(timeout=25)
        server.server_close()


if __name__ == "__main__":
    main()
