# System Overview — Office 365 MCP

## Components

| Component | Role |
|-----------|------|
| `app/mcp_server.py` | FastMCP tool definitions + HTTP app |
| `app/services/graph_service.py` | Microsoft Graph HTTP client |
| `app/services/file_types.py` | PDF/Office MIME validation |
| `app/oauth_routes.py` | Optional local OAuth connect flow |

- Files: OneDrive / SharePoint via Microsoft Graph
- Chat: Teams chats and channel messages (same delegated token; extra consent)

## Data flow

1. Agent invokes MCP tool with OAuth credentials.
2. `GraphService` attaches bearer token (refreshes on 401).
3. Graph returns driveItem metadata or file bytes.
4. Binary content encoded as base64 in MCP responses.

## External dependencies

- Microsoft identity platform (OAuth 2.0)
- Microsoft Graph `https://graph.microsoft.com/v1.0`

## Deployment

- Container: `Dockerfile` → uvicorn on port 8000
- Health: `GET /health`
- Optional k8s manifest: `k8s/deployment.yaml`
