# delete_file

Delete a file from OneDrive or SharePoint. Requires confirm=true.

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
| `confirm` | no | Must be true to delete (permanent side effect) |

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
  "file_path": "example",
  "message": "example"
}
```
