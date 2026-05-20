# DeepFind — Progress Log

Development journal tracking milestones, decisions, and notes.

---

## 2026-05-19 — Step 11: Auto-Tagging System

### What Was Done

**Backend — Tag Generation:**
- `engine/ai/tag_generator.py` — `generate_tags(name, path, ext, text)`: Uses simple rules (extension mapping, directory path splitting, keyword dictionaries on name/text) to generate comma-separated normalized tags. No AI or cloud APIs used.

**Backend — Tagging Manager & DB:**
- `engine/indexer/tagging_manager.py` — Background worker that fetches untagged files (or all if forced) and generates tags.
- `engine/database/repositories.py` — Added `update_tags()`, `get_files_for_tagging()`, and `get_tagging_summary()`.
- FTS index (`files_fts`) stays automatically in sync due to existing `files_au` trigger on UPDATE.

**Backend — Search Integration:**
- `engine/search/filename_search.py` — Added `tags` to SELECT, LIKE clause, and score (+50 for tag match).
- `engine/search/fulltext_search.py` — Added `tags` to SELECT and heuristic `matched_reasons` ("Tag matched query").

**Backend — API:**
- `engine/api/routes/tags.py` — Added `POST /tags/generate`, `GET /tags/status`, `GET /tags/summary`. Registered in `server.py`.

**Frontend:**
- `app/frontend/src/services/api.js` — Added tagging API calls.
- `app/frontend/src/components/TaggingPanel/TaggingPanel.jsx` & `.css` — New dashboard panel with live progress pulsing, DB stats, and top tags.
- `app/frontend/src/App.jsx` — Added `TaggingPanel` and updated CTA / feature card.
- `app/frontend/src/components/SearchResults/SearchResults.jsx` & `.css` — Added parsing and sleek purple chip rendering for tags (max 5 with a "+N more" badge).

### Next Step
→ **Step 12:** Search History & Recent Files — Store user queries locally and build a "Start/Home" page that displays recent searches and recently modified files.

---

## 2026-05-19 — Step 10: SQLite FTS5 Full-Text Content Search

### What Was Done

**Backend — FTS5 Search:**
- `engine/search/fulltext_search.py` — `search_content()`: FTS5 query builder, result ranking, snippet extraction, fallback on FTS parse errors; `rebuild_fts_index()`: clears + repopulates `files_fts` table; `check_has_extracted_content()` for UI hints

**Backend — Hybrid Search:**
- `engine/search/hybrid_search.py` — `unified_search()`: dispatches to metadata / content / all modes; merges by `file_id`, scores with formula `meta*0.45 + content*0.45 + recency*0.10`

**Backend — API:**
- `engine/api/routes/search.py` — extended `GET /search` with `type` query param (`all` | `metadata` | `content`); response includes `has_extracted_content`, `no_content_warning`; added `POST /search/rebuild-fts` developer endpoint

**Frontend:**
- `app/frontend/src/services/api.js` — `searchFiles()` now accepts `searchType` option
- `app/frontend/src/components/SearchBar/SearchBar.jsx` — 3-mode pill selector (All / Name·Path / Content); `onSearch(query, mode)` signature; adaptive placeholder per mode
- `app/frontend/src/components/SearchBar/SearchBar.css` — pill group, active accent gradient, hover states
- `app/frontend/src/components/SearchResults/SearchResults.jsx` — `MatchTypeBadge` (Name match / Content match / Hybrid match); content snippet display; no-content-yet warning empty state; mode badge in header; no-content banner when extracted=0
- `app/frontend/src/components/SearchResults/SearchResults.css` — badge styles, snippet styling (blue left border), result-card accent variants by match type
- `app/frontend/src/App.jsx` — added `searchMode`, `noContentWarning`, `hasExtractedContent` state; wired to SearchBar + SearchResults; updated Content Search feature card to active; updated CTA + footer to Step 10

### Search Modes
| Mode | Searches | Returns |
|------|----------|---------|
| `metadata` | filename, path, extension (SQL LIKE) | Name match badge |
| `content` | extracted_text via FTS5 BM25 | Content match badge + snippet |
| `all` | both, merged + hybrid scored | Hybrid/Name/Content badges |

