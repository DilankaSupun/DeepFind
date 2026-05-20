# engine/extractors/

This module will contain **text extraction logic** for supported file types.

## Planned Files (Step 9)

- `extractor.py` — Main extractor dispatcher (routes to correct reader)
- `pdf_extractor.py` — PDF text extraction using pypdf
- `docx_extractor.py` — Word document extraction using python-docx
- `text_extractor.py` — Plain text files (.txt, .md, .csv)
- `code_extractor.py` — Code files (.py, .js, .jsx, .ts, .tsx, .php, .java, .html, .css, .sql)
- `ocr_extractor.py` — OCR using Tesseract (V4 only — not implemented in V1)

## Supported File Types (V1)

```
.txt  .md   .csv
.py   .js   .jsx  .ts  .tsx
.php  .java .html .css .sql
.pdf  .docx
```

## Extraction Rules

- Skip files > 25 MB
- Handle extraction errors per file — never crash indexer
- Return empty string if extraction fails
- Store extracted text in SQLite `files.extracted_text`

> ⏳ Not implemented yet — awaiting Step 9.
