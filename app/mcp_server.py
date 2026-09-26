"""
Office 365 MCP Server

Microsoft Graph tools for OneDrive and SharePoint:
create, read, download, and delete PDF / Word / Excel / PowerPoint files.

Usage:
    python -m app.mcp_server
    uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import Field

from app.core.exceptions import GraphError
from app.schemas.mcp_models import (
    ChannelListResponse,
    ChannelMessageListResponse,
    ChatListResponse,
    CreateFileResponse,
    CreateFolderResponse,
    DeleteFileResponse,
    DownloadResponse,
    FileListResponse,
    FileMetadata,
    FileMetadataResponse,
    ReadFileResponse,
    SendMessageResponse,
    TeamListResponse,
)
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="office365",
    instructions="""
    Office 365 MCP Server provides tools for OneDrive and SharePoint file operations
    via Microsoft Graph (delegated OAuth):

    - list_files — browse folders
    - get_file_metadata — read file/folder properties
    - read_file — metadata plus file content (base64 for Office/PDF binaries)
    - download_file — download by item_id or path
    - create_file — upload PDF, Word (.doc/.docx), Excel (.xls/.xlsx), PowerPoint (.ppt/.pptx)
    - delete_file — remove a file (requires confirm=true)
    - create_folder — create a folder
    - list_chats / send_chat_message — Teams 1:1 and group chats
    - list_joined_teams / list_team_channels — discover Teams ids
    - list_channel_messages / send_channel_message — channel chat

    Credentials: credentials_path or credentials_json (OAuth token from Connect with Microsoft).

    drive_type:
    - onedrive — user's default OneDrive (/me/drive)
    - sharepoint — requires site_id OR site_hostname + site_path

    Safety:
    - delete_file, send_chat_message, and send_channel_message require confirm=true.
    - create_file supports dry_run to validate inputs without uploading.
  """,
)

_DRIVE_TYPE = Field(
    default="onedrive",
    description="Drive target: onedrive (default) or sharepoint",
)
_SITE_HOSTNAME = Field(
    default=None,
    description="SharePoint hostname, e.g. contoso.sharepoint.com",
)
_SITE_PATH = Field(
    default=None,
    description="SharePoint site server-relative path, e.g. /sites/ProjectAlpha",
)
_SITE_ID = Field(
    default=None,
    description="SharePoint site ID (alternative to hostname+path)",
)
_CREDS_PATH = Field(
    default=None,
    description="OAuth token JSON path under OFFICE365_CREDENTIALS_DIR",
)
_CREDS_JSON = Field(
    default=None,
    description="OAuth token JSON string (access_token/refresh_token)",
)
_ITEM_ID = Field(default=None, description="Drive item ID (Graph driveItem id)")
_FILE_PATH = Field(
    default=None,
    description="Path relative to drive root, e.g. Documents/report.pdf",
)


def _get_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> GraphService:
    if not credentials_path and not credentials_json:
        raise GraphError(
            "Credentials required: provide credentials_path or credentials_json",
            error_code="CREDENTIALS_REQUIRED",
            retryable=False,
        )
    return GraphService(
        credentials_path=credentials_path,
        credentials_json=credentials_json,
    )


def _error_dict(error: GraphError) -> dict:
    return error.to_dict()


def _creds_required() -> dict:
    return {
        "error_code": "CREDENTIALS_REQUIRED",
        "error_message": "Provide credentials_path or credentials_json",
        "retryable": False,
        "original_provider_error": None,
    }


def _confirm_required() -> dict:
    return {
        "error_code": "CONFIRM_REQUIRED",
        "error_message": "Set confirm=true to execute this side-effecting tool",
        "retryable": False,
        "original_provider_error": None,
    }


def _meta_from_dict(data: dict) -> FileMetadata:
    return FileMetadata(**data)


@mcp.tool()
def list_files(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    folder_id: Optional[str] = Field(default=None, description="Parent folder item ID"),
    folder_path: Optional[str] = Field(
        default=None, description="Parent folder path relative to drive root"
    ),
    page_size: int = Field(default=100, description="Max items (1-200)"),
    skip_token: Optional[str] = Field(default=None, description="Pagination token"),
    file_extension: Optional[str] = Field(
        default=None,
        description="Filter by extension, e.g. pdf, docx, xlsx, pptx",
    ),
) -> FileListResponse:
    """List files and folders in OneDrive or SharePoint.

        Capabilities: office365.list_files