### Hybrid Scoring
```
score = meta_score × 0.45 + content_score × 0.45 + recency_score × 0.10
recency: linear decay 0→1 over 30 days
```

### API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/search?q=&type=all&limit=50&offset=0` | Unified search |
| `GET` | `/search?q=&type=metadata` | Name/path only |
| `GET` | `/search?q=&type=content` | FTS5 content only |
| `POST` | `/search/rebuild-fts` | Rebuild FTS index (dev only) |

### FTS5 Notes
- `files_fts` is already kept in sync by triggers on `files` INSERT/UPDATE/DELETE
- `rebuild_fts_index()` safely re-syncs if triggers fall behind
- FTS queries are phrase-quoted to avoid injection; single-word fallback on parse error
- Snippets are 250 chars centred on first keyword match

### Next Step
→ **Step 11:** Auto-Tagging — generate comma-separated tags per file from filename/path/extension heuristics and populate `files.tags` for tag-based filtering in search

---

## 2026-05-19 — Step 9: Text Content Extraction

### What Was Done

**Backend — Extractors:**
- `engine/extractors/base_extractor.py` — `BaseExtractor` ABC with shared `clean_text()`, 100K char cap, null-byte removal, line normalization; `ExtractorError` raised on failure
- `engine/extractors/text_extractor.py` — `TextExtractor`: reads plain text/code files with multi-encoding fallback (utf-8 → utf-8-sig → latin-1 → cp1252 → utf-8/replace)
- `engine/extractors/pdf_extractor.py` — `PdfExtractor`: uses `pypdf`; handles password-protected PDFs and per-page errors gracefully
- `engine/extractors/docx_extractor.py` — `DocxExtractor`: uses `python-docx`; extracts paragraphs + table cells
- `engine/extractors/extractor_dispatcher.py` — routes by extension; `chunk_text()` splits into 400-word chunks (max 20 per file)
- `engine/extractors/__init__.py` — exports `extract_file`, `chunk_text`, `ExtractorError`

**Backend — Extraction Manager:**
- `engine/indexer/extraction_manager.py` — background threading worker (mirrors `index_manager.py`); skips `status='missing'` and files >25 MB; marks `content_extracted`, `extraction_failed`, or `content_skipped_large_file`; thread-safe state via lock

**Backend — API:**
- `engine/api/routes/extract.py` — `POST /extract/start`, `GET /extract/status`, `GET /extract/summary`; duplicate-run prevention
- `engine/api/server.py` — registered `/extract` router

**Backend — Database:**
- `engine/database/repositories.py` — implemented `FilesRepository.update_extracted_text()`, `FilesRepository.get_files_for_extraction()`; added `ChunksRepository` (clear/insert/count); added `get_extraction_summary()` module function
- `engine/config.py` — expanded `SUPPORTED_TEXT_EXTENSIONS` with `.c .cpp .cs .go .rs .json .xml`
- `engine/requirements.txt` — added `pypdf==5.5.0`, `python-docx==1.1.2`

**Frontend:**
- `app/frontend/src/components/ExtractionPanel/ExtractionPanel.jsx` — start button, live status bar, 5-counter stats grid, completion summary, persistent DB summary
- `app/frontend/src/components/ExtractionPanel/ExtractionPanel.css` — consistent with IndexingPanel visual language
- `app/frontend/src/services/api.js` — `startExtraction()`, `getExtractStatus()`, `getExtractSummary()`
- `app/frontend/src/App.jsx` — added `ExtractionPanel` between IndexingPanel and feature cards; updated footer to Step 9

### Supported File Types (Step 9)
| Category | Extensions |
|----------|-----------|
| Plain text | .txt .md .csv .json .xml |
| Code | .py .js .jsx .ts .tsx .php .java .html .css .sql .c .cpp .cs .go .rs |
| Documents | .pdf .docx |

### File Status Flow
```
metadata_indexed → content_extracted     (success)
metadata_indexed → extraction_failed     (error)
metadata_indexed → content_skipped_large_file  (>25 MB)
```

