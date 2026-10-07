# list_joined_teams

List Microsoft Teams the signed-in user has joined.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| — | — | This call takes no model arguments. |

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
  "teams": []
}
```
