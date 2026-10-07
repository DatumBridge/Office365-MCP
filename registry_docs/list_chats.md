# list_chats

List Microsoft Teams chats for the signed-in user.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `page_size` | no | Max chats (1-50) |
| `skip_token` | no | Pagination token |

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
  "chats": [],
  "next_skip_token": "example"
}
```
