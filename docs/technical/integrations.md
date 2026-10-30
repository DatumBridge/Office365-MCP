# Integrations

| System | Use |
|---|---|
| Microsoft identity platform | Delegated OAuth token refresh |
| Microsoft Graph `v1.0` | Drive item metadata and `/content` |
| OneDrive `/me/drive` | Default `drive_type=onedrive` |
| SharePoint `/sites/{id}/drive` | `drive_type=sharepoint` |
| `openpyxl` + `defusedxml` | Local read of `.xlsx` and `.xlsm` when `excel_format` is set |

Graph remains the only network integration for file bytes. `openpyxl` does not fetch links (`keep_links=false`) and is not asked to evaluate formulas (`data_only=false`).
