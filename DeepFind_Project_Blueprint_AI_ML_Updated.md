---
title: "DeepFind"
subtitle: "Updated Project Blueprint - Auto Source Discovery + Local AI/ML Plan"
author: "Personal Portfolio Project"
date: "2026-05-19"
geometry: margin=0.75in
fontsize: 10pt
---

# DeepFind - AI-Powered Local File Search Desktop App

**One-line pitch:** DeepFind helps users find local files by what they remember - filename, path, content, tags, metadata, and meaning - not only by exact file names.

This updated blueprint includes the latest requirement change: **DeepFind should automatically discover common user folders and local drives**, instead of depending only on manual one-by-one folder selection.

| Item | Final Decision |
|---|---|
| Project type | Personal portfolio desktop application |
| Primary platform | Windows first, with cross-platform possibility later |
| Core idea | Everything-like fast local file search plus AI/semantic understanding |
| App style | Local-first desktop app |
| Privacy direction | Files, indexes, embeddings, paths, and queries stay on the user's machine |
| Source discovery | Automatically detect common user folders and local drives |
| Default indexing behavior | Common user folders active by default; full drives inactive by default |
| AI strategy | Lightweight local embedding model, no cloud AI APIs |
| Recommended first release | Auto source discovery, metadata indexing, fast filename/path search, content search, and polished desktop UI |

---

# 1. Project Description

DeepFind is a local-first desktop file search application designed to help users find files even when they cannot remember the exact filename or location. It combines fast indexed search with automatic indexing source discovery, metadata indexing, content extraction, auto-generated tags, full-text search, and semantic AI search.

The app is inspired by a real personal problem: users often remember the topic, purpose, or context of a file, but not the actual filename. Existing tools such as Everything are excellent for fast filename search, but the goal of DeepFind is to extend that experience into content-aware and meaning-based local file discovery.

| Traditional Search | DeepFind Search |
|---|---|
| Searches mainly by file/folder name | Searches by filename, path, content, tags, metadata, and meaning |
| Requires exact or close keyword memory | Accepts natural language queries based on what the user remembers |
| Usually cannot explain why a result appeared | Shows matched reason and context for each result |
| Limited understanding of document content | Extracts and indexes supported file content |
| User must often know where to search | Automatically discovers common folders and drives |

---

# 2. Real-World Problem

The common problem is not that files are missing; the problem is that users cannot remember how they named or organized them. A user may remember "the document about PayHere sandbox setup" or "the Java assignment about linked lists," but the actual file may be named `notes_final.docx`, `practical3.pdf`, or saved inside an unexpected folder.

DeepFind solves this by allowing users to search the way they naturally remember files: by topic, purpose, content, tags, date, file type, location, or context.

---

# 3. Product Goal and Value

| Goal | Description |
|---|---|
| Fast local search | Return results from pre-built indexes instead of scanning files during search. |
| Automatic discovery | Detect common user folders and available local drives automatically. |
| Meaning-based discovery | Use embeddings and semantic similarity to find conceptually relevant files. |
| Content awareness | Extract text from documents and code files so hidden content becomes searchable. |
| Better user confidence | Explain why each result matched the query. |
| Privacy-first design | Process files locally without uploading file content, paths, embeddings, or queries. |
| Portfolio strength | Demonstrate desktop development, search systems, AI integration, databases, local privacy design, and product thinking. |

---

# 4. Core Functionalities

| Functionality | Description |
|---|---|
| Automatic source discovery | Detect Desktop, Documents, Downloads, Pictures, Videos, Music, and available local drives. |
| Source toggles | Let the user enable/disable detected indexing sources. |
| Safe default sources | Enable common user folders by default; keep full drives disabled by default. |
| Fast filename search | Search file names, folder names, extensions, and paths using indexed metadata. |
| Content-based search | Extract and search inside documents, text files, and code files. |
| Natural language search | Search using phrases such as "document about payment gateway setup". |
| Auto-tagging | Generate tags from filename, folder path, extension, content keywords, and later AI-assisted logic. |
| Metadata search | Filter/search by extension, size, modified date, created date, and indexed source. |
| Result explanation | Show why the result appeared: filename match, content match, tag match, semantic match, or recency. |
| Open file/folder | Open the selected file or reveal it in the file explorer. |
| File details panel | Show metadata, tags, text preview, matched reasons, and similar files. |
| Similar file detection | Use content/semantic similarity to find versions or related files. |
| Background indexing | Gradually index and update files without blocking the UI. |
| OCR support later | Extract searchable text from screenshots and scanned images. |

