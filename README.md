# Office 365 MCP Server

DatumBridge **tool-server** for **OneDrive** and **SharePoint** file operations via **Microsoft Graph**. Sibling to `google-drive-mcp`. **Outlook mail is `outlook-mcp`**, a separate Azure app — do not add Mail Graph permissions here.

**Registry id:** `mcpServer=office365`

**Production (DatumBridge Studio):** connect under **Account → Integrations**. The platform credential vault injects `credentials_json` on tool execute — do not map tokens in workflows.

## Tools

| Tool | Description |
|------|-------------|
| `list_files` | Browse folders (OneDrive or SharePoint) |
| `get_file_metadata` | Read file/folder properties |
| `read_file` | Metadata + content. Excel `.xlsx`/`.xlsm` can be returned as JSON or XML |
| `download_file` | Download by `item_id` or `file_path` |
| `create_file` | Upload PDF, Word, Excel, PowerPoint (`confirm=true`) |
| `delete_file` | Delete file (`confirm=true`) |
| `create_folder` | Create a folder |
| `list_chats` | List Teams chats for the signed-in user |
| `send_chat_message` | Send a Teams chat message (`confirm=true`) |
| `list_joined_teams` | List joined teams |
| `list_team_channels` | List channels in a team |
| `list_channel_messages` | List channel messages |
| `send_channel_message` | Send a channel message (`confirm=true`) |

### Supported file types

| Extension | Type |
|-----------|------|
| `.pdf` | PDF |
| `.doc` / `.docx` | Word |
| `.xls` / `.xlsx` | Excel |
| `.ppt` / `.pptx` | PowerPoint |

Every tool requires **`credentials_path`** or **`credentials_json`** (delegated OAuth token).

Side-effect tools:
- `create_file` — `confirm=true` (use `dry_run=true` to validate)
- `delete_file` — `confirm=true`

### Drive targets

- **OneDrive** (default): `drive_type=onedrive` → `/me/drive`
- **SharePoint**: `drive_type=sharepoint` plus either:
  - `site_id`, or
  - `site_hostname` + `site_path` (e.g. `contoso.sharepoint.com`, `/sites/ProjectAlpha`)

## Azure AD setup

1. [Azure Portal](https://portal.azure.com) → **App registrations** → New registration.
2. Add redirect URI: `http://localhost:8000/oauth/callback` (or your `OAUTH_REDIRECT_URI`).
3. **API permissions** (delegated):
   - `User.Read`
   - `Files.ReadWrite`
   - `Sites.ReadWrite.All`
4. Create a **client secret**; set `OFFICE365_CLIENT_ID` / `OFFICE365_CLIENT_SECRET`.
5. Set `OFFICE365_TENANT_ID` to your tenant ID, or `common` / `organizations`.

## Local run

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_mcp.txt
chmod +x mcp_server_entrypoint.sh
./mcp_server_entrypoint.sh
```

- Health: `GET http://localhost:8000/health`
- MCP: `POST http://localhost:8000/mcp/`
- Test UI: `http://localhost:8000/test` (`OFFICE365_ENABLE_OAUTH_UI=1`)

### OAuth token (CLI)

```bash
export OFFICE365_CLIENT_ID=...
export OFFICE365_CLIENT_SECRET=...
python scripts/oauth_connect.py
# writes token.json — pass credentials_path=token.json to tools
```

### Tests (no network)

```bash
PYTHONPATH=. python -m unittest tests.test_excel_workbook scripts.test_helpers -v
```

## Docker

```bash
docker build -t office365-mcp .
docker run -p 8000:8000 \
  -e OFFICE365_CLIENT_ID=... \
  -e OFFICE365_CLIENT_SECRET=... \
  office365-mcp
```

## Example tool calls

**List PDFs in OneDrive Documents:**

```json
{
  "drive_type": "onedrive",
  "folder_path": "Documents",
  "file_extension": "pdf",
  "credentials_path": "token.json"
}
```

**Upload a Word document:**

```json
{
  "file_name": "proposal.docx",
  "content_base64": "<base64>",
  "parent_folder_path": "Documents",
  "confirm": true,
  "credentials_path": "token.json"
}
```

**Read an Excel workbook as JSON:**

```json
{
  "drive_type": "onedrive",
  "file_path": "Documents/orders.xlsx",
  "excel_format": "json",
  "header_row": true,
  "credentials_path": "token.json"
}
```

`excel_format` is `json` or `xml`. Omit it to keep the raw file as base64. `sheet_name` limits the read to one worksheet. Formulas are returned as formula text and are not calculated.

**Read SharePoint file:**

```json
{
  "drive_type": "sharepoint",
  "site_hostname": "contoso.sharepoint.com",
  "site_path": "/sites/ProjectAlpha",
  "file_path": "Shared Documents/report.pdf",
  "credentials_path": "token.json"
}
```

## Limits

- Simple upload max **4 MiB** per `create_file` (Microsoft Graph simple upload). Larger files need upload session support (future).
- Without `excel_format`, Office and PDF bytes are returned as **base64**.
- `read_file` with `excel_format=json` or `excel_format=xml` parses `.xlsx` and `.xlsm` in memory. The raw file must be at most **8 MiB**, with at most **2000** rows and **50** columns per sheet. Legacy `.xls` is not parsed. Formulas and macros are not executed.

## Docs

- [`design.md`](design.md)
- [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md)
- [`docs/changelog/CHANGELOG.md`](docs/changelog/CHANGELOG.md)
