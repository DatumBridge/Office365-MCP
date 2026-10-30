# Business rules

## File reads

- `read_file` returns metadata plus content when `include_content` is true (the default).
- PDF, Word, PowerPoint, and raw Excel stay base64 unless an Excel transform is requested.
- `excel_format` accepts only `json` or `xml`.
- `excel_format` requires `include_content=true`.
- `excel_format` applies to Excel workbooks (`.xlsx`, `.xlsm`, or a `.xls` name whose bytes are an Open XML package). Other types are a validation error and are not downloaded.
- Legacy BIFF `.xls`, `.xlsb`, and encrypted workbooks cannot be transformed. The caller saves a `.xlsx` copy or reads the raw base64 without `excel_format`.

## Excel cell values

- Numbers, booleans, strings, and ISO-8601 dates are returned as values.
- A formula is returned as its formula text. The server does not calculate it.
- Blank rows are omitted. Row numbers in the result are the worksheet row numbers.
- `header_row=true` uses the first non-empty row as column names. Duplicate names get a numeric suffix (`Name`, `Name_2`). The name `excel_row` is reserved.
- `sheet_name` selects one sheet. An unknown name is an error that lists sheet names. A case-insensitive match is used only when it is unique.
- When a cap is hit (rows, columns, cells, or 1,000,000 characters of cell text), the response is marked `truncated=true`.

## Writes

`create_file` and `delete_file` still require `confirm=true`. Excel transform does not write to the drive.