---

# 5. Updated Source Discovery Requirement

The app should not depend only on manually adding folders one by one. DeepFind should behave more like a local system file search tool by automatically detecting useful locations on the machine.

## 5.1 Sources to Detect Automatically

| Source type | Examples |
|---|---|
| Common user folders | Desktop, Documents, Downloads, Pictures, Videos, Music |
| User profile folder | `C:\Users\<username>` on Windows, where appropriate |
| Local drives | `C:`, `D:`, `E:`, and other mounted local drives if available |
| Manual folders later | User-added custom folders can be added as an optional feature later |

## 5.2 Default Active/Inactive Behavior

| Source | Default status | Reason |
|---|---|---|
| Desktop | Active | Common location for important files. |
| Documents | Active | Main location for documents and academic/work files. |
| Downloads | Active | Common location for newly saved files. |
| Pictures | Active | Useful for screenshots and images. |
| Videos | Inactive | Can contain large files and slow down indexing. |
| Music | Inactive | Often large and less relevant to document search. |
| Full drives such as C:, D:, E: | Inactive | Full drive indexing can be heavy and should be optional. |

## 5.3 Important Rule

Full drive indexing must not start automatically. The app may detect drives, but full drives should stay inactive until the user enables them.

---

# 6. Version-wise Feature Plan

## Version 1 - Strong MVP

Purpose: Build a usable desktop app that automatically discovers indexing sources, indexes active safe folders, and performs fast filename/content search.

| Feature | Included in V1 |
|---|---|
| Desktop app shell | Electron window with React UI |
| Engine connection | React calls local FastAPI backend health endpoint |
| SQLite database | Local schema for files, indexed folders, FTS5, settings, and future AI mapping |
| Automatic source discovery | Detect common folders and drives |
| Source manager UI | Show detected sources with active/inactive toggles |
| Safe default sources | Desktop, Documents, Downloads, Pictures active by default |
| Full-drive safety | Full drives detected but inactive by default |
| Metadata indexing | Path, filename, extension, size, created/modified date |
| Filename/path search | Fast search by file/folder name, path, and extension |
| Text extraction | TXT, MD, CSV, PDF, DOCX, and code files |
| Full-text search | SQLite FTS5 search over extracted content and tags |
| Basic auto-tags | Rules/keywords from name, folder, type, and content |
| Result cards | File name, path, type, modified date, tags, actions |
| Open file/folder | Open selected file or location |
| Manual re-indexing | Button to re-index active sources |

## Version 2 - Lightweight Semantic AI Search

| Feature | Included in V2 |
|---|---|
| Embeddings | Generate semantic vectors from extracted text using `sentence-transformers/all-MiniLM-L6-v2` |
| FAISS vector search | Find conceptually similar files locally |
| Natural language search | Search by meaning instead of exact words |
| Chunk-level embeddings | Split long documents into chunks and embed chunks, not huge whole files |
| Hybrid ranking | Combine filename, tag, content, semantic, and recency scores |
| Result explanation | Show why each result matched |
| Similar files | Detect related or duplicate-like files |
| Improved tags | Better keyword and AI-assisted tag generation without large LLMs |

## Version 3 - Background Updates and Efficiency

| Feature | Included in V3 |
|---|---|
| Background file watcher | Use watchdog to update index when files change |
| Incremental re-indexing | Re-index only changed files, not entire folders |
| Deleted/renamed file handling | Keep database synced with file system changes |
| Advanced filters | Date range, file size, type, source, tag, status |
| Search history | Store recent searches locally |
| Performance logging | Track indexing time, search time, DB size, and vector index size |
| Installer packaging | Create installable Windows release |

## Version 4 - OCR and Future Expansion

| Feature | Future Possibility |
|---|---|
| OCR for screenshots/images | Use Tesseract to extract text from images and screenshots |
| Scanned PDF support | OCR-based extraction where normal PDF text extraction fails |
| Image meaning search | Find images by visual content such as "screenshot of login page" |
| Audio/video search | Transcribe audio/video and make speech searchable |
| Cross-platform releases | Support macOS and Linux builds |
| Local LLM assistant | Optional future conversational file questions and summaries |
| Smart cleanup tools | Find duplicates, old downloads, temporary files, and unused large files |

---

