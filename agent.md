# DeepFind — AI Agent Reference Guide

> **This file is the single reference document for the AI coding agent working on DeepFind.**
> Read this before every implementation step. Follow it strictly.

---

## 1. What Is DeepFind?

DeepFind is a **local-first desktop AI file search application**.

It helps users find files by:
- Filename, path, extension
- Extracted text content
- Auto-generated tags
- Natural language meaning (semantic search)
- Similar file detection

**One-line pitch:** Find files by what you remember about them — not just their name.

---

## 2. Core Agent Rules

| Rule | Detail |
|------|--------|
| Implement **only the current step** | Never build ahead without instruction |
| After each step: report files, how to run, how to test | Stop and wait for next instruction |
| No cloud APIs ever | All processing is local |
| No large LLMs | Use lightweight pre-trained models only |
| Search always uses indexes | Never scan files during live search |
| Keep it lightweight | CPU-friendly, low memory, background tasks |

---

## 3. Hard Requirements (Non-Negotiable)

### 3.1 Local-First
- No file uploads to any server
- No cloud AI APIs (no OpenAI, Gemini, Claude, etc.)
- No remote vector databases
- All data stays on the user's machine

### 3.2 Desktop App
- Built with **Electron** — not a website
- Final product is an installable desktop application

### 3.3 Lightweight
- No large LLMs
- No heavy background processes
- No scanning files during search
- Skip files > 25 MB for text extraction by default
- OCR disabled by default

### 3.4 Indexed Search Only
Search must only use:
- SQLite metadata index
- SQLite FTS5 full-text index
- FAISS semantic vector index (V2+)

---

## 4. Approved Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop shell | Electron |
| Frontend UI | React |
| Local backend | Python + FastAPI |
| Database | SQLite |
| Full-text search | SQLite FTS5 |
| Semantic search | FAISS + sentence-transformers/all-MiniLM-L6-v2 |
| Text extraction | pypdf, python-docx, plain text readers |
| File watching (V3) | watchdog |
| OCR (V4) | Tesseract |
| Packaging | Electron Builder |

### Technologies the Agent Must NOT Use
```
Cloud AI APIs, OpenAI, Gemini, Claude
Online vector databases
Large local LLMs (Llama, GPT-style chat models)
Image generation models
Cloud storage or sync
Tailwind CSS (use Vanilla CSS)
```

---

## 5. System Architecture

```
Electron Desktop Shell
        ↓
React Frontend (search bar, results, filters, file details, settings)
        ↓
Local API Bridge (HTTP to Python FastAPI)
        ↓
Python Search Engine
        ↓
Hybrid Search Layer
   ┌─────────────┬─────────────┬─────────────┐
   │ Filename    │ Full-text   │ Semantic    │
   │ Search      │ FTS5        │ FAISS       │
   └─────────────┴─────────────┴─────────────┘
        ↓
Ranking Engine
        ↓
Results with Match Explanation
        ↓
SQLite + FTS5 + FAISS (local storage)
```

**Key principle:** Index slowly in the background. Search instantly from indexes. AI is only a lightweight semantic layer.

---

## 6. Database Schema

### Main Tables

| Table | Key Fields |
|-------|-----------|
| `files` | id, path, name, extension, size, created_at, modified_at, last_indexed_at, content_hash, extracted_text, tags, status |
| `indexed_folders` | folder_path, added_at, is_active |
| `files_fts` | FTS5 virtual table on name, path, extracted_text, tags |
| `file_chunks` | id, file_id, chunk_index, chunk_text, vector_id, created_at |
| `embeddings` | id, file_id, chunk_id, vector_id, model_name, created_at |
| `search_history` | query, searched_at, result_count |
| `settings` | key-value preferences |
| `index_jobs` | job tracking |

---

## 7. Staged Indexing Flow

| Stage | Task | Result |
|-------|------|--------|
| Stage 1 | Metadata scan | Filename search available immediately |
| Stage 2 | Text extraction | Content search available |
| Stage 3 | FTS5 indexing | Fast full-text search |
| Stage 4 | Tag generation | Better filtering |
| Stage 5 | Embedding generation | Semantic search available |
| Stage 6 | OCR (V4 only) | Images/scanned files searchable |

> App must be usable after Stage 1. Never block user until all stages complete.

---

## 8. Hybrid Search Ranking Formula

```
Final Score =
  filename_score  * 0.30
+ tag_score       * 0.20
+ content_score   * 0.25
+ semantic_score  * 0.20
+ recency_score   * 0.05
```

