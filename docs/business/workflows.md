# Workflows

## Read an Excel file as JSON or XML

1. The caller passes `item_id` or `file_path`, plus `excel_format` of `json` or `xml`.
2. Optional: `sheet_name` and `header_row`.
3. The server loads metadata. If the item is not an Excel workbook, or metadata `size` is above 8 MiB, it returns `VALIDATION_ERROR` and does not download the bytes.
4. The server downloads `/content` with the delegated token and stops reading if the body passes 8 MiB.
5. Package limits are checked. Encrypted, legacy `.xls`, and unsafe ZIP entries fail closed.
6. Cells are parsed in memory. The response includes `content_json` or `content_xml`, and the same payload in `content_text`.
7. `content_base64` is omitted for that response.

## Read any other file

Omit `excel_format`. The server returns metadata and `content_base64` (or `content_text` when `as_text` is true and the MIME type is text).

## Failure

Validation errors use `error_code=VALIDATION_ERROR` and `retryable=false`. Graph auth, permission, not-found, and rate-limit errors keep their existing codes.