# 7. Recommended Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Desktop shell | Electron | Creates an installable desktop app with native window and file-system actions. |
| Frontend UI | React | Modern interface with reusable components and fast UI iteration. |
| Search/AI engine | Python | Strong ecosystem for file processing, AI models, FAISS, OCR, and indexing. |
| Local API | FastAPI | Simple communication bridge between React/Electron and Python engine. |
| Database | SQLite | Lightweight local database suitable for desktop apps. |
| Full-text search | SQLite FTS5 | Fast local keyword/content search without external services. |
| Semantic search | FAISS | Efficient vector similarity search for meaning-based retrieval. |
| Embeddings | sentence-transformers | Creates semantic vectors from file text and user queries. |
| Embedding model | all-MiniLM-L6-v2 | Lightweight CPU-friendly local embedding model. |
| File watcher | watchdog | Detects file changes for background re-indexing. |
| Text extraction | pypdf, python-docx | Extracts searchable text from PDFs and Word documents. |
| OCR later | Tesseract | Extracts text from screenshots and scanned images. |
| Packaging | Electron Builder | Creates installable app builds. |

---

# 8. Efficient System Architecture

The most efficient architecture is a hybrid local desktop architecture where the UI is separated from the indexing/search engine. The UI should never scan files directly. It should only call the local engine, which searches pre-built indexes.

```text
DeepFind Desktop App
|
|-- Electron Desktop Shell
|   |-- App window
|   |-- Native desktop actions
|   |-- Open file / open folder actions
|
|-- React Frontend
|   |-- Search bar
|   |-- Source manager UI
|   |-- Result cards
|   |-- Filters
|   |-- File details panel
|   |-- Settings
|
|-- Local Python Engine
|   |-- Source discovery layer
|   |-- Indexing source manager
|   |-- Scanner
|   |-- Extractors
|   |-- Indexer
|   |-- Hybrid search
|   |-- Ranker
|
|-- Local Storage
    |-- SQLite metadata database
    |-- SQLite FTS5 full-text index
    |-- FAISS semantic vector index
```

| Architecture Principle | Decision |
|---|---|
| Search from indexes only | Never read every file during user search. |
| Source discovery first | Automatically discover common folders and drives before indexing. |
| Safe indexing defaults | Index common user folders first; keep full drives disabled. |
| Staged indexing | Index metadata first, then content, tags, embeddings, and OCR. |
| Background processing | Heavy extraction and embedding tasks run outside the UI thread. |
| Hybrid search | Combine filename, full-text, tags, semantic vectors, and recency. |
| Local-first | Keep database, extraction, vectors, paths, and search queries on the user device. |

---

# 9. Source Discovery and Indexing Flow

## 9.1 Source Discovery Flow

```text
App starts
   ↓
Detect common user folders
   ↓
Detect available local drives
   ↓
Save sources in SQLite
   ↓
Set safe default active/inactive states
   ↓
Show sources in UI
   ↓
User can enable/disable sources
   ↓
Index active sources only
```

## 9.2 Staged Indexing Flow

| Stage | Task | Result |
|---|---|---|
| Stage 0 | Source discovery | App knows where files may be indexed. |
| Stage 1 | Quick metadata scan | Filename/path search becomes available quickly. |
| Stage 2 | Text extraction | Content search becomes available. |
| Stage 3 | Tag generation | Files receive searchable categories. |
| Stage 4 | Embedding generation | Semantic search becomes available. |
| Stage 5 | OCR later | Images/screenshots/scanned files become searchable. |

## 9.3 Exclusion Rules for Future Scanning

When scanning active sources, the app should skip or avoid heavy/system folders by default.

Default exclusions:

```text
Windows
Program Files
Program Files (x86)
AppData
node_modules
.git
.venv
__pycache__
Temp
cache folders
large binary-only folders
```

---

# 10. Hybrid Search Flow

The app should not rely only on AI. It should combine traditional indexed search with lightweight semantic search.

```text
User Query
   |
   |-- Filename/path search
   |-- SQLite FTS5 content search
   |-- Tag search
   |-- Metadata filters
   |-- FAISS semantic search
   |
Merge results
   |
Rank results
   |
Return result list with explanation
```

Recommended ranking formula:

```text
final_score =
  filename_score * 0.30
+ tag_score      * 0.20
+ content_score  * 0.25
+ semantic_score * 0.20
+ recency_score  * 0.05
```

For Version 1, semantic score can be zero. For Version 2, semantic score comes from FAISS similarity.

---

# 11. Data Storage Design

