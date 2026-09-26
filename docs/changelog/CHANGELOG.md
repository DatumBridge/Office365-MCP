# Changelog

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
