# send_chat_message

Send a message in a Teams chat. Requires confirm=true.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `chat_id` | yes | Teams chat id |
| `content` | yes | Plain-text message body |
| `confirm` | no | Must be true to send |
| `dry_run` | no | Validate without sending |

## Cases

### Typical call

Input:

```json
{
  "chat_id": "example-id",
  "content": "hello",
  "dry_run": true
}
```

Output:

```json
{
  "success": true,
  "id": "example-id",
  "chat_id": "example-id",
  "team_id": "example-id",
  "channel_id": "C00000000",
  "created": "example",
  "web_url": "https://example.com/page",
  "message": "example",
  "dry_run": false
}
```

### Missing `chat_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "content": "hello",
  "dry_run": true
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "chat_id is required",
    "retryable": false
  }
}
```

### Preview the write

Set `dry_run` to true. The tool returns the planned change and does not send it.

Input:

```json
{
  "chat_id": "example-id",
  "content": "hello",
  "dry_run": true
}
```

### Confirmed write

Set `confirm` to true. Omit `dry_run`.

Input:

```json
{
  "chat_id": "example-id",
  "content": "hello",
  "confirm": true
}
```

### Write without confirm or dry_run

Input:

```json
{
  "chat_id": "example-id",
  "content": "hello"
}
```

Output:

```json
{
  "success": false,
  "error_message": "confirm=true required for write tools (or dry_run=true to preview)"
}
```
