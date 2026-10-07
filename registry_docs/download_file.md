# download_file

Download a file from OneDrive or SharePoint.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `drive_type` | no | str |
| `site_hostname` | no | Optional[str] |
| `site_path` | no | Optional[str] |
| `site_id` | no | Optional[str] |
| `item_id` | no | Optional[str] |
| `file_path` | no | Optional[str] |
| `as_text` | no | Return plain text for text/* MIME types; else base64 |

## Cases

### Typical call

Input:

```json
{}
```

Output:

```json
{
  "success": true,
  "item_id": "example-id",
  "file_name": "notes.txt",
  "content_base64": "example",
  "content_text": "example",
  "mime_type": "example",
  "size_bytes": []
}
```
