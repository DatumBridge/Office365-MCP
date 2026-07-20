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
| read_file | GET metadata + /content | No |
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
- Treat downloaded file content as untrusted data

## Non-goals (v1)

- Large-file resumable upload sessions (>4 MiB)
- Server-side Office text extraction
- Exchange / Outlook / Teams APIs
