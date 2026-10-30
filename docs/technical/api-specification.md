# API specification

Office 365 MCP tools are MCP tools, not REST resources. The HTTP app exposes `POST /mcp/` and `GET /health`.

The planner contract for each tool is `registry_docs/<tool>.md`, copied onto `x-datumbridge-docs` at bind time. Those guides follow the MCP tool template: audience (`external` / `required`), agent rules, when to call, parameters (name, required, type, sample, related tool, meaning), success fields, error codes, and cases. Deep fills arguments from that text. A schema change is not visible until the image is deployed and Tool Registry Setup runs again.

List tools return `next_skip_token`. They do not return `paging` or `total_page`.

## read_file

Reads a OneDrive or SharePoint drive item.

| Field | Required | Notes |
|---|---|---|
| `credentials_path` or `credentials_json` | yes | Delegated OAuth token. The gateway injects `credentials_json` |
| `item_id` or `file_path` | yes | Which item |
| `drive_type` | no | `onedrive` or `sharepoint` |
| `excel_format` | no | `json` or `xml` for Excel cell values |
| `sheet_name` | no | One worksheet |
| `header_row` | no | Column names from the first non-empty row |
| `include_content` | no | Default true |
| `as_text` | no | Text MIME types only. Not used for Excel transform |

### Success

| Field | When |
|---|---|
| `metadata` | Always on success |
| `content_base64` | Raw file. Absent when `excel_format` is set |
| `content_json` | `excel_format=json` |
| `content_xml` | `excel_format=xml` |
| `content_text` | JSON text, XML text, or a text MIME body |
| `excel_format` | `json` or `xml` when a transform ran |
| `truncated` | True when a workbook cap was hit |
| `size_bytes` | Raw download size |
| `message` | `File read`, `Metadata only`, or `Excel workbook as json|xml` |

### Errors

| error_code | When | retryable |
|---|---|---|
| `CREDENTIALS_REQUIRED` | No token | false |
| `VALIDATION_ERROR` | Missing path, bad `excel_format`, non-Excel transform, unreadable workbook, unknown sheet | false |
| `AUTH_ERROR` | Token rejected | true |
| `PERMISSION_DENIED` | Graph 403 | false |
| `NOT_FOUND` | Graph 404 | false |
| `RATE_LIMIT` | Graph 429 | true |

Authentication is the bearer token inside the credential JSON. No token is returned in the tool result.
