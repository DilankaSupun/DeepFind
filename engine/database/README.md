# engine/database/

This module will contain **SQLite database schema, connection management, and migrations**.

## Planned Files (Step 5)

- `connection.py` — SQLite connection factory, WAL mode setup
- `schema.py` — Table creation SQL and FTS5 virtual table definitions
- `migrations.py` — Schema versioning and upgrade logic

## Tables

| Table | Purpose |
|-------|---------|
| `files` | File metadata, extracted text, tags, status |
| `indexed_folders` | User-selected folders to index |
| `files_fts` | FTS5 virtual table for full-text search |
| `file_chunks` | Text chunks for semantic embedding (V2) |
| `embeddings` | Vector ID mapping for FAISS (V2) |
| `search_history` | Recent queries |
| `settings` | User preferences |
| `index_jobs` | Indexing job status tracking |

## Database Rules

- WAL journal mode for better concurrent read performance
- Never store binary file content in SQLite
- Store paths and extracted text only
- FTS5 table keeps in sync with `files` table

> ⏳ Not implemented yet — awaiting Step 5.
