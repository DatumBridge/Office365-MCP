# Database design

This server does not own a database. Drive items stay in OneDrive or SharePoint. OAuth tokens are supplied per call and are not stored by the Excel transform.

`read_file` Excel parsing holds the workbook in memory for the duration of the call and discards it. There is no table, index, or migration for cell values.