Outputs: success
        """
    logger.info("MCP: list_files drive_type=%s", drive_type)
    try:
        if not credentials_path and not credentials_json:
            return FileListResponse(success=False, error=_creds_required())
        service = _get_service(credentials_path, credentials_json)
        files, next_token = service.list_files(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            folder_id=folder_id,
            folder_path=folder_path,
            page_size=page_size,
            skip_token=skip_token,
            file_extension=file_extension,
        )
        meta = [_meta_from_dict(f) for f in files]
        return FileListResponse(
            success=True,
            files=meta,
            total_count=len(meta),
            next_skip_token=next_token,
        )
    except GraphError as e:
        return FileListResponse(success=False, error=_error_dict(e))


@mcp.tool()
def get_file_metadata(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    item_id: Optional[str] = _ITEM_ID,
    file_path: Optional[str] = _FILE_PATH,
) -> FileMetadataResponse:
    """Get metadata for a file or folder by item_id or file_path.

        Capabilities: office365.get_file_metadata
Outputs: success
        """
    logger.info("MCP: get_file_metadata")
    try:
        if not credentials_path and not credentials_json:
            return FileMetadataResponse(success=False, error=_creds_required())
        if not item_id and not file_path:
            return FileMetadataResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": "Provide item_id or file_path",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        service = _get_service(credentials_path, credentials_json)
        metadata = service.get_file_metadata(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            item_id=item_id,
            file_path=file_path,
        )
        return FileMetadataResponse(success=True, metadata=_meta_from_dict(metadata))
    except GraphError as e:
        return FileMetadataResponse(success=False, error=_error_dict(e))


@mcp.tool()
def read_file(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    item_id: Optional[str] = _ITEM_ID,
    file_path: Optional[str] = _FILE_PATH,
    include_content: bool = Field(
        default=True,
        description="If false, return metadata only",
    ),
    as_text: bool = Field(
        default=False,
        description="Return UTF-8 text when MIME is text/* (Office/PDF return base64)",
    ),
) -> ReadFileResponse:
    """Read a file: metadata and optional content (base64 for PDF/Office binaries).

        Capabilities: office365.read_file
Outputs: success
        """
    logger.info("MCP: read_file include_content=%s", include_content)
    try:
        if not credentials_path and not credentials_json:
            return ReadFileResponse(success=False, error=_creds_required())
        if not item_id and not file_path:
            return ReadFileResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": "Provide item_id or file_path",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        service = _get_service(credentials_path, credentials_json)
        result = service.read_file(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            item_id=item_id,
            file_path=file_path,
            include_content=include_content,
            as_text=as_text,
        )
        return ReadFileResponse(
            success=True,
            metadata=_meta_from_dict(result["metadata"]),
            content_base64=result.get("content_base64"),
            content_text=result.get("content_text"),
            size_bytes=result.get("size_bytes"),
            message="Metadata only" if not include_content else "File read",
        )
    except GraphError as e:
        return ReadFileResponse(success=False, error=_error_dict(e))


@mcp.tool()
def download_file(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    item_id: Optional[str] = _ITEM_ID,
    file_path: Optional[str] = _FILE_PATH,
    as_text: bool = Field(
        default=False,
        description="Return plain text for text/* MIME types; else base64",
    ),
) -> DownloadResponse:
    """Download a file from OneDrive or SharePoint.

        Capabilities: office365.download_file
