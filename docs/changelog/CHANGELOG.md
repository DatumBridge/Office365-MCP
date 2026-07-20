# Changelog

## 2026-07-20

### Added

- Initial **office365-mcp** repository — FastMCP tool-server for OneDrive and SharePoint.
- Tools: `list_files`, `get_file_metadata`, `read_file`, `download_file`, `create_file`, `delete_file`, `create_folder`.
- PDF and Office formats: `.pdf`, `.doc/.docx`, `.xls/.xlsx`, `.ppt/.pptx`.
- Delegated OAuth (Microsoft identity) with token refresh.
- SharePoint site resolution via `site_id` or `site_hostname` + `site_path`.
- Docker image, OAuth CLI (`scripts/oauth_connect.py`), unit tests for file type helpers.
