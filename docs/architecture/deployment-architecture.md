# Deployment architecture

The server is a single container. `Dockerfile` installs `requirements_mcp.txt` (including `openpyxl`) and runs uvicorn on port 8000 as a non-root user.

- Health check: `GET /health`
- Remote gateway: `GET /register`
- MCP endpoint: `POST /mcp/`
- Optional Kubernetes manifest: `k8s/deployment.yaml` in namespace `mcp-tools`

Excel parsing uses process memory only. It does not add a volume, a database, or a second service. Rollback is the previous image. Callers that omit `excel_format` keep the previous base64 behavior.

Secrets (`OFFICE365_CLIENT_SECRET`, token JSON) stay in the environment or the credential vault. They are not written into tool responses.
