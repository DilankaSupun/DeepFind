# engine/api/

This module will contain the **FastAPI server and route definitions**.

## Planned Files (Step 3)

- `server.py` — FastAPI app instance and startup config
- `routes/health.py` — Health check endpoint
- `routes/index.py` — Indexing endpoints (start, status, cancel)
- `routes/search.py` — Search endpoints (keyword, content, semantic)
- `routes/folders.py` — Indexed folder management
- `routes/files.py` — File detail and file action endpoints
- `routes/settings.py` — App settings endpoints

## API Design Rules

- Lightweight payloads — never return full extracted text in search results
- Return top 20–50 results per search
- File details loaded separately when user opens detail panel
- All processing is local — no external calls

> ⏳ Not implemented yet — awaiting Step 3.