| Storage item | Purpose |
|---|---|
| SQLite normal tables | Store file metadata, indexing sources, settings, search history, and mapping data. |
| SQLite FTS5 table | Store searchable text fields for fast full-text search. |
| FAISS index | Store semantic vectors for text chunks. |
| Local app data folder | Store database and index files on the user machine. |

## 11.1 Suggested Tables

| Table | Main fields |
|---|---|
| files | id, path, name, extension, size, created_at, modified_at, last_indexed_at, content_hash, extracted_text, tags, status, error_message |
| indexed_folders | id, folder_path, is_active, source_type, added_at, last_scanned_at |
| files_fts | name, path, extracted_text, tags |
| file_chunks | id, file_id, chunk_index, chunk_text, vector_id, created_at |
| embeddings | id, file_id, chunk_id, vector_id, model_name, created_at |
| search_history | id, query, searched_at, result_count |
| settings | key, value |

## 11.2 Source Type Values

| source_type | Meaning |
|---|---|
| auto_common_folder | Automatically detected folder such as Desktop or Documents |
| auto_drive | Automatically detected local drive such as C: or D: |
| manual | Optional custom folder added by user later |

---

# 12. Main App Screens

| Screen | Purpose |
|---|---|
| Welcome / setup screen | Introduce the app and show engine status. |
| Indexing sources screen | Show automatically detected folders/drives with toggles. |
| Indexing progress screen | Show staged indexing progress and errors. |
| Main search screen | Search by filename, content, tags, metadata, and meaning. |
| Results screen | Display result cards with matched reasons and actions. |
| File details panel | Show metadata, preview, tags, similar files, and explanation. |
| Settings screen | Configure indexed sources, file limits, semantic search, OCR, and privacy options. |

---

# 13. Development Roadmap

| Phase | Task |
|---|---|
| Phase 1 | Create project structure and documentation. |
| Phase 2 | Build Electron + React desktop shell. |
| Phase 3 | Build FastAPI backend with health endpoint. |
| Phase 4 | Connect frontend to backend health endpoint. |
| Phase 5 | Create SQLite database schema and status endpoint. |
| Phase 6 | Implement automatic source discovery and source toggles. |
| Phase 7 | Scan active sources and store file metadata. |
| Phase 8 | Add filename/path/extension search. |
| Phase 9 | Add text extraction for supported file types. |
| Phase 10 | Add SQLite FTS5 content search. |
| Phase 11 | Add basic auto-tagging. |
| Phase 12 | Build complete search UI and result cards. |
| Phase 13 | Add open file/open folder actions. |
| Phase 14 | Add indexing progress. |
| Phase 15 | Add MiniLM + FAISS semantic search. |
| Phase 16 | Add hybrid ranking and result explanations. |
| Phase 17 | Add similar file detection. |
| Phase 18 | Add file watcher and incremental re-indexing. |
| Phase 19 | Add OCR later. |
| Phase 20 | Package as desktop app. |

---

# 14. AI/ML Strategy and Model Plan

The AI/ML part should be lightweight and fully local. DeepFind should not train a large model from scratch and should not use cloud AI APIs for file search.

## 14.1 Local Model Rule

DeepFind must use a local pretrained embedding model for semantic search. The approved first model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The model is used only to generate embeddings for extracted text chunks and user queries.

It must not act as:

```text
cloud AI agent
chatbot
external search service
file upload service
remote document processor
```

## 14.2 How the Local Model Works

```text
User file
   ↓
Text extracted locally
   ↓
Local embedding model converts text chunks into vectors
   ↓
Vectors stored locally in FAISS
   ↓
User search query converted into a vector locally
   ↓
FAISS finds similar vectors locally
   ↓
Results mapped back to local files
```

No file content, filenames, paths, metadata, embeddings, or search queries should leave the user's machine.

## 14.3 Model Download and Cache Behavior

During development, the model may be downloaded automatically by the `sentence-transformers` library on first use.

Example:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

Expected behavior:

| Situation | Behavior |
|---|---|
| First run | Model downloads from a trusted source and is cached locally. |
| Later runs | Model loads from local cache. |
| Production option 1 | Download model during first setup. |
| Production option 2 | Bundle model inside the installer for offline use. |

For the portfolio version, first-run download is acceptable during development. Later packaging can support model bundling.

---

# 15. Lightweight Model Selection

