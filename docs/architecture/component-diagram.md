# Component diagram

```mermaid
flowchart LR
  agent[MCP client]
  server[office365-mcp]
  graph[Microsoft Graph]
  drive[OneDrive or SharePoint]
  excel[excel_workbook]

  agent -->|tools/call| server
  server -->|bearer token| graph
  graph --> drive
  server -->|excel_format json or xml| excel
  excel -->|cell values| agent
```

`excel_workbook` runs only for `read_file` when `excel_format` is `json` or `xml`. It does not call Graph and does not write the workbook back.
