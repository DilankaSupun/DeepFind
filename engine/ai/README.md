# engine/ai/

This module will contain **semantic AI search** using FAISS and sentence-transformers.

> ⚠️ This module is for **Version 2 only**. It must not be implemented in V1.

## Planned Files (Step 15)

- `embedder.py` — Generate text embeddings using MiniLM
- `faiss_index.py` — FAISS index create, save, load, and search
- `chunker.py` — Split long text into chunks for embedding
- `semantic_search.py` — Query the FAISS index and map results back to files

## AI Rules

| Rule | Value |
|------|-------|
| Model | sentence-transformers/all-MiniLM-L6-v2 |
| Max chunk size | 300–500 words |
| Max chunks per file | 20 |
| Max text per file | 20,000 characters |
| Batch size | 16 or 32 chunks |
| Embedding during live search | ❌ Never for files |
| Embedding during live search | ✅ Query embedding only |
| Model training | ❌ Never — use pre-trained only |
| Cloud APIs | ❌ Never |

> ⏳ Not implemented yet — awaiting Step 15 (V2).
