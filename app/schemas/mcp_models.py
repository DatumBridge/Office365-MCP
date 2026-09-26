"""Pydantic models for Office 365 MCP Server tools."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    web_url: Optional[str] = None
    parent_id: Optional[str] = None
    drive_id: Optional[str] = None
    is_folder: bool = False
    path: Optional[str] = None


class BaseToolResponse(BaseModel):
    success: bool
    error: Optional[dict] = None


class FileListResponse(BaseToolResponse):
    files: List[FileMetadata] = Field(default_factory=list)
    total_count: int = 0
    next_skip_token: Optional[str] = None


class FileMetadataResponse(BaseToolResponse):
    metadata: Optional[FileMetadata] = None


class ReadFileResponse(BaseToolResponse):
    metadata: Optional[FileMetadata] = None
    content_base64: Optional[str] = None
    content_text: Optional[str] = None
    size_bytes: Optional[int] = None
    message: Optional[str] = None


class DownloadResponse(BaseToolResponse):
    item_id: Optional[str] = None
    file_name: Optional[str] = None
    content_base64: Optional[str] = None
    content_text: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class CreateFileResponse(BaseToolResponse):
    metadata: Optional[FileMetadata] = None
    message: Optional[str] = None
    dry_run: bool = False


class DeleteFileResponse(BaseToolResponse):
    item_id: Optional[str] = None
    file_path: Optional[str] = None
    message: Optional[str] = None


class CreateFolderResponse(BaseToolResponse):
    metadata: Optional[FileMetadata] = None
    message: Optional[str] = None


class ChatItem(BaseModel):
    id: Optional[str] = None
    topic: Optional[str] = None
    chat_type: Optional[str] = None
    web_url: Optional[str] = None
    last_updated: Optional[str] = None


class ChatListResponse(BaseToolResponse):
    chats: List[ChatItem] = Field(default_factory=list)
    next_skip_token: Optional[str] = None


class SendMessageResponse(BaseToolResponse):
    id: Optional[str] = None
    chat_id: Optional[str] = None
    team_id: Optional[str] = None
    channel_id: Optional[str] = None
    created: Optional[str] = None
    web_url: Optional[str] = None
    message: Optional[str] = None
    dry_run: bool = False


class TeamItem(BaseModel):
    id: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None


class TeamListResponse(BaseToolResponse):
    teams: List[TeamItem] = Field(default_factory=list)


class ChannelItem(BaseModel):
    id: Optional[str] = None
    display_name: Optional[str] = None
    membership_type: Optional[str] = None
    web_url: Optional[str] = None


class ChannelListResponse(BaseToolResponse):
    channels: List[ChannelItem] = Field(default_factory=list)


class ChatMessageItem(BaseModel):
    id: Optional[str] = None
    created: Optional[str] = None
    from_name: Optional[str] = None
    content: Optional[str] = None


class ChannelMessageListResponse(BaseToolResponse):
    messages: List[ChatMessageItem] = Field(default_factory=list)