### API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/extract/start` | Start background extraction |
| `GET` | `/extract/status` | Live progress counters |
| `GET` | `/extract/summary` | DB totals by status + chunk count |

### What Works Now
- Click "Extract Text Content" → background extraction starts
- Live counters: checked, extracted, chunks, skipped, failed, current path
- Text stored in `files.extracted_text`; chunks stored in `file_chunks`
- Graceful error handling: corrupted PDFs, permission denied, encoding failures, missing files
- Search behavior unchanged — still filename/path/extension only (Step 10 adds content search)

### Next Step
→ **Step 10:** FTS5 full-text content search — populate `files_fts` from `extracted_text` and add content search to the `/search` endpoint

---

## 2026-05-19 — Step 8: Filename, Path & Extension Search

### What Was Done

**Backend (already scaffolded, now complete):**
- `engine/search/filename_search.py` — SQLite LIKE-based search with 5-tier ranking (exact match → starts with → contains → extension → path); returns `matched_reasons` + `size_human`; excludes `status = 'missing'`; uses parameterized queries with `LIMIT`/`OFFSET`
- `engine/api/routes/search.py` — `GET /search?q=&limit=&offset=` endpoint; returns standardized `{status, query, total, count, limit, offset, results}` response
- `engine/api/server.py` — search router already registered (Step 7 scaffolding)
- `engine/api/routes/` — `search.py` already imported

**Frontend (new/updated):**
- Created `app/frontend/src/components/SearchResults/SearchResults.jsx` — renders 4 states: `loading`, `error`, `empty`, `results`; per-card: filename, path, ext badge with colour-coded type, size, modified date, match reason, relevance %; Open/Folder actions (placeholder)
- Created `app/frontend/src/components/SearchResults/SearchResults.css` — full component styles with coloured left-border accent on hover
- Updated `app/frontend/src/App.jsx` — search state machine (`idle|loading|results|empty|error`), `handleSearch` / `handleClear` callbacks wired to `<SearchBar>`, `<SearchResults>` rendered below search bar; FolderManager/IndexingPanel hidden during active search
- Updated `app/frontend/src/styles/App.css` — `feature-card--active` and `feature-step--active` styles to highlight completed steps
- `app/frontend/src/services/api.js` — `searchFiles()` already added in Step 7 scaffolding; no changes needed

### Search Ranking (Step 8)
| Score | Condition |
|-------|-----------|
| 100 | Exact filename match |
| 85 | Filename starts with query |
| 70 | Filename contains query |
| 55 | Extension exact match |
| 40 | Path contains query |

### API Endpoint
```
GET http://127.0.0.1:8765/search?q=pdf&limit=50&offset=0
```

### What Works Now
- Type `pdf`, `docx`, `cv`, `screenshot`, `.php`, `assignment` → ranked result cards appear
- Clean empty state when no results
- Safe error state when engine is offline
- No disk scanning during search — SQLite only
- `status = 'missing'` files excluded from results

### Next Step
→ **Step 9:** Text content extraction (PDFs, DOCX, TXT, code files) — populates `file_chunks` table

---

## 2026-05-19 — Step 6: Automatic Folder & Drive Discovery

### What Was Done
- Created `engine/scanner/discovery.py` — detects common folders via `Path.home()`, drives via A-Z letter check; `SCAN_EXCLUSIONS` documented for Step 7
- Updated `engine/database/db.py` — added `_run_migrations()`: adds `source_type TEXT DEFAULT 'manual'` to existing DBs
- Updated `engine/database/repositories.py` — `FoldersRepository` fully implemented: `add(source_type, is_active)`, `list_all()`, `toggle()`, `set_active()`, `count_by_path()`
- Rewrote `engine/api/routes/folders.py` — 6 endpoints (static routes registered before dynamic to avoid conflicts)
- Updated `app/frontend/src/services/api.js` — `discoverFolders`, `initializeDefaults`, `getAllFolders`, `toggleFolder` added
- Rewrote `app/frontend/src/components/FolderManager/FolderManager.jsx` — discovery setup flow, grouped sources, CSS toggle switches
- Rewrote `app/frontend/src/components/FolderManager/FolderManager.css` — setup prompt, preview chips, folder rows, toggle switch

