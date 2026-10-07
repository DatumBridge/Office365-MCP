# list_channel_messages

List recent messages in a Teams channel.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `team_id` | yes | Team id |
| `channel_id` | yes | Channel id |
| `page_size` | no | Max messages (1-50) |

## Cases

### Typical call

Input:

```json
{
  "team_id": "example-id",
  "channel_id": "C00000000"
}
```

Output:

```json
{
  "success": true,
  "messages": []
}
```

### Missing `team_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "channel_id": "C00000000"
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "team_id is required",
    "retryable": false
  }
}
```
