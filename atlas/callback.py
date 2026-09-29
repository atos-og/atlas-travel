"""Safely synchronize the Atlas webhook callback with the Meta app subscription."""

import argparse
import json
import re
from time import sleep
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .webhook import settings


OBJECT = "whatsapp_business_account"
FIELD = "messages"


def callback_url(value):
    """Return a strict HTTPS webhook URL without credentials, queries, or fragments."""
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("invalid_callback_url")
    parsed = urlsplit(value.strip())
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.port not in {None, 443}):
        raise ValueError("invalid_callback_url")
    path = parsed.path.rstrip("/")
    if not path:
        path = "/webhook"
    if path != "/webhook":
        raise ValueError("callback_path_must_be_webhook")
    return urlunsplit(("https", parsed.netloc, path, "", ""))


def _credentials(config):
    app = config.get("META_APP_ID", "")
    secret = config.get("META_APP_SECRET", "")
    version = config.get("META_GRAPH_API_VERSION", "")
    verify = config.get("WHATSAPP_VERIFY_TOKEN", "")
    if not app.isdigit() or not secret or not verify or not re.fullmatch(r"v\d+\.\d+", version):
        raise ValueError("configuration")
    return app, secret, version, verify


def subscription(config, *, opener=urlopen):
    """Return only non-secret subscription facts used by readiness checks."""
    app, secret, version, _ = _credentials(config)
    request = Request(
        f"https://graph.facebook.com/{version}/{app}/subscriptions",
        headers={"Authorization": "Bearer " + app + "|" + secret},
    )
    with opener(request, timeout=15) as response:
        payload = json.load(response)
    for item in payload.get("data", []):
        if item.get("object") == OBJECT:
            fields = [field.get("name") for field in item.get("fields", []) if isinstance(field, dict)]
            return {
                "active": item.get("active") is True,
                "callback_url": item.get("callback_url"),
                "messages": FIELD in fields,
            }
    return {"active": False, "callback_url": None, "messages": False}


def synchronize(config, url, *, opener=urlopen, sleeper=sleep):
    """Update and verify the Meta subscription without exposing credentials or raw errors."""
    try:
        expected = callback_url(url)
        app, secret, version, verify = _credentials(config)
    except ValueError as error:
        return {"ok": False, "reason": str(error)}
    body = urlencode({
        "object": OBJECT,
        "callback_url": expected,
        "verify_token": verify,
        "fields": FIELD,
    }).encode()
    request = Request(
        f"https://graph.facebook.com/{version}/{app}/subscriptions",
        data=body,
        headers={
            "Authorization": "Bearer " + app + "|" + secret,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with opener(request, timeout=20) as response:
            updated = json.load(response)
        if updated.get("success") is not True:
            return {"ok": False, "reason": "update_rejected"}
        current = subscription(config, opener=opener)
        for delay in (0.25, 0.75):
            if (current["active"] and current["messages"]
                    and current["callback_url"] == expected):
                break
            sleeper(delay)
            current = subscription(config, opener=opener)
    except HTTPError as error:
        reason = "credentials_or_access" if error.code in {400, 401, 403} else "meta_api"
        return {"ok": False, "reason": reason, "code": error.code}
    except Exception:
        return {"ok": False, "reason": "network_or_response"}
    verified = (current["active"] and current["messages"]
                and current["callback_url"] == expected)
    return {
        "ok": verified,
        "callback_url": expected,
        "active": current["active"],
        "messages": current["messages"],
        **({"reason": "verification_failed"} if not verified else {}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public HTTPS tunnel URL, with optional /webhook path.")
    args = parser.parse_args()
    result = synchronize(settings(), args.url)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