### Verified (on LENOVO machine)
| Item | Result |
|------|--------|
| `GET /folders/discover` | 4 common folders + 3 drives (C:, D:, E:) detected |
| Desktop/Pictures missing | Correct — redirected to OneDrive on this machine |
| `POST /initialize-defaults` | 7 items saved: Documents ✓, Downloads ✓, Videos ✗, Music ✗, C:/ ✗, D:/ ✗, E:/ ✗ |
| `GET /folders` | Returns all 7 with correct active/inactive states |
| Default active state | Documents, Downloads = active; Videos, Music, all drives = inactive |
| DB migration | `source_type` column added to existing DB without data loss |

### API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/folders/discover` | Detect folders/drives (no DB writes) |
| `POST` | `/folders/initialize-defaults` | Save detected defaults to DB |
| `GET` | `/folders` | List all (active + inactive) |
| `POST` | `/folders` | Add custom folder manually |
| `PATCH` | `/folders/{id}/toggle` | Flip active/inactive |
| `DELETE` | `/folders/{id}` | Soft-delete |

### Next Step
→ **Step 7:** File system scanner — walk indexed folders, collect file metadata, store in `files` table

---

## 2026-05-19 — Step 5: SQLite Database Schema

### What Was Done
- Created `engine/config.py` — central config (paths, limits, constants)
- Created `engine/database/schema.sql` — full schema: 7 tables + FTS5 triggers + default settings
- Created `engine/database/db.py` — `init_db()`, WAL-mode `get_connection()`, `get_db_info()`
- Created `engine/database/repositories.py` — SettingsRepository (full), Folders/Files/SearchHistory (stubs)
- Created `engine/database/__init__.py` — package exports
- Created `engine/api/routes/db.py` — `GET /db/status` endpoint
- Updated `engine/api/server.py` — FastAPI lifespan calls `init_db()` on startup; db router registered
- Updated `engine/main.py` — added DB Status URL to startup banner; `database/` added to reload_dirs

### Verified
- `engine/data/deepfind.db` created (88 KB) on first startup
- `GET /db/status` returns `{"status":"ok","database":"connected","tables_created":true,...}`
- All 7 tables confirmed: files, indexed_folders, files_fts, file_chunks, embeddings, search_history, settings
- Default settings inserted: app_version, max_file_size_mb, theme, etc.
- `GET /health` still works (no regression)

### Database Tables
| Table | Purpose | Implemented |
|-------|---------|-------------|
| `files` | Indexed file metadata | Schema ✅ · Data Step 7 |
| `indexed_folders` | User-selected folders | Schema ✅ · Data Step 6 |
| `files_fts` | FTS5 full-text index | Schema ✅ · Data Step 10 |
| `file_chunks` | Semantic chunk mapping | Schema ✅ · Data Step 15 |
| `embeddings` | FAISS vector mapping | Schema ✅ · Data Step 15 |
| `search_history` | Local search log | Schema ✅ · Data Step 8 |
| `settings` | App preferences | Schema ✅ · Defaults inserted |

### Next Step
→ **Step 6:** Folder selection — let the user pick folders to index (Electron dialog + FastAPI endpoint)

---

## 2026-05-19 — Step 4: Frontend ↔ Backend Connection

### What Was Done
- Created `app/frontend/src/services/api.js` — central API layer with `fetchWithTimeout` and `checkHealth()`
- Created `app/frontend/src/hooks/useEngineStatus.js` — polling hook (15s interval, 5s timeout, never throws)
- Updated `app/frontend/src/App.jsx` — wired hook, replaced hardcoded badge with `EngineStatusBadge` component
- Updated `app/frontend/src/styles/App.css` — three-state badge styles (checking/online/offline) with spinning dot animation

### Verified Behavior
| Backend state | Badge display |
|---------------|--------------|
| Starting up | Grey spinner · "Checking engine…" |
| Running | 🟢 Green · "Engine running · v0.1.0" |
| Stopped | 🟡 Amber · "Backend not connected · start engine to enable search" |

