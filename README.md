# Office 365 MCP Server

DatumBridge **tool-server** for **OneDrive** and **SharePoint** file operations via **Microsoft Graph**. Sibling to `google-drive-mcp` and `gmail-mcp`.

**Registry id:** `mcpServer=office365`

## Tools

| Tool | Description |
|------|-------------|
| `list_files` | Browse folders (OneDrive or SharePoint) |
| `get_file_metadata` | Read file/folder properties |
| `read_file` | Metadata + content (base64 for PDF/Office binaries) |
| `download_file` | Download by `item_id` or `file_path` |
| `create_file` | Upload PDF, Word, Excel, PowerPoint (`confirm=true`) |
| `delete_file` | Delete file (`confirm=true`) |
| `create_folder` | Create a folder |

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
python scripts/test_helpers.py -v
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
- Office binary content is returned as **base64**; text extraction is not performed server-side.

## Docs

- [`design.md`](design.md)
- [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md)
- [`docs/changelog/CHANGELOG.md`](docs/changelog/CHANGELOG.md)
