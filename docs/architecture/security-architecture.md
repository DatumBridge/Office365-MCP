# Security architecture

## Access

`read_file` uses the delegated Graph token already required for OneDrive or SharePoint. Excel transform does not add a scope. A caller who cannot download the file cannot transform it. Non-Excel files are rejected before the bytes are downloaded when `excel_format` is set.

## Workbook bytes

Cell text is untrusted data. It is not executed, not logged, and not treated as tool instructions. Formulas are copied out as text. Macros are not loaded.

Before `openpyxl` parses a package the server checks:

- metadata `size` above 8 MiB is rejected before `GET /content`
- the content body is streamed and stopped at 8 MiB
- ZIP local header (`PK`)
- at most 512 entries
- only store and deflate members; inflated bytes are counted up to 32 MiB and the package openpyxl sees is that capped copy
- entry names are not absolute and do not contain `..`
- `EncryptionInfo` / `EncryptedPackage` rejected
- `xl/workbook.xml` is present

`openpyxl` parses worksheet XML through `defusedxml`. The server refuses to transform a workbook when that parser is not active. Legacy OLE `.xls` is rejected. A malformed package returns `Could not read Excel workbook` without the parser's internal text.

Row and column caps scan cells past the limit, including cells after a blank row or column. Any value past the cap sets `truncated=true` and is omitted. The serialized JSON or XML, including repeated `header_row` names, is kept within 1,000,000 characters.

## Output bounds

At most 32 sheets, 2000 rows and 50 columns per sheet, 20000 non-empty cells, 8000 characters per cell, and 1,000,000 characters of serialized JSON or XML. Overflow sets `truncated=true` instead of returning a silent partial read. XML text and attributes are escaped. Characters that are illegal in XML 1.0 are stripped from cell text.

## Logs

Tool logs record `excel_format` as `json`, `xml`, or `raw`. They do not record cell values, tokens, or file bytes.

## Residual

Cell text can still contain instructions aimed at a model. Callers must treat the document as data. A raw `read_file` without `excel_format` still returns the original bytes, including a macro part, and does not run them.
