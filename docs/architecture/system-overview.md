# System Overview — Office 365 MCP

## Components

| Component | Role |
|-----------|------|
| `app/mcp_server.py` | FastMCP tool definitions + HTTP app |
| `app/services/graph_service.py` | Microsoft Graph HTTP client |
| `app/services/excel_workbook.py` | Excel `.xlsx`/`.xlsm` cell transform to JSON or XML |
| `app/services/file_types.py` | PDF/Office MIME validation |
| `app/oauth_routes.py` | Optional local OAuth connect flow |

- Files: OneDrive / SharePoint via Microsoft Graph
- Chat: Teams chats and channel messages (same delegated token; extra consent)

## Data flow

1. Agent invokes MCP tool with OAuth credentials.
2. `GraphService` attaches bearer token (refreshes on 401).
3. Graph returns driveItem metadata or file bytes.
4. Binary content is encoded as base64, except when `read_file` is asked to transform an Excel workbook.
5. For `excel_format=json` or `excel_format=xml`, the server checks the package limits, parses cells in memory, and returns JSON or XML. Formulas are not evaluated.

## Why Excel is parsed here

Agents need cell values, not a base64 blob. Parsing stays inside `read_file` so OneDrive and SharePoint reads keep one tool. The transform is local: Graph is only used to download the bytes the caller is already allowed to read.

## External dependencies

- Microsoft identity platform (OAuth 2.0)
- Microsoft Graph `https://graph.microsoft.com/v1.0`
- `openpyxl` reads `.xlsx` and `.xlsm` through `defusedxml`. Store and deflate ZIP members only. Inflated bytes are capped at 32 MiB.

## Deployment

- Container: `Dockerfile` → uvicorn on port 8000
- Health: `GET /health`
- Optional k8s manifest: `k8s/deployment.yaml`
