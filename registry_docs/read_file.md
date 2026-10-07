# read_file

Read a file: metadata and optional content (base64 for PDF/Office binaries).

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
| `include_content` | no | If false, return metadata only |
| `as_text` | no | Return UTF-8 text when MIME is text/* (Office/PDF return base64) |

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
  "metadata": "example",
  "content_base64": "example",
  "content_text": "example",
  "size_bytes": [],
  "message": "example"
}
```