Outputs: success
        """
    logger.info("MCP: download_file")
    try:
        if not credentials_path and not credentials_json:
            return DownloadResponse(success=False, error=_creds_required())
        if not item_id and not file_path:
            return DownloadResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": "Provide item_id or file_path",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        service = _get_service(credentials_path, credentials_json)
        content_bytes, mime, name = service.download_file(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            item_id=item_id,
            file_path=file_path,
            as_text=as_text,
        )
        if as_text and (
            mime.startswith("text/") or "json" in mime or "xml" in mime
        ):
            return DownloadResponse(
                success=True,
                item_id=item_id,
                file_name=name,
                content_text=content_bytes.decode("utf-8", errors="replace"),
                mime_type=mime,
                size_bytes=len(content_bytes),
            )
        return DownloadResponse(
            success=True,
            item_id=item_id,
            file_name=name,
            content_base64=base64.b64encode(content_bytes).decode("ascii"),
            mime_type=mime,
            size_bytes=len(content_bytes),
        )
    except GraphError as e:
        return DownloadResponse(success=False, error=_error_dict(e))


@mcp.tool()
def create_file(
    file_name: str = Field(
        ...,
        description="File name with extension (.pdf, .docx, .xlsx, .pptx, etc.)",
    ),
    content_base64: str = Field(
        ...,
        description="File bytes as base64 (max 4 MiB for simple upload)",
    json_schema_extra={"x-datumbridge-encoding": "base64"}
    ),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    parent_folder_id: Optional[str] = Field(
        default=None, description="Parent folder item ID"
    ),
    parent_folder_path: Optional[str] = Field(
        default=None, description="Parent folder path, e.g. Documents/Reports"
    ),
    mime_type: Optional[str] = Field(
        default=None,
        description="MIME type (auto-detected from extension if omitted)",
    ),
    conflict_behavior: str = Field(
        default="rename",
        description="On name conflict: rename, replace, or fail",
    ),
    confirm: bool = Field(
        default=False,
        description="Must be true to upload (side effect)",
    ),
    dry_run: bool = Field(
        default=False,
        description="Validate inputs without calling Microsoft Graph",
    ),
) -> CreateFileResponse:
    """Create/upload a PDF or Office document to OneDrive or SharePoint.

        Capabilities: office365.create_file
Outputs: success
        """
    logger.info(
        "MCP: create_file name=%s dry_run=%s confirm=%s",
        file_name,
        dry_run,
        confirm,
    )
    try:
        if not credentials_path and not credentials_json:
            return CreateFileResponse(success=False, error=_creds_required())
        if not dry_run and not confirm:
            return CreateFileResponse(success=False, error=_confirm_required())
        if dry_run:
            from app.services.file_types import infer_mime_type, validate_supported_file_name

            validate_supported_file_name(file_name)
            detected = infer_mime_type(file_name, mime_type)
            size = len(base64.b64decode(content_base64))
            return CreateFileResponse(
                success=True,
                dry_run=True,
                message=f"Dry run — would upload {file_name} ({detected}, {size} bytes)",
            )
        service = _get_service(credentials_path, credentials_json)
        metadata = service.create_file(
            file_name=file_name,
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            parent_folder_id=parent_folder_id,
            parent_folder_path=parent_folder_path,
            content_base64=content_base64,
            mime_type=mime_type,
            conflict_behavior=conflict_behavior,
        )
        return CreateFileResponse(
            success=True,
            metadata=_meta_from_dict(metadata),
            message=f"Created {file_name}",
        )
    except GraphError as e:
        return CreateFileResponse(success=False, error=_error_dict(e))


@mcp.tool()
def delete_file(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    item_id: Optional[str] = _ITEM_ID,
    file_path: Optional[str] = _FILE_PATH,
    confirm: bool = Field(
        default=False,
        description="Must be true to delete (permanent side effect)",
    ),
) -> DeleteFileResponse:
    """Delete a file from OneDrive or SharePoint. Requires confirm=true.

        Capabilities: office365.delete_file
