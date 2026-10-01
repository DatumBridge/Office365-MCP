"""OAuth 2.0 routes for Microsoft identity (OneDrive / SharePoint delegated access)."""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

import requests
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

_oauth_tokens: dict[str, dict] = {}

DEFAULT_SCOPES = [
    "openid",
    "profile",
    "offline_access",
    "User.Read",
    "Files.Read.All",
    "Sites.Read.All",
]


def _oauth_ui_enabled() -> bool:
    return os.environ.get("OFFICE365_ENABLE_OAUTH_UI", "0").strip() in (
        "1",
        "true",
        "yes",
    )


def _tenant_id() -> str:
    return os.environ.get("OFFICE365_TENANT_ID", "common").strip() or "common"


def _get_oauth_config() -> tuple[str, str]:
    client_id = os.environ.get("OFFICE365_CLIENT_ID", "").strip()
    client_secret = os.environ.get("OFFICE365_CLIENT_SECRET", "").strip()
    creds_path = os.environ.get("OFFICE365_OAUTH_CREDENTIALS", "").strip()
    if not creds_path:
        creds_path = str(Path(__file__).resolve().parent.parent / "credentials.json")
    if os.path.exists(creds_path):
        with open(creds_path) as f:
            data = json.load(f)
        client_id = client_id or data.get("client_id", "")
        client_secret = client_secret or data.get("client_secret", "")
    return client_id, client_secret


def _get_base_url(request: Request) -> str:
    if os.environ.get("OAUTH_REDIRECT_URI"):
        uri = os.environ["OAUTH_REDIRECT_URI"].rstrip("/")
        return uri.replace("/oauth/callback", "") if "/oauth/callback" in uri else uri
    return str(request.base_url).rstrip("/")


def _get_redirect_uri(request: Request) -> str:
    if os.environ.get("OAUTH_REDIRECT_URI"):
        return os.environ["OAUTH_REDIRECT_URI"].rstrip("/")
    return f"{_get_base_url(request)}/oauth/callback"


async def oauth_start(request: Request):
    client_id, client_secret = _get_oauth_config()
    if not client_id or not client_secret:
        return JSONResponse(
            {
                "error": "OAuth not configured. Set OFFICE365_CLIENT_ID/SECRET or credentials.json."
            },
            status_code=500,
        )
    redirect_uri = _get_redirect_uri(request)
    state = secrets.token_urlsafe(32)
    _oauth_tokens[state] = {"status": "pending"}
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(DEFAULT_SCOPES),
        "state": state,
        "response_mode": "query",
    }
    url = (
        f"https://login.microsoftonline.com/{_tenant_id()}/oauth2/v2.0/authorize?"
        + urlencode(params)
    )
    return RedirectResponse(url)


async def oauth_callback(request: Request):
    base_url = _get_base_url(request)
    redirect_uri = _get_redirect_uri(request)
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return RedirectResponse(f"{base_url}/test?oauth_error={error}")
    if not state or not code or state not in _oauth_tokens:
        return RedirectResponse(f"{base_url}/test?oauth_error=invalid_state")

    client_id, client_secret = _get_oauth_config()
    if not client_id or not client_secret:
        return RedirectResponse(f"{base_url}/test?oauth_error=config")

    try:
        body = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(DEFAULT_SCOPES),
        }
        token_url = (
            f"https://login.microsoftonline.com/{_tenant_id()}/oauth2/v2.0/token"
        )
        resp = requests.post(token_url, data=body, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()
    except Exception:
        return RedirectResponse(f"{base_url}/test?oauth_error=exchange")

    creds = {
        "type": "oauth",
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "scopes": DEFAULT_SCOPES,
    }
    _oauth_tokens[state] = {"status": "complete", "credentials": creds}
    return RedirectResponse(f"{base_url}/test?oauth_state={state}")


async def oauth_token(request: Request):
    state = request.query_params.get("state")
    if not state or state not in _oauth_tokens:
        return JSONResponse({"error": "invalid_state"}, status_code=400)
    entry = _oauth_tokens.pop(state, {})
    if entry.get("status") != "complete":
        return JSONResponse({"error": "pending"}, status_code=202)
    return JSONResponse(entry.get("credentials", {}))


async def oauth_info(request: Request):
    client_id, _ = _get_oauth_config()
    return JSONResponse(
        {
            "provider": "microsoft",
            "tenant": _tenant_id(),
            "scopes": DEFAULT_SCOPES,
            "client_id_configured": bool(client_id),
            "oauth_ui_enabled": _oauth_ui_enabled(),
        }
    )