| Option | Decision |
|---|---|
| Train from scratch | Do not do this. Too heavy and unnecessary. |
| Large local LLM | Do not use in early versions. Too resource-heavy. |
| Cloud AI API | Do not use. Privacy/security risk. |
| MiniLM embedding model | Recommended first model. Lightweight and CPU-friendly. |
| ONNX optimized model | Future optimization. |
| INT8 quantization | Future optimization for smaller/faster CPU inference. |

The first semantic search model should be:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Reasons:

```text
Lightweight
CPU-friendly
Good enough for semantic search
Works locally
Produces compact embeddings
Suitable for normal laptops
```

---

# 16. Training and Fine-Tuning Approach

## 16.1 No Training First

DeepFind should not train or fine-tune a model in Version 1 or Version 2. Semantic search should work using the pretrained MiniLM embedding model.

Most of the app's intelligence comes from:

```text
file indexing
text extraction
embedding generation
FAISS similarity search
hybrid ranking
result explanation
```

This is much lighter than training a model.

## 16.2 Optional Future Fine-Tuning

Fine-tuning can be considered later only if needed and only with local user feedback.

Possible local feedback data:

```text
search query
clicked file
ignored results
timestamp
```

This can create training pairs:

| Data Type | Example | Use |
|---|---|---|
| Positive pair | Query + clicked file text | The clicked file is likely relevant. |
| Negative pair | Query + ignored unrelated file text | Skipped files can be weak negative examples. |
| Ranking feedback | Query + result order + click behavior | Can improve future ranking logic. |

Fine-tuning must remain optional and local.

---

# 17. Resource-Friendly AI Design

The app must remain efficient on normal laptops. AI tasks should be background enrichment tasks, not blocking tasks. The user should be able to search filenames and metadata quickly even while deeper AI indexing is still running.

## 17.1 Practical Resource Limits

Recommended default limits for a lightweight first release:

```text
Maximum file size for text extraction: 25 MB initially
Maximum text length per file for embeddings: around 20,000 characters
Chunk size: around 300 to 500 words
Maximum chunks per large file: around 20 initially
OCR disabled by default
Full drive indexing disabled by default
CPU inference first; no GPU required
Batch embedding generation instead of one chunk at a time
Cache extracted text, tags, summaries, and embeddings
Re-index only if file path, size, or modified timestamp has changed
```

## 17.2 Memory Efficiency Rules

```text
Do not load all extracted text into memory.
Do not load all file records into the UI at once.
Return top 20 or top 50 results first.
Load full file details only when the user opens a result.
Store vectors in FAISS and metadata/text in SQLite.
Use pagination or virtualized lists for large result sets.
```

## 17.3 Optimization Roadmap

```text
Start with normal sentence-transformers for easier development.
Later convert the embedding model to ONNX.
Apply INT8 quantization to reduce size and improve CPU speed.
Keep FAISS index loaded only when the search engine is running.
Use lazy loading and batch processing for large sources.
Store vector mappings clearly so FAISS results can be traced back to file IDs and chunk IDs.
```

---

# 18. AI/ML Data Storage and Processing

To support efficient semantic search, DeepFind should store document chunks separately from file metadata. This makes large PDFs and long documents easier to search because the app can match the most relevant chunk instead of only comparing one vector for the whole file.

## 18.1 Chunk-Based Embedding Design

Recommended processing flow:

```text
1. Read file metadata.
2. Extract text from supported file types.
3. Clean extracted text.
4. Split text into chunks.
5. Generate embeddings for each chunk.
6. Store chunk text preview in SQLite.
7. Store vectors in FAISS.
8. Store mapping between file ID, chunk ID, and vector ID.
```

## 18.2 Suggested ML Tables

```sql
CREATE TABLE file_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_index INTEGER,
    chunk_text TEXT,
    vector_id INTEGER,
    created_at TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
);
```

```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    chunk_id INTEGER,
    vector_id INTEGER,
    model_name TEXT,
    created_at TEXT
);
```

---

# 19. Privacy and Security Direction

DeepFind handles local files, so privacy must be central.

| Rule | Explanation |
|---|---|
| No cloud AI APIs | Do not send extracted text to external AI services. |
| No file uploads | Files must stay on the user's machine. |
| No remote vector DB | FAISS index must be local. |
| No remote database | SQLite database must be local. |
| No hidden telemetry | Do not collect analytics by default. |
| User-controlled sources | User can enable/disable indexing sources. |
| Clear index option | User should eventually be able to delete local index data. |
| Local model only | Embedding generation must happen locally after model download/cache. |

Security rule for the agent:

```text
DeepFind must never send user files, extracted text, file paths, metadata, embeddings, or search queries to any external server or cloud AI API.
```