### How to Run (both together)
```powershell
# Terminal 1 — backend
cd engine && .venv\Scripts\activate && python main.py

# Terminal 2 — frontend
cd app && npm run dev
```

### Next Step
→ **Step 5:** Setup SQLite database schema

---

## 2026-05-19 — Step 3: Python FastAPI Backend

### What Was Done
- Created `engine/requirements.txt` — fastapi, uvicorn[standard] (future deps commented out)
- Created `engine/.venv` — Python virtual environment
- Installed 18 packages: fastapi 0.115.12, uvicorn 0.34.2, starlette, pydantic, etc.
- Created `engine/api/server.py` — FastAPI app with CORS middleware for Electron origins
- Created `engine/api/routes/health.py` — `/health` GET endpoint
- Created `engine/api/routes/__init__.py` — routes package
- Created `engine/main.py` — entry point with startup banner and uvicorn runner
- Created `scripts/run_engine.bat` — one-click Windows setup + start script
- Verified: `GET http://127.0.0.1:8765/health` returns `200 OK` with correct JSON

### Health Response (verified)
```json
{
  "status": "ok",
  "service": "DeepFind Engine",
  "version": "0.1.0",
  "backend": "FastAPI",
  "timestamp": "2026-05-19T10:26:49.199490+00:00"
}
```

### How to Run
```powershell
cd engine
.venv\Scripts\activate
python main.py
```

### Next Step
→ **Step 4:** Connect the React frontend to the backend — poll `/health` and display backend status in the UI

---

## 2026-05-19 — Step 2: Electron + React Desktop App

### What Was Done
- Created `app/package.json` with Electron, Vite, React, concurrently, wait-on
- Created `app/vite.config.js` pointing Vite root to `./frontend`
- Created `app/electron/main.js` — window creation, dev/prod mode detection, lifecycle
- Created `app/electron/preload.js` — secure contextBridge API stub
- Created `app/frontend/index.html` — Vite HTML entry with Inter font
- Created `app/frontend/src/main.jsx` — React entry point
- Created `app/frontend/src/App.jsx` — Welcome screen with hero, search, feature cards, footer
- Created `app/frontend/src/components/SearchBar/` — Placeholder search bar component
- Created `app/frontend/src/styles/index.css` — Global design system (CSS tokens, animations)
- Created `app/frontend/src/styles/App.css` — App layout with dark theme, glow orbs, dot grid
- Ran `npm install` — 188 packages installed
- Verified app launches with `npm run dev` — window opens, UI renders correctly

### How to Run
```powershell
cd app
npm install   # first time only
npm run dev
```

### Next Step
→ **Step 3:** Setup Python FastAPI backend with health check endpoint

---

## 2026-05-19 — Step 1: Project Structure Created

### What Was Done
- Created monorepo folder structure
- Created `README.md` with project overview and tech stack
- Created `.gitignore` for Python, Node, Electron, SQLite, FAISS, and model files
- Created `agent.md` for AI agent reference
- Created placeholder `README.md` files in all engine modules with planned responsibilities
- Created `__init__.py` package stubs for all Python modules
- Created `docs/`, `screenshots/`, `tests/`, `scripts/` directories

### Folder Structure
```
deepfind/
├── app/
│   ├── electron/      ← Electron main process (Step 2)
│   └── frontend/      ← React UI (Step 2)
├── engine/
│   ├── api/           ← FastAPI routes (Step 3)
│   ├── scanner/       ← File scanner (Step 6)
│   ├── extractors/    ← Text extraction (Step 9)
│   ├── database/      ← SQLite schema (Step 5)
│   ├── search/        ← Search logic (Step 8)
│   ├── ai/            ← Semantic search (Step 15 / V2)
│   ├── indexer/       ← Indexing pipeline (Step 7)
│   └── utils/         ← Shared utilities
├── docs/
├── screenshots/
├── tests/
├── scripts/
└── README.md
```

### Next Step
→ **Step 2:** Setup Electron + React (working desktop window, no backend yet)

---