- V1: semantic_score = 0
- V2+: semantic_score from FAISS similarity
- Filename matches must never be buried by semantic results

---

## 9. Result Explanation Format

Every result should show why it matched. Examples:
```
Filename matched "payment"
Content contains "PayHere sandbox"
Tags include "gateway"
Semantic meaning is close to your search
Modified recently
```
Explanations must come from real signals — not generated text.

---

## 10. Auto-Tagging Rules

Use signals from: file extension, folder name, filename, extracted keywords.
Do NOT use a large LLM for tagging.

Example keyword categories:
```
finance:     invoice, payment, receipt, bank, salary
university:  assignment, lecture, tutorial, practical, exam
project:     github, database, frontend, backend, api
code:        function, class, import, controller, model
design:      figma, logo, ui, ux, wireframe
```

---

## 11. Text Extraction — Supported File Types (V1)

```
.txt  .md   .csv
.py   .js   .jsx  .ts  .tsx
.php  .java .html .css .sql
.pdf  .docx
```

- Skip files > 25 MB for extraction
- Still index metadata for unsupported/skipped files
- Handle errors per file — never crash the whole indexer

---

## 12. Semantic / AI Rules (V2+)

| Rule | Detail |
|------|--------|
| Model | sentence-transformers/all-MiniLM-L6-v2 only |
| Chunk size | 300–500 words |
| Max chunks per file | 20 |
| Max text per file | 20,000 characters |
| Batch size | 16 or 32 chunks |
| When to embed | Only during indexing or background processing |
| During live search | Only generate query embedding — never file embeddings |
| Cache embeddings | Skip if file unchanged (check path + size + mtime) |
| ONNX optimization | Later optimization — not MVP |

---

## 13. Memory & Performance Rules

- Never load all file records or extracted text into memory at once
- Return top 20–50 search results; paginate for more
- Load file details only when user opens a result panel
- FAISS index lives in memory; all metadata stays in SQLite
- Debounce search input by 250–400 ms in UI
- Batch embed generation; never one-by-one
- Background tasks: text extraction, tag generation, embedding generation, OCR

---

## 14. Version Plan

### Version 1 — Core Local File Search (Current Target)
Includes: Electron shell, React UI, Python FastAPI, SQLite, folder selection, metadata indexing, filename search, text extraction, FTS5 content search, basic auto-tagging, result cards, open file/folder, indexing progress, basic settings.

**V1 must NOT include:** FAISS, embeddings, semantic search, OCR, similar file detection, fine-tuning.

### Version 2 — Semantic AI Search
Add: MiniLM embeddings, FAISS, semantic search, hybrid ranking, result explanation, similar file detection.

### Version 3 — Background Updates
Add: watchdog file watcher, background re-indexing, changed/deleted/renamed file handling, performance logging.

### Version 4 — OCR
Add: Tesseract OCR (disabled by default), screenshot/scanned doc search.

---

## 15. Step-by-Step Build Workflow

| Step | Task |
|------|------|
| Step 0 | Understand project, read docs, confirm — no code |
| Step 1 | Create project folder structure (placeholders only) |
| Step 2 | Setup Electron + React (working desktop window) |
| Step 3 | Setup Python FastAPI backend (health check only) |
| Step 4 | Connect React frontend to backend health check |
| Step 5 | Setup SQLite database schema |
| Step 6 | Build file scanner (metadata only) |
| Step 7 | Store scanned metadata into SQLite |
| Step 8 | Add filename search (from index only) |
| Step 9 | Add text extraction (supported file types) |
| Step 10 | Add SQLite FTS5 content search |
| Step 11 | Add basic auto-tagging |
| Step 12 | Build search UI (search bar, filters, result cards) |
| Step 13 | Add open file / open folder actions |
| Step 14 | Add indexing progress display |
| Step 15 | Add semantic search (MiniLM + FAISS) |
| Step 16 | Add hybrid ranking |
| Step 17 | Add similar file detection |
| Step 18 | Add file watcher (watchdog) |
| Step 19 | Add OCR (Tesseract, disabled by default) |
| Step 20 | Add packaging (Electron Builder installer) |

---

## 16. Required Response Format After Each Step

```
Completed Step:
Files Created/Updated:
What Was Implemented:
How to Run:
How to Test:
Limitations:
Next Recommended Step:
```

**The agent must stop after each step and wait for the next instruction.**

---

## 17. Electron Desktop Rules

