# Use cases

## Agent reads an orders workbook

A workflow has an `.xlsx` on OneDrive. `read_file` with `excel_format=json` and `header_row=true` returns one object per data row so the agent can filter or summarize without decoding base64.

## Agent needs a single sheet as XML

`excel_format=xml` and `sheet_name` return one worksheet. Downstream steps that already accept XML can consume `content_xml`.

## Caller still wants the original file

Omit `excel_format`. `download_file` is unchanged and always returns the raw bytes.
