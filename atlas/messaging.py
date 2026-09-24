"""Private test conversation queue and official WhatsApp text delivery."""

import json
import re
import sqlite3
import time
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .conversation import Conversation, Session
from .interactive import incoming, payload_for, text_payload, ACTION_PREFIX


@contextmanager
def database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS inbox (
              id TEXT PRIMARY KEY, sender TEXT NOT NULL, body TEXT NOT NULL,
              timestamp INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
              reply TEXT, outbound_id TEXT, delivery TEXT, error_code TEXT);
            CREATE TABLE IF NOT EXISTS sessions (
              sender TEXT PRIMARY KEY, step TEXT NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS progress (
              inbox_id TEXT PRIMARY KEY, state TEXT NOT NULL,
              outbound_id TEXT, delivery TEXT, error_code TEXT);
        """)
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def phone(value):
    return re.sub(r"[+\s()-]", "", value)


def ingest(payload, config, path, now=None):
    now = int(time.time() if now is None else now)
    allowed = phone(config.get("ATLAS_ALLOWED_WHATSAPP_USER", ""))
    if not allowed or not config.get("WHATSAPP_PHONE_NUMBER_ID"):
        return 0
    count = 0
    with database(path) as db:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue
                value = change.get("value", {})
                if value.get("metadata", {}).get("phone_number_id") != config["WHATSAPP_PHONE_NUMBER_ID"]:
                    continue
                for status in value.get("statuses", []):
                    errors = status.get("errors") or []
                    code = str(errors[0].get("code", "")) if errors else None
                    db.execute("UPDATE inbox SET delivery=?, error_code=? WHERE outbound_id=?",
                               (status.get("status"), code, status.get("id")))
                    db.execute("UPDATE progress SET delivery=?, error_code=? WHERE outbound_id=?",
                               (status.get("status"), code, status.get("id")))
                for message in value.get("messages", []):
                    if message.get("from") != allowed:
                        continue
                    mid = message.get("id")
                    text = incoming(message)
                    try:
                        timestamp = int(message.get("timestamp", 0))
                    except (ValueError, TypeError):
                        continue
                    if not 0 <= now - timestamp < 23 * 3600:
                        continue
                    if not isinstance(text, str):
                        continue
                    if not isinstance(mid, str) or not mid or not text.strip() or len(text) > 2000:
                        continue
                    count += db.execute(
                        "INSERT OR IGNORE INTO inbox(id,sender,body,timestamp) VALUES (?,?,?,?)",
                        (mid, allowed, text, timestamp),
                    ).rowcount
    return count


def send_text(config, recipient, text):
    return send_message(config, recipient, text_payload(text))


def send_message(config, recipient, payload):
    version = config.get("META_GRAPH_API_VERSION", "")
    number_id = config.get("WHATSAPP_PHONE_NUMBER_ID", "")
    token = config.get("WHATSAPP_ACCESS_TOKEN", "")
    if not re.fullmatch(r"v\d+\.\d+", version) or not number_id.isdigit() or not token:
        return "failed", None, "configuration"
    body = json.dumps({"messaging_product": "whatsapp", "recipient_type": "individual",
                       "to": recipient, **payload}).encode()
    request = Request(f"https://graph.facebook.com/{version}/{number_id}/messages", data=body,
                      headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
        mid = result.get("messages", [{}])[0].get("id")
        return ("sent", mid, None) if mid else ("uncertain", None, "missing_message_id")
    except HTTPError as error:
        try:
            code = str(json.load(error).get("error", {}).get("code", error.code))
        except (ValueError, AttributeError):
            code = str(error.code)
        return "failed", None, code
    except Exception:
        # Never retry a possibly delivered message automatically.
        return "uncertain", None, "transport_or_response"


def process_one(config, path, sender=None, now=None):
    if config.get("ATLAS_WHATSAPP_REPLIES_ENABLED") != "true":
        return False
    allowed = phone(config.get("ATLAS_ALLOWED_WHATSAPP_USER", ""))
    if not allowed or not config.get("WHATSAPP_ACCESS_TOKEN"):
        return False
    now = int(time.time() if now is None else now)
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT id,sender,body,timestamp FROM inbox WHERE state='pending' ORDER BY timestamp,rowid LIMIT 1").fetchone()
        if row is None:
            return False
        mid, recipient, body, timestamp = row
        if recipient != allowed or not 0 <= now - timestamp < 23 * 3600:
            db.execute("UPDATE inbox SET state='skipped' WHERE id=?", (mid,))
            return True
        saved = db.execute("SELECT step,data FROM sessions WHERE sender=?", (recipient,)).fetchone()
        db.execute("UPDATE inbox SET state='processing' WHERE id=?", (mid,))
    from .flights import search
    def progress(text):
        # Persist the attempt before I/O so a crash cannot repeat the notice.
        with database(path) as db:
            fresh = db.execute('INSERT OR IGNORE INTO progress(inbox_id,state) VALUES (?,?)',
                               (mid, 'attempted')).rowcount
        if not fresh:
            return
        try:
            state, outbound, error = sender(config, recipient, text) if sender else send_text(config, recipient, text)
        except Exception:
            state, outbound, error = 'uncertain', None, 'sender_exception'
        with database(path) as db:
            db.execute('UPDATE progress SET state=?,outbound_id=?,error_code=? WHERE inbox_id=?',
                       (state, outbound, error, mid))

    from .preferences import Preferences
    conversation = Conversation(search if config.get("ATLAS_LIVE_FLIGHTS_ENABLED") == "true" else None,
                                on_search=progress, preferences=Preferences(path))
    if saved:
        conversation.sessions[recipient] = Session(saved[0], json.loads(saved[1]))
    try:
        if body.startswith(ACTION_PREFIX):
            current = conversation.sessions.get(recipient, Session())
            command = current.values.get('_choices', {}).get(body[len(ACTION_PREFIX):])
            reply = conversation.reply(recipient, command) if command else 'Essa opção ficou antiga. Escolha novamente nas opções atuais ou digite cancelar.'
        else:
            reply = conversation.reply(recipient, body)
    except Exception:
        reply = "Não consegui concluir essa etapa. Digite cancelar para recomeçar."
    with database(path) as db:
        session = conversation.sessions.get(recipient, Session())
        payload = payload_for(session, reply) if config.get('ATLAS_LIVE_FLIGHTS_ENABLED') == 'true' else text_payload(reply)
        db.execute("INSERT OR REPLACE INTO sessions(sender,step,data) VALUES (?,?,?)",
                   (recipient, session.step, json.dumps(session.values)))
        db.execute("UPDATE inbox SET state='sending',reply=? WHERE id=?", (reply, mid))
    try:
        state, outbound, error = sender(config, recipient, reply) if sender else send_message(config, recipient, payload)
    except Exception:
        state, outbound, error = "uncertain", None, "sender_exception"
    with database(path) as db:
        db.execute("UPDATE inbox SET state=?,outbound_id=?,error_code=? WHERE id=?",
                   (state, outbound, error, mid))
    print("WhatsApp reply outcome: " + state, flush=True)
    return True


def worker(config_loader, path, stop):
    # A crash during an HTTP send leaves an ambiguous result; do not resend.
    with database(path) as db:
        db.execute("UPDATE inbox SET state='uncertain' WHERE state='sending'")
        db.execute("UPDATE inbox SET state='pending' WHERE state='processing'")
    while not stop.is_set():
        try:
            if not process_one(config_loader(), path):
                stop.wait(1)
        except Exception:
            print("WhatsApp worker failure; details withheld.", flush=True)
            stop.wait(5)