Electron main process must handle:
- Open/close app window
- Start Python backend on launch
- Stop Python backend on app close
- Native folder picker
- Open file (shell.openPath)
- Open file location (shell.showItemInFolder)

React must NOT directly access the filesystem.

---

## 18. UI Rules

- Use Vanilla CSS (not TailwindCSS)
- Debounce search input 250–400 ms
- Paginate results (show top 20–50, load more on demand)
- Show loading states, empty states, progress indicators
- Do not render thousands of results at once
- API responses must not include full extracted text — use previews only

---

## 19. Security & Privacy Rules

- No cloud upload, ever
- No remote APIs
- No telemetry by default
- No hidden network calls
- Local SQLite database only
- User controls which folders are indexed
- Provide a "Clear Index" option (eventually)

---

## 20. API Search Response Shape (Lightweight)

```json
{
  "file_id": 1,
  "name": "filename.pdf",
  "path": "/path/to/file",
  "extension": ".pdf",
  "size": 204800,
  "modified_date": "2026-01-01T10:00:00",
  "tags": ["finance", "invoice"],
  "score": 0.87,
  "matched_reasons": ["Filename matched 'invoice'", "Tag matched 'finance'"],
  "preview": "Short text preview..."
}
```

Full extracted text is loaded only when user opens the file details panel.

---

## 21. Acceptance Criteria Checklist

- [ ] Runs as a desktop app (Electron)
- [ ] Indexes selected folders locally
- [ ] Searches only from pre-built indexes (never live scan)
- [ ] Supports filename search
- [ ] Supports content search (FTS5)
- [ ] Stores data locally in SQLite
- [ ] Uses FTS5 for full-text search
- [ ] Uses MiniLM + FAISS for semantic search (V2)
- [ ] Does not use cloud APIs
- [ ] Does not use large LLMs
- [ ] Handles file errors safely (no crashes)
- [ ] UI remains responsive during indexing
- [ ] Includes clear documentation

---

*Last updated: Step 0 — Project understanding confirmed. Awaiting Step 1 instruction.*


# DeepFind Code Quality, Security, Performance, and Maintainability Rules

## Purpose

From this point onward, all code written for **DeepFind** must follow professional software engineering standards.

The project should not look like quick AI-generated code. It should look like clean, intentional, developer-written code that is secure, optimized, maintainable, and easy to extend.

These rules apply to every future step and patch.

---

## 1. General Coding Standard

Write code as if this is a real production desktop application.

Code must be:

- Clean
- Readable
- Secure
- Efficient
- Modular
- Maintainable
- Easy to debug
- Easy to extend
- Well-named
- Not over-engineered

Do not write messy, duplicated, temporary, or shortcut code.

Do not rewrite unrelated parts of the app unless explicitly asked.

For patches, make the smallest safe change.

---

## 2. Architecture Discipline

Follow the existing architecture:

```text
Electron + React frontend
Python FastAPI backend
SQLite local database
SQLite FTS5 search
FAISS and MiniLM only later for semantic search
```

Do not introduce new frameworks, libraries, databases, or patterns without explicit approval.

Do not redesign the app during a feature step.

Do not mix responsibilities.

### Frontend responsibilities

- UI rendering
- User interactions
- Calling backend APIs
- Calling safe Electron preload APIs

### Electron responsibilities

- Desktop shell
- Native file/folder actions
- Secure IPC bridge

### Backend responsibilities

- File indexing
- Search
- Database
- Extraction
- Tagging
- API endpoints

### Database responsibilities

- Local persistence only

---

## 3. Security Rules

DeepFind is a local-first file search app, so security is critical.

Never:

- Upload files
- Upload extracted text
- Upload file paths
- Upload metadata
- Upload search queries
- Use cloud AI APIs
- Use remote databases
- Use telemetry by default
- Expose Node.js APIs directly to React
- Use `child_process` for opening files
- Execute arbitrary commands
- Trust frontend input blindly

### Electron security

- `contextIsolation` must remain `true`
- `nodeIntegration` must remain `false`
- Use `contextBridge` only
- Expose only specific safe functions
- Do not expose `ipcRenderer` directly
- Do not expose `fs`, `path`, `shell`, or `require` directly

Allowed desktop bridge functions only:

```text
openFile(filePath)
showInFolder(filePath)
selectFolder() if needed later
isDesktop flag
```

Validate all file paths before opening:

- Must be a non-empty string
- Must not be `http://` or `https://`
- Must be a local path
- Should exist before opening
- Return safe error if invalid