---

# 20. Testing Plan

| Test Area | Example Test |
|---|---|
| Source discovery | Detect Desktop, Documents, Downloads, Pictures, Videos, Music, and available drives. |
| Source defaults | Confirm common folders active and full drives inactive. |
| Source toggles | Enable/disable sources and verify SQLite updates. |
| File scanner | Scan active sources while skipping exclusions. |
| Metadata indexing | Save file path, name, extension, size, and modified date correctly. |
| Filename search | Search `cv` and return matching filenames. |
| Content extraction | Extract text from PDF, DOCX, TXT, MD, and code files. |
| FTS5 search | Search content such as `PayHere sandbox`. |
| Auto-tagging | Generate tags from filename, path, extension, and content. |
| Semantic search | Search natural language query and return conceptually relevant files. |
| Open actions | Open file and open folder from result card. |
| Error handling | Skip permission errors, corrupted PDFs, and unsupported files safely. |
| Performance | Track indexing time, search time, database size, and memory use. |

---

# 21. Documentation to Maintain

| Document | Purpose |
|---|---|
| README.md | Main GitHub introduction. |
| PROJECT_OVERVIEW.md | Project purpose and value. |
| PROBLEM_STATEMENT.md | Real-world problem and motivation. |
| FEATURES.md | Current and planned features. |
| TECH_STACK.md | Technologies and reasons. |
| SYSTEM_ARCHITECTURE.md | How frontend, backend, database, and AI fit together. |
| SOURCE_DISCOVERY.md | Automatic folder/drive discovery rules and defaults. |
| DATABASE_DESIGN.md | Tables, fields, and relationships. |
| API_DOCUMENTATION.md | Local API endpoints. |
| AI_ML_STRATEGY.md | Local model, embeddings, FAISS, and optimization plan. |
| PERFORMANCE_REPORT.md | Measured speed and resource usage. |
| PRIVACY_AND_SECURITY.md | Local-first privacy rules. |
| TESTING_DOCUMENTATION.md | Test cases and results. |
| FUTURE_IMPROVEMENTS.md | Planned features after the portfolio release. |
| PROGRESS_LOG.md | Development journal. |

---

# 22. AI Agent Implementation Rules Summary

The coding agent should be instructed to implement only the current step and not redesign the system.

Important rules:

```text
Do not build the whole app at once.
Do not use cloud APIs.
Do not use large local LLMs.
Do not scan files during search.
Do not automatically index full drives.
Do not process OCR by default.
Use SQLite locally.
Use FTS5 for full-text search.
Use MiniLM + FAISS only from Version 2.
Use automatic source discovery from Version 1.
Keep common folders active by default and full drives inactive by default.
Index slowly in the background; search instantly from indexes.
```

---

# 23. Final Architecture Summary

| Layer | Technology | Purpose |
|---|---|---|
| UI | Electron + React | Modern desktop interface. |
| App control | Electron main process | Window lifecycle, file opening, desktop behavior. |
| Local API | FastAPI | Communication between React and Python engine. |
| Source discovery | Python + OS APIs | Detect common user folders and local drives. |
| Search engine | Python local engine | File scanning, extraction, indexing, ranking. |
| Database | SQLite | Local metadata, sources, settings, and mapping data. |
| Keyword search | SQLite FTS5 | Fast content and filename search. |
| Semantic search | MiniLM + FAISS | Natural language and meaning-based search. |
| Tagging | Rule-based + keyword extraction | Fast and explainable tags. |
| Optimization later | ONNX + INT8 | Lower memory and CPU usage. |
| OCR later | Tesseract | Image/screenshot text search. |

Final principle:

> **Discover sources automatically, index safely in the background, and search instantly from local indexes. Use AI as a lightweight semantic layer, not as the whole search engine.**

---

# 24. Final Decision Summary

- DeepFind is a personal portfolio desktop app, not an academic research project.
- It should behave like a local file search tool, not just a manually configured folder search app.
- It should automatically discover common folders and local drives.
- Desktop, Documents, Downloads, and Pictures should be active by default.
- Videos, Music, and full drives should be inactive by default.
- Full drive indexing should be optional because it can be heavy.
- The app must search from indexes, not by live scanning during user search.
- It must use local SQLite and local FAISS.
- It must not upload user files or extracted text.
- It must use a lightweight local embedding model for semantic search.
- It must not train a model from scratch in early versions.
- It must be efficient, explainable, and resource-friendly.
