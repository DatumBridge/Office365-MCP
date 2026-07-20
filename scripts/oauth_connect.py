#!/usr/bin/env python3
"""Obtain Microsoft OAuth token for office365-mcp (delegated Graph access)."""

from __future__ import annotations

import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

SCOPES = [
    "openid",
    "profile",
    "offline_access",
    "User.Read",
    "Files.ReadWrite",
    "Sites.ReadWrite.All",
]


def _load_client() -> tuple[str, str, str]:
    tenant = os.environ.get("OFFICE365_TENANT_ID", "common").strip() or "common"
    client_id = os.environ.get("OFFICE365_CLIENT_ID", "").strip()
    client_secret = os.environ.get("OFFICE365_CLIENT_SECRET", "").strip()
    creds_path = Path(__file__).resolve().parent.parent / "credentials.json"
    if creds_path.exists():
        data = json.loads(creds_path.read_text())
        client_id = client_id or data.get("client_id", "")
        client_secret = client_secret or data.get("client_secret", "")
    if not client_id or not client_secret:
        print("Set OFFICE365_CLIENT_ID/SECRET or credentials.json", file=sys.stderr)
        sys.exit(1)
    return client_id, client_secret, tenant


def main() -> None:
    client_id, client_secret, tenant = _load_client()
    redirect_uri = os.environ.get(
        "OAUTH_REDIRECT_URI", "http://localhost:8765/callback"
    )
    port = urlparse(redirect_uri).port or 8765
    auth_code: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != urlparse(redirect_uri).path:
                self.send_response(404)
                self.end_headers()
                return
            qs = parse_qs(parsed.query)
            if "error" in qs:
                auth_code["error"] = qs["error"][0]
            else:
                auth_code["code"] = qs.get("code", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Auth complete. Close this window.</body></html>")

        def log_message(self, *_args):
            return

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "response_mode": "query",
    }
    auth_url = (
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?"
        + urlencode(params)
    )
    print(f"Open: {auth_url}")
    webbrowser.open(auth_url)
    HTTPServer(("localhost", port), Handler).handle_request()

    if auth_code.get("error"):
        print("OAuth error:", auth_code["error"], file=sys.stderr)
        sys.exit(1)
    code = auth_code.get("code")
    if not code:
        print("No authorization code received", file=sys.stderr)
        sys.exit(1)

    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    resp = requests.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(SCOPES),
        },
        timeout=30,
    )
    resp.raise_for_status()
    token_data = resp.json()
    out = {
        "type": "oauth",
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "scopes": SCOPES,
    }
    out_path = Path(__file__).resolve().parent.parent / "token.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
