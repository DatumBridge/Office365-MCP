# create_folder

Create a folder in OneDrive or SharePoint.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `folder_name` | yes | New folder name |
| `drive_type` | no | str |
| `site_hostname` | no | Optional[str] |
| `site_path` | no | Optional[str] |
| `site_id` | no | Optional[str] |
| `parent_folder_id` | no | Optional[str] |
| `parent_folder_path` | no | Optional[str] |

## Cases

### Typical call

Input:

```json
{
  "folder_name": "example"
}
```

Output:

```json
{
  "success": true,
  "metadata": "example",
  "message": "example"
}
```

### Missing `folder_name`

The tool rejects the call and does not guess the missing value.

Input:

```json
{}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "folder_name is required",
    "retryable": false
  }
}
```
