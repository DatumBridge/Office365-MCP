# list_files

List files and folders in OneDrive or SharePoint.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `drive_type` | no | str |
| `site_hostname` | no | Optional[str] |
| `site_path` | no | Optional[str] |
| `site_id` | no | Optional[str] |
| `folder_id` | no | Parent folder item ID |
| `folder_path` | no | Parent folder path relative to drive root |
| `page_size` | no | Max items (1-200) |
| `skip_token` | no | Pagination token |
| `file_extension` | no | Filter by extension, e.g. pdf, docx, xlsx, pptx |

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
  "files": [],
  "total_count": "example",
  "next_skip_token": "example"
}
```
