"""Supported Office document MIME types and extension helpers."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Optional

from app.core.exceptions import GraphValidationError

# PDF + Microsoft Office formats (Open XML and legacy)
EXTENSION_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".ppt": "application/vnd.ms-powerpoint",
}

MIME_TO_EXTENSION: dict[str, str] = {
    mime: ext for ext, mime in EXTENSION_TO_MIME.items()
}

SUPPORTED_EXTENSIONS = frozenset(EXTENSION_TO_MIME.keys())


def infer_mime_type(file_name: str, mime_type: Optional[str] = None) -> str:
    if mime_type and mime_type.strip():
        return mime_type.strip()
    ext = PurePosixPath(file_name).suffix.lower()
    if ext in EXTENSION_TO_MIME:
        return EXTENSION_TO_MIME[ext]
    raise GraphValidationError(
        f"Unsupported file type for '{file_name}'. "
        f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def validate_supported_file_name(file_name: str) -> str:
    name = (file_name or "").strip()
    if not name:
        raise GraphValidationError("file_name is required")
    ext = PurePosixPath(name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise GraphValidationError(
            f"Unsupported extension '{ext or '(none)'}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return name


def is_folder_mime(mime_type: str) -> bool:
    return mime_type == "application/vnd.microsoft.graph.folder"
