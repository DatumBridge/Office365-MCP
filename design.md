# Office 365 MCP — Design

## Purpose

MCP tool-server exposing Microsoft Graph delegated file operations for **OneDrive** and **SharePoint**, focused on PDF and Microsoft Office formats.

## Architecture

```text
MCP Client (Studio / Agent)
        ↓ Streamable HTTP / stdio
office365-mcp (FastMCP)
        ↓ OAuth bearer token
Microsoft Graph API v1.0
        ↓
OneDrive (/me/drive) | SharePoint (/sites/{id}/drive)
```

## Tool surface

| Tool | Graph operation | Side effect |
|------|-----------------|-------------|
| list_files | GET .../children | No |
| get_file_metadata | GET .../items/{id} | No |
| read_file | GET metadata + /content. Optional in-memory Excel JSON or XML transform | No |
| download_file | GET /content | No |
| create_file | PUT ...:/{name}:/content | Yes (`confirm`) |
| delete_file | DELETE .../items/{id} | Yes (`confirm`) |
| create_folder | POST .../children | No |

## Credentials

- Input-only: `credentials_path` or `credentials_json`
- Path jail: `OFFICE365_CREDENTIALS_DIR`
- Refresh via `refresh_token` + `OFFICE365_CLIENT_SECRET` (or secret in token JSON)

## Security

- Deny-by-default on writes/deletes without `confirm=true`
- No secrets in tool responses
- Treat downloaded file content as untrusted data, including Excel cell text
- Excel transform does not evaluate formulas or run macros
- Workbook parse is capped (8 MiB file, 32 MiB declared uncompressed, 512 package entries, 32 sheets, 2000 rows, 50 columns, 20000 cells, 1,000,000 characters of cell text)

## Non-goals (v1)

- Large-file resumable upload sessions (>4 MiB)
- Word and PowerPoint text extraction
- Legacy BIFF `.xls` and `.xlsb` cell parsing
- Formula calculation or macro execution
- Exchange / Outlook mail (use sibling `outlook-mcp` and a separate Azure app)
