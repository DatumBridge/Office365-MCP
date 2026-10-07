# get_file_metadata

Get metadata for a file or folder by item_id or file_path.

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
  "metadata": "example"
}
```
