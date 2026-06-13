# scripts/diagnostics/

One-off diagnostic scripts used during development and debugging.

These scripts are **not automated tests**. They are manual debugging tools
that helped trace specific search issues. They write to stdout only.

## Usage

Run from the repo root:
```
cd <repo_root>
engine\.venv\Scripts\activate
python scripts/diagnostics/<script>.py
```

## Scripts

| Script | Purpose |
|---|---|
| `test_ayya.py` | Debug "pdfs in ayya folder" query via hybrid_search |
| `test_ayya_2.py` | Debug "pdfs in ayya folder" via filename_search |
| `test_ayya_3.py` | Debug "pdfs in ayya folder" full hybrid result inspection |
| `test_ayya_4.py` | Debug folder filter matching via filename_search |
| `test_ayya_5.py` | Debug score calculation per result |
| `test_parser.py` | Standalone query parser prototype (no engine imports) |
| `perf_report.py` | Quick DB stats + live server performance report |
| `perf_test.py` | Live server location-query test |

All scripts use file-relative `sys.path` insertion and can be run from any directory.