---

## 4. Backend Security Rules

All API inputs must be validated.

Use:

- Pydantic models where useful
- Type hints
- Safe defaults
- Parameterized SQL queries

Never build SQL using string concatenation with user input.

Bad:

```python
query = f"SELECT * FROM files WHERE name LIKE '%{q}%'"
```

Good:

```python
cursor.execute("SELECT ... WHERE name LIKE ?", (f"%{q}%",))
```

FTS5 query strings must be sanitized.

If FTS query syntax fails:

- Catch the error
- Fallback to safe sanitized search
- Never crash the backend

---

## 5. Performance Rules

DeepFind must feel fast.

Search must never:

- Scan the disk
- Read file contents
- Extract text
- Regenerate tags
- Generate embeddings
- Run OCR
- Load all rows into memory

Search must only use:

- SQLite `files` table
- SQLite indexes
- SQLite FTS5
- Already stored tags
- Already extracted text
- Later, FAISS indexes

Target performance:

```text
metadata search: ideally under 100–200ms
FTS content search: ideally under 300–700ms
hybrid search: ideally under 500–1000ms
UI loading state should appear immediately
```

Use `LIMIT` and `OFFSET` everywhere results can grow.

Default result limit:

```text
50
```

Candidate limits:

```text
metadata candidates: 100–200
content candidates: 100–200
final results: 50
```

Do not return full `extracted_text` in search results.

Return snippets only.

---

## 6. Memory Efficiency Rules

Do not load large datasets into memory.

Avoid:

- `SELECT *`
- Loading all files
- Loading all extracted text
- Loading all chunks
- Returning huge API payloads
- Processing all records in Python when SQL can filter

Prefer:

- Selected columns only
- Pagination
- Candidate limits
- Batch processing
- Streaming/generator-style scanning
- Small API responses

Dashboard responses must be small.

Search result responses should include only:

```text
id
name
path
extension
size
size_human
modified_at
status
tags
score
match_type
matched_reasons
snippet if needed
```

---

## 7. Database Best Practices

SQLite is the local source of truth.

Use:

- WAL mode
- Safe PRAGMA settings
- Reusable repository methods
- Migrations that do not destroy data
- Indexes for frequently searched columns
- Batch writes for indexing/extraction/tagging

Never:

- Delete user data unexpectedly
- Drop tables during normal startup
- Store binary file contents
- Store huge unnecessary data
- Commit local user database to GitHub

Database file should remain gitignored.

Recommended indexes:

```sql
files(name)
files(extension)
files(status)
files(modified_at)
files(last_indexed_at)
files(path)
files(tags), if useful
```

Use FTS5 for full-text search.

---

## 8. Background Task Rules

Heavy work must run in background workers.

Heavy work includes:

- Metadata indexing
- Text extraction
- Tagging
- Future embedding generation
- Future OCR
- Future file watching updates

Rules:

- UI must remain responsive
- `/health` must remain responsive
- `/search` must remain responsive
- Prevent duplicate jobs
- Expose progress endpoints
- Handle errors per file
- Continue processing after errors
- Save progress regularly

If a task is already running:

```json
{
  "status": "already_running"
}
```

Do not start duplicate background jobs.

---

## 9. Error Handling Rules

The app must not crash because of one bad file.

Handle:

- Permission errors
- Locked files
- Corrupted PDFs
- Broken DOCX files
- Encoding errors
- Deleted files
- Missing paths
- Long paths
- Unsupported file types
- Invalid search input
- Failed Electron open action

Return clean errors.

Log useful technical details in backend/electron console, but show user-friendly messages in UI.

Never expose scary stack traces to the UI.

---

## 10. Logging Rules

Use clear and useful logs.

Backend logs should help debug:

- Indexing start/end
- Extraction start/end
- Tagging start/end
- Search timing
- Errors with path if safe
- Counts processed/skipped/failed

Avoid noisy logs during normal search.

For performance work, add timing logs:

- Query parsing
- Metadata search
- FTS search
- Merge/ranking
- History save
- Total request time

---

## 11. Frontend Code Rules

React code must be clean and component-based.

Use:

- Reusable components
- Clear props
- Hooks for data fetching/state
- Service layer for API calls
- Loading/error/empty states
- Accessible buttons and labels

Do not:

- Put large API logic inside JSX
- Duplicate fetch code everywhere
- Mutate state directly
- Render thousands of results
- Block the UI
- Show raw backend errors without cleanup

