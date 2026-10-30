# Configuration

See `.env.example`. Excel transform has no new environment variable. Limits are constants in `app/services/excel_workbook.py`.

| Variable | Purpose |
|---|---|
| `PORT` | HTTP port, default 8000 |
| `OFFICE365_CLIENT_ID` / `OFFICE365_CLIENT_SECRET` | Azure app used to refresh tokens |
| `OFFICE365_TENANT_ID` | `common`, `organizations`, or a tenant id |
| `OAUTH_REDIRECT_URI` | Local OAuth callback |
| `OFFICE365_CREDENTIALS_DIR` | Jail for `credentials_path` |
| `OFFICE365_HTTP_TIMEOUT_SEC` | Graph HTTP timeout, default 60 |
| `OFFICE365_ENABLE_OAUTH_UI` | `1` enables the local `/test` UI |

`openpyxl` is installed from `requirements_mcp.txt`. No API key is required for the parser.