Outputs: success
        """
    logger.info("MCP: delete_file confirm=%s", confirm)
    try:
        if not credentials_path and not credentials_json:
            return DeleteFileResponse(success=False, error=_creds_required())
        if not item_id and not file_path:
            return DeleteFileResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": "Provide item_id or file_path",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        if not confirm:
            return DeleteFileResponse(success=False, error=_confirm_required())
        service = _get_service(credentials_path, credentials_json)
        service.delete_file(
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            item_id=item_id,
            file_path=file_path,
        )
        return DeleteFileResponse(
            success=True,
            item_id=item_id,
            file_path=file_path,
            message="File deleted",
        )
    except GraphError as e:
        return DeleteFileResponse(success=False, error=_error_dict(e))


@mcp.tool()
def create_folder(
    folder_name: str = Field(..., description="New folder name"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    drive_type: str = _DRIVE_TYPE,
    site_hostname: Optional[str] = _SITE_HOSTNAME,
    site_path: Optional[str] = _SITE_PATH,
    site_id: Optional[str] = _SITE_ID,
    parent_folder_id: Optional[str] = Field(default=None),
    parent_folder_path: Optional[str] = Field(default=None),
) -> CreateFolderResponse:
    """Create a folder in OneDrive or SharePoint.

        Capabilities: office365.create_folder
Outputs: success
        """
    logger.info("MCP: create_folder name=%s", folder_name)
    try:
        if not credentials_path and not credentials_json:
            return CreateFolderResponse(success=False, error=_creds_required())
        service = _get_service(credentials_path, credentials_json)
        metadata = service.create_folder(
            folder_name=folder_name,
            drive_type=drive_type,
            site_hostname=site_hostname,
            site_path=site_path,
            site_id=site_id,
            parent_folder_id=parent_folder_id,
            parent_folder_path=parent_folder_path,
        )
        return CreateFolderResponse(
            success=True,
            metadata=_meta_from_dict(metadata),
            message=f"Created folder {folder_name}",
        )
    except GraphError as e:
        return CreateFolderResponse(success=False, error=_error_dict(e))


@mcp.tool()
def list_chats(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    page_size: int = Field(default=50, description="Max chats (1-50)"),
    skip_token: Optional[str] = Field(default=None, description="Pagination token"),
) -> ChatListResponse:
    """List Microsoft Teams chats for the signed-in user.

        Capabilities: office365.list_chats
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return ChatListResponse(success=False, error=_creds_required())
        service = _get_service(credentials_path, credentials_json)
        chats, next_token = service.list_chats(page_size=page_size, skip_token=skip_token)
        return ChatListResponse(success=True, chats=chats, next_skip_token=next_token)
    except GraphError as e:
        return ChatListResponse(success=False, error=_error_dict(e))


@mcp.tool()
def send_chat_message(
    chat_id: str = Field(..., description="Teams chat id"),
    content: str = Field(..., description="Plain-text message body", json_schema_extra={"x-datumbridge-encoding": "plain"}),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False, description="Must be true to send"),
    dry_run: bool = Field(default=False, description="Validate without sending"),
) -> SendMessageResponse:
    """Send a message in a Teams chat. Requires confirm=true.

        Capabilities: office365.send_chat_message
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return SendMessageResponse(success=False, error=_creds_required())
        if dry_run:
            return SendMessageResponse(
                success=True,
                dry_run=True,
                chat_id=chat_id,
                message="Dry run — would send chat message",
            )
        if not confirm:
            return SendMessageResponse(success=False, error=_confirm_required())
        service = _get_service(credentials_path, credentials_json)
        result = service.send_chat_message(chat_id=chat_id, content=content)
        return SendMessageResponse(success=True, message="Message sent", **result)
    except GraphError as e:
        return SendMessageResponse(success=False, error=_error_dict(e))


@mcp.tool()
def list_joined_teams(
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
) -> TeamListResponse:
    """List Microsoft Teams the signed-in user has joined.

        Capabilities: office365.list_joined_teams
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return TeamListResponse(success=False, error=_creds_required())
        service = _get_service(credentials_path, credentials_json)
        return TeamListResponse(success=True, teams=service.list_joined_teams())
    except GraphError as e:
        return TeamListResponse(success=False, error=_error_dict(e))


