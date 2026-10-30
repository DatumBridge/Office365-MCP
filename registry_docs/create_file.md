# create_file

Create/upload a PDF or Office document to OneDrive or SharePoint.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Agent rules

- Do not copy `content_base64` from this guide. A sample such as `"example"` is not a file.
- A new Word file comes from `Utilities MCP/create_docx`. Set `content_base64` to `{{thatStep.content_base64}}` and `file_name` to `{{thatStep.file_name}}`.
- A file already stored on the work item: set `file_name` to that name and leave `content_base64` empty. The runtime copies the stored bytes.
- Set `confirm` to true to upload. `dry_run` true only previews and does not store the file.
- `drive_type` is `onedrive` unless the user asked only for SharePoint. SharePoint also needs `site_id` or `site_hostname` plus `site_path`.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_name` | yes | File name with extension (.pdf, .docx, .xlsx, .pptx, etc.) |
| `content_base64` | yes | File bytes as base64 (max 4 MiB for simple upload). Use `{{step.content_base64}}` from `create_docx`, or leave empty when the work item already has that file. Do not copy a sample. |
| `drive_type` | no | str |
| `site_hostname` | no | Optional[str] |
| `site_path` | no | Optional[str] |
| `site_id` | no | Optional[str] |
| `parent_folder_id` | no | Parent folder item ID |
| `parent_folder_path` | no | Parent folder path, e.g. Documents/Reports |
| `mime_type` | no | MIME type (auto-detected from extension if omitted) |
| `conflict_behavior` | no | On name conflict: rename, replace, or fail |
| `confirm` | no | Must be true to upload (side effect). A call without `confirm` true does not store the file. |
| `dry_run` | no | Validate inputs without calling Microsoft Graph |

## Cases

### Typical call

`step_1` is `Utilities MCP/create_docx`. Do not replace the references with a sample string.

Input:

```json
{
  "file_name": "{{step_1.file_name}}",
  "content_base64": "{{step_1.content_base64}}",
  "drive_type": "onedrive",
  "confirm": true
}
```

Output:

```json
{
  "success": true,
  "metadata": "example",
  "message": "example",
  "dry_run": false
}
```

### Missing `file_name`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "content_base64": "example",
  "dry_run": true
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "file_name is required",
    "retryable": false
  }
}
```

### Preview the write

Set `dry_run` to true. The tool returns the planned change and does not send it.

Input:

```json
{
  "file_name": "notes.txt",
  "content_base64": "example",
  "dry_run": true
}
```

### Confirmed write

Set `confirm` to true. Omit `dry_run`.

Input:

```json
{
  "file_name": "{{step_1.file_name}}",
  "content_base64": "{{step_1.content_base64}}",
  "drive_type": "onedrive",
  "confirm": true
}
```

### Write without confirm or dry_run

Input:

```json
{
  "file_name": "notes.txt",
  "content_base64": "example"
}
```

Output:

```json
{
  "success": false,
  "error_message": "confirm=true required for write tools (or dry_run=true to preview)"
}
```
