# DeepFind

> **AI-Powered Local File Search Desktop App**

Find files by what you remember — filename, content, tags, metadata, and meaning — not just exact file names.

---

## What Is DeepFind?

DeepFind is a **local-first desktop application** that helps users find their files even when they cannot remember the exact filename or location.

It combines:
- **Fast indexed search** — filename, path, extension, and metadata
- **Content search** — extracted text from documents, code, and PDFs
- **Auto-tagging** — intelligent categories from file context
- **Semantic AI search** — find files by natural language meaning (V2)

All processing happens **on your machine**. No files are uploaded anywhere.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop shell | Electron |
| Frontend UI | React |
| Local backend | Python + FastAPI |
| Database | SQLite + FTS5 |
| Semantic search | FAISS + sentence-transformers/all-MiniLM-L6-v2 |
| Text extraction | pypdf, python-docx |
| File watching | watchdog (V3) |
| OCR | Tesseract (V4) |

---

## Project Structure

```
deepfind/
├── app/
│   ├── electron/          # Electron main process (desktop shell)
│   └── frontend/          # React frontend UI
├── engine/
│   ├── api/               # FastAPI routes and server
│   ├── scanner/           # File system scanner
│   ├── extractors/        # Text extraction (PDF, DOCX, TXT, etc.)
│   ├── database/          # SQLite schema and connection
│   ├── search/            # Search logic (filename, FTS5, hybrid)
│   ├── ai/                # Semantic search (FAISS + embeddings)
│   ├── indexer/           # Indexing pipeline and job management
│   └── utils/             # Shared utilities
├── docs/                  # Project documentation
├── screenshots/           # App screenshots for portfolio
├── tests/                 # Test files
├── scripts/               # Dev and setup helper scripts
└── README.md
```

---

## Version Plan

| Version | Goal |
|---------|------|
| **V1** | Core local search — folder indexing, filename/content search, FTS5, basic tags |
| **V2** | Semantic AI search — MiniLM embeddings, FAISS, hybrid ranking, result explanation |
| **V3** | Background updates — file watcher, incremental re-indexing |
| **V4** | OCR — Tesseract for screenshots and scanned documents |

---

## Privacy

- All files and indexes stay on your machine
- No cloud APIs used
- No telemetry
- You control which folders are indexed

---

## Development Status

> 🚧 **In active development — Step 1: Project structure created**

---

## Getting Started

> Setup instructions will be added as each component is built.

---

## License

MIT