@mcp.tool()
def list_team_channels(
    team_id: str = Field(..., description="Team id from list_joined_teams"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
) -> ChannelListResponse:
    """List channels in a team.

        Capabilities: office365.list_team_channels
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return ChannelListResponse(success=False, error=_creds_required())
        service = _get_service(credentials_path, credentials_json)
        return ChannelListResponse(
            success=True, channels=service.list_team_channels(team_id=team_id)
        )
    except GraphError as e:
        return ChannelListResponse(success=False, error=_error_dict(e))


@mcp.tool()
def list_channel_messages(
    team_id: str = Field(..., description="Team id"),
    channel_id: str = Field(..., description="Channel id"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    page_size: int = Field(default=50, description="Max messages (1-50)"),
) -> ChannelMessageListResponse:
    """List recent messages in a Teams channel.

        Capabilities: office365.list_channel_messages
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return ChannelMessageListResponse(success=False, error=_creds_required())
        service = _get_service(credentials_path, credentials_json)
        messages = service.list_channel_messages(
            team_id=team_id, channel_id=channel_id, page_size=page_size
        )
        return ChannelMessageListResponse(success=True, messages=messages)
    except GraphError as e:
        return ChannelMessageListResponse(success=False, error=_error_dict(e))


@mcp.tool()
def send_channel_message(
    team_id: str = Field(..., description="Team id"),
    channel_id: str = Field(..., description="Channel id"),
    content: str = Field(..., description="Plain-text message body", json_schema_extra={"x-datumbridge-encoding": "plain"}),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False, description="Must be true to send"),
    dry_run: bool = Field(default=False, description="Validate without sending"),
) -> SendMessageResponse:
    """Send a message to a Teams channel. Requires confirm=true.

        Capabilities: office365.send_channel_message
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return SendMessageResponse(success=False, error=_creds_required())
        if dry_run:
            return SendMessageResponse(
                success=True,
                dry_run=True,
                team_id=team_id,
                channel_id=channel_id,
                message="Dry run — would send channel message",
            )
        if not confirm:
            return SendMessageResponse(success=False, error=_confirm_required())
        service = _get_service(credentials_path, credentials_json)
        result = service.send_channel_message(
            team_id=team_id, channel_id=channel_id, content=content
        )
        return SendMessageResponse(success=True, message="Message sent", **result)
    except GraphError as e:
        return SendMessageResponse(success=False, error=_error_dict(e))


_base_app = mcp.http_app()

from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route

from app.oauth_routes import (
    _oauth_ui_enabled,
    oauth_callback,
    oauth_info,
    oauth_start,
    oauth_token,
)


async def health(request):
    return JSONResponse({"status": "ok", "service": "office365-mcp"})


async def test_ui(request):
    if not _oauth_ui_enabled():
        return JSONResponse(
            {
                "error_code": "OAUTH_UI_DISABLED",
                "error_message": "Set OFFICE365_ENABLE_OAUTH_UI=1 for local /test UI",
                "retryable": False,
            },
            status_code=404,
        )
    ui_path = Path(__file__).resolve().parent.parent / "static" / "test-ui.html"
    if not ui_path.exists():
        return JSONResponse({"error": "test-ui.html not found"}, status_code=404)
    return FileResponse(ui_path, media_type="text/html")


http_app = Starlette(
    routes=[
        Route("/health", health),
        Route("/test", test_ui),
        Route("/oauth/start", oauth_start),
        Route("/oauth/callback", oauth_callback),
        Route("/oauth/token", oauth_token),
        Route("/oauth/info", oauth_info),
        Mount("/", _base_app),
    ],
    lifespan=getattr(_base_app, "lifespan", None),
)


if __name__ == "__main__":
    logger.info("Starting Office 365 MCP Server (stdio mode)")
    mcp.run()