Search UI must:

- Show loading immediately
- Handle backend offline safely
- Show empty states
- Prevent duplicate rapid requests where needed
- Ignore stale responses if user searches again

---

## 12. Electron Code Rules

Electron main process should only handle desktop responsibilities.

Keep Electron code minimal and secure.

Use:

- `ipcMain.handle` for controlled actions
- `shell.openPath`
- `shell.showItemInFolder`
- Dialog APIs only when needed
- `contextBridge` in preload

Do not use:

- `child_process`
- Remote module
- Direct Node access in React
- Insecure `webPreferences`

After changing `main.js` or `preload.js`, restart Electron fully.

---

## 13. Search Quality Rules

Search should prioritize best matches first.

For natural queries:

- Parse query into metadata terms, extension filters, tag terms, content terms
- Ignore filler words
- Use file type words as strong signals
- Calculate match coverage
- Rank results matching most important parts higher

Do not let weak generic tags dominate.

Generic weak tags:

```text
document
file
text
data
common
```

Specific strong tags:

```text
pdf
python
php
sql
payment
fixlanka
cv
design
university
database
```

For query:

```text
ayya pdf
```

Expected:

- Files in/related to `ayya`
- With `.pdf` extension

These should rank above unrelated `.txt` files tagged `document`.

For query:

```text
python code file using pandas library
```

Expected:

- `.py` / python / code files
- Containing `pandas`

These should rank above random files matching only `code`.

---

## 14. Patch Rules

When fixing bugs, do not redo the whole step.

Use patch-only changes.

Before editing:

- Inspect the related files
- Identify the smallest safe fix
- Avoid touching unrelated files

For every patch response, include:

```text
Patched Files:
What Changed:
What Was Not Changed:
How to Test:
```

If more than the expected files need changes, explain why before changing them.

---

## 15. Dependency Rules

Keep dependencies minimal.

Do not install packages unless truly needed.

Before adding a dependency, consider:

- Is it necessary?
- Is it lightweight?
- Is it maintained?
- Can built-in Python/JS do this?
- Does it increase app size significantly?
- Does it affect security?

Allowed existing direction:

```text
fastapi
uvicorn
sqlite3 built-in
pypdf
python-docx
watchdog later
FAISS later
sentence-transformers/all-MiniLM-L6-v2 later only
```

Do not add:

- Cloud SDKs
- Large NLP libraries
- Large LLM packages
- Unnecessary UI libraries
- Remote database clients

---

## 16. Documentation Rules

Each step must update documentation briefly.

Update:

- `docs/progress-log.md`
- `docs/setup-notes.md` if run/test commands changed

Do not write huge unnecessary docs for small patches.

Docs should be clear and practical.

---

## 17. Code Style Rules

### Python

- Type hints where useful
- Small functions
- Clear names
- No giant functions
- Repository methods for DB access
- Service/manager classes for background jobs
- Avoid duplicated logic
- Handle exceptions intentionally

### JavaScript / React

- Clean components
- Clear service functions
- No business logic hidden in JSX
- No direct Electron/Node access except through preload API
- Avoid global hacks

### SQL

- Parameterized queries
- Selected columns only
- Proper indexes
- No destructive migrations
- Safe schema updates

---

## 18. Testing Rules

Every step must include Electron app testing instructions.

Browser/API testing is optional developer debugging only.

For features involving desktop behavior:

- Test only in Electron app
- Do not rely on browser testing

For backend-only features:

- API debugging is okay
- User-facing validation should still happen through the Electron app when possible

---

## 19. Expected Agent Behavior

After each step, respond with:

```text
Completed Step:
Files Created/Updated:
What Was Implemented / Fixed / Optimized:
How to Run:
How to Test in Electron App:
Optional Developer Debugging:
Limitations:
Next Recommended Step:
```

For patches, respond with:

```text
Patched Files:
What Changed:
What Was Not Changed:
How to Test:
Limitations:
```

---

## 20. Final Reminder

The goal is not just to make the app work.

The goal is to make DeepFind:

- Secure
- Fast
- Local-first
- Resource-friendly
- Maintainable
- Professional
- Cleanly coded
- Easy to extend

The agent must write code like a careful developer, not like a quick prototype generator.

---

## Recommended Message to Give the Agent

Use this message before the next step:

```text
These are global rules. Apply them to all future code changes and patches. Do not rewrite existing code just to apply these rules. Apply them gradually when touching relevant files.
```
