# list_team_channels

List channels in a team.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `team_id` | yes | Team id from list_joined_teams |

## Cases

### Typical call

Input:

```json
{
  "team_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "channels": []
}
```

### Missing `team_id`

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
    "error_message": "team_id is required",
    "retryable": false
  }
}
```
