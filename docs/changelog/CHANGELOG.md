# Changelog

## 2026-10-30

### Added

- `read_file` can transform Excel `.xlsx` and `.xlsm` cell values to JSON or XML via `excel_format`.
- Optional `sheet_name` to read one worksheet, and `header_row` to return JSON rows as objects keyed by the first non-empty row.
- Response fields `content_json`, `content_xml`, `excel_format`, and `truncated`.
- In-memory workbook limits: 8 MiB file, 32 MiB declared uncompressed size, 512 package entries, 32 sheets, 2000 rows, 50 columns, 20000 cells, 1,000,000 characters of cell text.

### Changed

- Excel reads that set `excel_format` no longer return `content_base64`. Other files are unchanged.
- Legacy `.xls`, encrypted workbooks, and macro execution stay unsupported. Formulas are returned as text and are not calculated.
- Oversized workbooks are rejected from item size before download, and the body is streamed only up to 8 MiB. Package XML is parsed with `defusedxml`. Only store and deflate ZIP members are accepted. A value past a blank row or column still sets `truncated`. Serialized JSON or XML is capped at 1,000,000 characters.

## 2026-10-14

### Changed

- Outlook mail is not in this server. Use sibling `outlook-mcp` and a separate Azure app.

## 2026-08-26

### Added

- Teams Graph tools on the same Microsoft 365 Connect: `list_chats`, `send_chat_message`, `list_joined_teams`, `list_team_channels`, `list_channel_messages`, `send_channel_message`. Writes require `confirm=true`.
- k8s publish target namespace `mcp-tools` (`office365-mcp-main`).

### Changed

- Delegated Graph scopes now include Chat/Channel/Team read-write. Existing Studio Connect users must Disconnect and Connect again.

## 2026-07-20

### Added

- Initial **office365-mcp** repository — FastMCP tool-server for OneDrive and SharePoint.
- **Studio credential vault integration** — Connect / Disconnect via DatumBridge **Account → Integrations** (`office365` provider); `credentials_json` injected when `mcpServer` contains `office365`.
- Tools: `list_files`, `get_file_metadata`, `read_file`, `download_file`, `create_file`, `delete_file`, `create_folder`.
- PDF and Office formats: `.pdf`, `.doc/.docx`, `.xls/.xlsx`, `.ppt/.pptx`.
- Delegated OAuth (Microsoft identity) with token refresh.
- SharePoint site resolution via `site_id` or `site_hostname` + `site_path`.
- Docker image, OAuth CLI (`scripts/oauth_connect.py`), unit tests for file type helpers.
