# engine/indexer/

This module will manage the **staged indexing pipeline and job coordination**.

## Planned Files (Steps 7, 9, 11)

- `indexer.py` — Main indexing pipeline controller
- `job_manager.py` — Create, track, and update indexing jobs
- `metadata_indexer.py` — Stage 1: persist file metadata to SQLite
- `content_indexer.py` — Stage 2: trigger text extraction and FTS5 update
- `tag_indexer.py` — Stage 3: generate and store tags
- `embedding_indexer.py` — Stage 4: generate and store embeddings (V2)

## Staged Indexing Order

```
Stage 1: Metadata indexing    → filename search available
Stage 2: Text extraction      → content search available
Stage 3: FTS5 indexing        → full-text search available
Stage 4: Tag generation       → tag-based filtering available
Stage 5: Embedding generation → semantic search available (V2)
Stage 6: OCR                  → image/scan search (V4)
```

## Indexing Rules

- App is usable after Stage 1
- Never block UI until all stages complete
- Run extraction and embedding in background threads
- Re-index only changed files (check mtime + size)
- Skip inaccessible files — log error and continue

> ⏳ Not implemented yet — awaiting Step 7.
