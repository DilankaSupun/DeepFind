# scripts/maintenance/

Live regression tests and maintenance scripts for DeepFind.

These scripts query the **real production database** and/or the **live FastAPI server**.
They are not run in automated CI. Use them to verify the system after significant changes.

## Requirements

- Production `deepfind.db` must be populated with indexed files.
- For server-based tests (`regression_tests.py`): the FastAPI backend must be running on port 8765.
- For direct Python tests: no server needed, but the `.venv` must be active.

## Usage

```
cd <repo_root>
engine\.venv\Scripts\activate

# Direct Python tests (no server needed):
python scripts/maintenance/test_regression_final.py
python scripts/maintenance/test_regression_direct.py

# Live server tests (requires: python engine/main.py in another terminal):
python scripts/maintenance/regression_tests.py
```

## Scripts

| Script | Purpose | Requires Server |
|---|---|---|
| `test_regression_final.py` | Verifies all 9 canonical queries return results with timing | No |
| `test_regression_direct.py` | Comprehensive regression: 9 queries, timing, filter validation | No |
| `regression_tests.py` | HTTP-based regression via live API, includes timing thresholds | Yes (port 8765) |

## Canonical Queries

```
dashboard.js        Exact filename
setup.exe           Exact executable
IGI                 App/folder name
report              Common stem
assignment          Common stem
movie.mp4           Exact filename+ext
pdfs in Ayya folder Structured: folder+ext filter
Buddhism and the History of Nursing   FTS fast path
payment gateway setup                 Semantic fallback
videos in Downloads  Extension+folder filter
```
