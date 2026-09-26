"""
Microsoft Graph API wrapper for OneDrive and SharePoint file operations.

Credentials are passed as input (credentials_path or credentials_json).
Uses delegated OAuth tokens with refresh support.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import requests

from app.core.exceptions import (
    GraphError,
    GraphValidationError,
    normalize_graph_error,
)
from app.services.file_types import infer_mime_type, is_folder_mime, validate_supported_file_name

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
DEFAULT_SCOPES = (
    "openid",
    "profile",
    "offline_access",
    "User.Read",
    "Files.ReadWrite",
    "Sites.ReadWrite.All",
    "Chat.ReadWrite",
    "ChannelMessage.Send",
    "ChannelMessage.Read.All",
    "Team.ReadBasic.All",
    "Channel.ReadBasic.All",
)
DEFAULT_TIMEOUT_SEC = 60
MAX_SIMPLE_UPLOAD_BYTES = 4 * 1024 * 1024  # Graph simple upload limit


def _request_timeout() -> int:
    raw = os.environ.get("OFFICE365_HTTP_TIMEOUT_SEC", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SEC
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TIMEOUT_SEC


def _tenant_id() -> str:
    return os.environ.get("OFFICE365_TENANT_ID", "common").strip() or "common"


def _token_url() -> str:
    return f"https://login.microsoftonline.com/{_tenant_id()}/oauth2/v2.0/token"


def _credentials_dir() -> Path:
    raw = os.environ.get("OFFICE365_CREDENTIALS_DIR", "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _is_oauth_creds(creds_dict: dict) -> bool:
    has_access = bool(creds_dict.get("access_token") or creds_dict.get("token"))
    has_refresh = bool(creds_dict.get("refresh_token"))
    return creds_dict.get("type") == "oauth" or has_access or has_refresh


def _resolve_credentials_path(credentials_path: str) -> Path:
    base = _credentials_dir()
    candidate = Path(credentials_path)
    if not candidate.is_absolute():
        candidate = (base / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise GraphError(
            "credentials_path must be under OFFICE365_CREDENTIALS_DIR",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e
    return candidate


def load_credentials_dict(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> dict:
    creds_dict: Optional[dict] = None
    try:
        if credentials_json:
            creds_dict = json.loads(credentials_json)
        elif credentials_path:
            path = _resolve_credentials_path(credentials_path)
            if not path.exists():
                raise GraphError(
                    f"Credentials file not found: {credentials_path}",
                    error_code="CREDENTIALS_REQUIRED",
                    retryable=False,
                )
            with open(path) as f:
                creds_dict = json.load(f)
    except GraphError:
        raise
    except json.JSONDecodeError as e:
        raise GraphError(
            "Invalid credentials JSON",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e
    except OSError as e:
        raise GraphError(
            "Unable to read credentials file",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e

    if not creds_dict or not isinstance(creds_dict, dict):
        raise GraphError(
            "Credentials required: provide credentials_path or credentials_json",
            error_code="CREDENTIALS_REQUIRED",
            retryable=False,
        )
    if not _is_oauth_creds(creds_dict):
        raise GraphError(
            "OAuth credentials required. Use Connect with Microsoft or scripts/oauth_connect.py.",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    access = creds_dict.get("access_token") or creds_dict.get("token")
    refresh = creds_dict.get("refresh_token")
    if not access and not refresh:
        raise GraphError(
            "OAuth credentials must include access_token or refresh_token",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    return creds_dict


def _client_credentials(creds_dict: dict) -> tuple[str, str]:
    client_id = creds_dict.get("client_id") or os.environ.get("OFFICE365_CLIENT_ID", "")
    client_secret = creds_dict.get("client_secret") or os.environ.get(
        "OFFICE365_CLIENT_SECRET", ""
    )
    return client_id.strip(), client_secret.strip()


def refresh_access_token(creds_dict: dict) -> dict:
    refresh_token = creds_dict.get("refresh_token")
    if not refresh_token:
        raise GraphError(
            "No refresh_token available; re-authenticate",
            error_code="AUTH_ERROR",
            retryable=False,
        )
    client_id, client_secret = _client_credentials(creds_dict)
    if not client_id or not client_secret:
        raise GraphError(
            "client_id and client_secret required for token refresh "
            "(in credentials or OFFICE365_CLIENT_ID/SECRET env)",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": " ".join(creds_dict.get("scopes") or DEFAULT_SCOPES),
    }
    try:
        resp = requests.post(_token_url(), data=body, timeout=_request_timeout())
        if resp.status_code >= 400:
            raise normalize_graph_error(
                Exception(resp.text), status_code=resp.status_code
            )
        data = resp.json()
    except GraphError:
        raise
    except requests.RequestException as e:
        raise normalize_graph_error(e) from e

    creds_dict["access_token"] = data.get("access_token")
    creds_dict["token"] = data.get("access_token")
    if data.get("refresh_token"):
        creds_dict["refresh_token"] = data["refresh_token"]
    creds_dict["expires_in"] = data.get("expires_in")
    return creds_dict


class GraphService:
    """Microsoft Graph wrapper for OneDrive and SharePoint drives."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._creds = load_credentials_dict(credentials_path, credentials_json)

    def _access_token(self) -> str:
        token = self._creds.get("access_token") or self._creds.get("token")
        if not token:
            self._creds = refresh_access_token(self._creds)
            token = self._creds.get("access_token")
        if not token:
            raise GraphError("Missing access token", error_code="AUTH_ERROR", retryable=True)
        return token

    def _headers(self, content_type: Optional[str] = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
        data: Optional[bytes] = None,
        content_type: Optional[str] = None,
        raw: bool = False,
    ) -> Any:
        try:
            resp = requests.request(
                method,
                url,
                headers=self._headers(content_type),
                params=params,
                json=json_body,
                data=data,
                timeout=_request_timeout(),
            )
            if resp.status_code == 401:
                self._creds = refresh_access_token(self._creds)
                resp = requests.request(
                    method,
                    url,
                    headers=self._headers(content_type),
                    params=params,
                    json=json_body,
                    data=data,
                    timeout=_request_timeout(),
                )
            if resp.status_code >= 400:
                detail = resp.text[:500] if resp.text else resp.reason
                raise normalize_graph_error(
                    Exception(detail), status_code=resp.status_code
                )
            if raw:
                return resp.content
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
        except GraphError:
            raise
        except requests.RequestException as e:
            raise normalize_graph_error(e) from e

    def _normalize_drive_location(
        self,
        drive_type: str,
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
    ) -> str:
        kind = (drive_type or "onedrive").strip().lower()
        if kind == "onedrive":
            return "/me/drive"
        if kind != "sharepoint":
            raise GraphValidationError("drive_type must be 'onedrive' or 'sharepoint'")
        if site_id:
            return f"/sites/{site_id}/drive"
        host = (site_hostname or "").strip()
        path = (site_path or "").strip()
        if not host or not path:
            raise GraphValidationError(
                "SharePoint requires site_id or both site_hostname and site_path"
            )
        if not path.startswith("/"):
            path = "/" + path
        encoded = quote(f"{host}:{path}", safe="")
        site = self._request("GET", f"{GRAPH_BASE}/sites/{encoded}")
        resolved_id = site.get("id")
        if not resolved_id:
            raise GraphError("Unable to resolve SharePoint site", error_code="NOT_FOUND")
        return f"/sites/{resolved_id}/drive"

    def _item_url(
        self,
        drive_prefix: str,
        *,
        item_id: Optional[str] = None,
        file_path: Optional[str] = None,
        suffix: str = "",
    ) -> str:
        if item_id:
            return f"{GRAPH_BASE}{drive_prefix}/items/{item_id}{suffix}"
        path = (file_path or "").strip().lstrip("/")
        if not path:
            raise GraphValidationError("Provide item_id or file_path")
        encoded_path = quote(path, safe="/")
        return f"{GRAPH_BASE}{drive_prefix}/root:/{encoded_path}:{suffix}"

    def _to_metadata(self, item: dict) -> dict:
        mime = item.get("file", {}).get("mimeType") or (
            "application/vnd.microsoft.graph.folder"
            if "folder" in item
            else "application/octet-stream"
        )
        parent = item.get("parentReference") or {}
        return {
            "id": item.get("id"),
            "name": item.get("name"),
            "mime_type": mime,
            "size": item.get("size"),
            "created_time": item.get("createdDateTime"),
            "modified_time": item.get("lastModifiedDateTime"),
            "web_url": item.get("webUrl"),
            "parent_id": parent.get("id"),
            "drive_id": parent.get("driveId"),
            "is_folder": "folder" in item,
            "path": parent.get("path"),
        }

    def list_files(
        self,
        *,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        folder_path: Optional[str] = None,
        page_size: int = 100,
        skip_token: Optional[str] = None,
        file_extension: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        drive_prefix = self._normalize_drive_location(
            drive_type, site_hostname, site_path, site_id
        )
        if folder_id:
            url = f"{GRAPH_BASE}{drive_prefix}/items/{folder_id}/children"
        elif folder_path:
            url = self._item_url(drive_prefix, file_path=folder_path, suffix=":/children")
        else:
            url = f"{GRAPH_BASE}{drive_prefix}/root/children"

        params: dict[str, Any] = {
            "$top": min(max(page_size, 1), 200),
            "$select": "id,name,size,createdDateTime,lastModifiedDateTime,webUrl,file,folder,parentReference",
        }
        if skip_token:
            params["$skiptoken"] = skip_token

        data = self._request("GET", url, params=params)
        items = data.get("value", [])
        if file_extension:
            ext = file_extension.lower()
            if not ext.startswith("."):
                ext = "." + ext
            items = [
                i
                for i in items
                if i.get("name", "").lower().endswith(ext) or "folder" in i
            ]
        files = [self._to_metadata(i) for i in items]
        next_link = data.get("@odata.nextLink")
        next_token = None
        if next_link and "$skiptoken=" in next_link:
            next_token = next_link.split("$skiptoken=", 1)[1].split("&", 1)[0]
        return files, next_token

    def get_file_metadata(
        self,
        *,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        item_id: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> dict:
        drive_prefix = self._normalize_drive_location(
            drive_type, site_hostname, site_path, site_id
        )
        url = self._item_url(drive_prefix, item_id=item_id, file_path=file_path)
        item = self._request("GET", url)
        return self._to_metadata(item)

    def read_file(
        self,
        *,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        item_id: Optional[str] = None,
        file_path: Optional[str] = None,
        include_content: bool = True,
        as_text: bool = False,
    ) -> dict:
        metadata = self.get_file_metadata(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            item_id=item_id,
            file_path=file_path,
        )
        if metadata.get("is_folder"):
            raise GraphValidationError("Cannot read a folder as a file")
        result = {"metadata": metadata}
        if not include_content:
            return result

        drive_prefix = self._normalize_drive_location(
            drive_type, site_hostname, site_path, site_id
        )
        url = self._item_url(
            drive_prefix,
            item_id=item_id or metadata.get("id"),
            file_path=file_path,
            suffix="/content",
        )
        content_bytes = self._request("GET", url, raw=True)
        mime = metadata.get("mime_type") or "application/octet-stream"
        if as_text and (
            mime.startswith("text/") or "json" in mime or "xml" in mime
        ):
            result["content_text"] = content_bytes.decode("utf-8", errors="replace")
        else:
            result["content_base64"] = base64.b64encode(content_bytes).decode("ascii")
        result["size_bytes"] = len(content_bytes)
        return result

    def download_file(
        self,
        *,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        item_id: Optional[str] = None,
        file_path: Optional[str] = None,
        as_text: bool = False,
    ) -> tuple[bytes, str, str]:
        payload = self.read_file(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            item_id=item_id,
            file_path=file_path,
            include_content=True,
            as_text=as_text,
        )
        metadata = payload["metadata"]
        mime = metadata.get("mime_type") or "application/octet-stream"
        name = metadata.get("name") or "file"
        if "content_text" in payload:
            return payload["content_text"].encode("utf-8"), mime, name
        raw = base64.b64decode(payload["content_base64"])
        return raw, mime, name

    def create_file(
        self,
        *,
        file_name: str,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        parent_folder_path: Optional[str] = None,
        content_base64: Optional[str] = None,
        mime_type: Optional[str] = None,
        conflict_behavior: str = "rename",
    ) -> dict:
        name = validate_supported_file_name(file_name)
        content_type = infer_mime_type(name, mime_type)
        if not content_base64:
            raise GraphValidationError("content_base64 is required to create a file")
        content_bytes = base64.b64decode(content_base64)
        if len(content_bytes) > MAX_SIMPLE_UPLOAD_BYTES:
            raise GraphValidationError(
                f"File exceeds simple upload limit ({MAX_SIMPLE_UPLOAD_BYTES} bytes). "
                "Split the file or use a smaller payload."
            )

        drive_prefix = self._normalize_drive_location(
            drive_type, site_hostname, site_path, site_id
        )
        behavior = (conflict_behavior or "rename").strip().lower()
        if behavior not in ("rename", "replace", "fail"):
            raise GraphValidationError(
                "conflict_behavior must be rename, replace, or fail"
            )

        if parent_folder_id:
            url = (
                f"{GRAPH_BASE}{drive_prefix}/items/{parent_folder_id}"
                f":/{quote(name)}:/content"
            )
        elif parent_folder_path:
            folder = parent_folder_path.strip().lstrip("/").rstrip("/")
            url = (
                f"{GRAPH_BASE}{drive_prefix}/root:/{quote(folder, safe='/')}"
                f"/{quote(name)}:/content"
            )
        else:
            url = f"{GRAPH_BASE}{drive_prefix}/root:/{quote(name)}:/content"

        params = {"@microsoft.graph.conflictBehavior": behavior}
        item = self._request(
            "PUT",
            url,
            params=params,
            data=content_bytes,
            content_type=content_type,
        )
        return self._to_metadata(item)

    def delete_file(
        self,
        *,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        item_id: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> None:
        drive_prefix = self._normalize_drive_location(
            drive_type, site_hostname, site_path, site_id
        )
        url = self._item_url(drive_prefix, item_id=item_id, file_path=file_path)
        self._request("DELETE", url)

    def create_folder(
        self,
        *,
        folder_name: str,
        drive_type: str = "onedrive",
        site_hostname: Optional[str] = None,
        site_path: Optional[str] = None,
        site_id: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        parent_folder_path: Optional[str] = None,
    ) -> dict:
        name = (folder_name or "").strip()
        if not name:
            raise GraphValidationError("folder_name is required")

        drive_prefix = self._normalize_drive_location(
            drive_type, site_hostname, site_path, site_id
        )
        body = {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename",
        }
        if parent_folder_id:
            url = f"{GRAPH_BASE}{drive_prefix}/items/{parent_folder_id}/children"
        elif parent_folder_path:
            url = self._item_url(
                drive_prefix, file_path=parent_folder_path, suffix=":/children"
            )
        else:
            url = f"{GRAPH_BASE}{drive_prefix}/root/children"

        item = self._request("POST", url, json_body=body)
        return self._to_metadata(item)

    def list_chats(
        self,
        *,
        page_size: int = 50,
        skip_token: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        params: dict[str, Any] = {"$top": max(1, min(page_size, 50))}
        if skip_token:
            params["$skiptoken"] = skip_token
        data = self._request("GET", f"{GRAPH_BASE}/me/chats", params=params)
        items = []
        for chat in data.get("value") or []:
            items.append(
                {
                    "id": chat.get("id"),
                    "topic": chat.get("topic"),
                    "chat_type": chat.get("chatType"),
                    "web_url": chat.get("webUrl"),
                    "last_updated": chat.get("lastUpdatedDateTime"),
                }
            )
        next_link = data.get("@odata.nextLink") or ""
        next_token = None
        if "skiptoken=" in next_link:
            next_token = next_link.split("skiptoken=", 1)[-1]
        return items, next_token

    def send_chat_message(self, *, chat_id: str, content: str) -> dict:
        cid = (chat_id or "").strip()
        body = (content or "").strip()
        if not cid or not body:
            raise GraphValidationError("chat_id and content are required")
        data = self._request(
            "POST",
            f"{GRAPH_BASE}/me/chats/{quote(cid, safe='')}/messages",
            json_body={"body": {"content": body}},
        )
        return {
            "id": data.get("id"),
            "chat_id": cid,
            "created": data.get("createdDateTime"),
            "web_url": data.get("webUrl"),
        }

    def list_joined_teams(self) -> list[dict]:
        data = self._request("GET", f"{GRAPH_BASE}/me/joinedTeams")
        out = []
        for team in data.get("value") or []:
            out.append(
                {
                    "id": team.get("id"),
                    "display_name": team.get("displayName"),
                    "description": team.get("description"),
                }
            )
        return out

    def list_team_channels(self, *, team_id: str) -> list[dict]:
        tid = (team_id or "").strip()
        if not tid:
            raise GraphValidationError("team_id is required")
        data = self._request(
            "GET", f"{GRAPH_BASE}/teams/{quote(tid, safe='')}/channels"
        )
        out = []
        for ch in data.get("value") or []:
            out.append(
                {
                    "id": ch.get("id"),
                    "display_name": ch.get("displayName"),
                    "membership_type": ch.get("membershipType"),
                    "web_url": ch.get("webUrl"),
                }
            )
        return out

    def list_channel_messages(
        self,
        *,
        team_id: str,
        channel_id: str,
        page_size: int = 50,
    ) -> list[dict]:
        tid = (team_id or "").strip()
        cid = (channel_id or "").strip()
        if not tid or not cid:
            raise GraphValidationError("team_id and channel_id are required")
        data = self._request(
            "GET",
            f"{GRAPH_BASE}/teams/{quote(tid, safe='')}/channels/{quote(cid, safe='')}/messages",
            params={"$top": max(1, min(page_size, 50))},
        )
        out = []
        for msg in data.get("value") or []:
            body = msg.get("body") or {}
            from_user = ((msg.get("from") or {}).get("user") or {})
            out.append(
                {
                    "id": msg.get("id"),
                    "created": msg.get("createdDateTime"),
                    "from_name": from_user.get("displayName"),
                    "content": body.get("content"),
                }
            )
        return out

    def send_channel_message(
        self, *, team_id: str, channel_id: str, content: str
    ) -> dict:
        tid = (team_id or "").strip()
        cid = (channel_id or "").strip()
        body = (content or "").strip()
        if not tid or not cid or not body:
            raise GraphValidationError("team_id, channel_id, and content are required")
        data = self._request(
            "POST",
            f"{GRAPH_BASE}/teams/{quote(tid, safe='')}/channels/{quote(cid, safe='')}/messages",
            json_body={"body": {"content": body}},
        )
        return {
            "id": data.get("id"),
            "team_id": tid,
            "channel_id": cid,
            "created": data.get("createdDateTime"),
            "web_url": data.get("webUrl"),
        }
