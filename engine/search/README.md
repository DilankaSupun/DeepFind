# engine/search/

This module will contain **all search logic**.

## Planned Files (Steps 8, 10, 16)

- `filename_search.py` — Search file name, path, extension from metadata index
- `fts_search.py` — SQLite FTS5 full-text content search
- `tag_search.py` — Tag-based search and filtering
- `hybrid_search.py` — Merge and rank results from all search signals
- `ranker.py` — Scoring engine with the hybrid ranking formula
- `explainer.py` — Generate human-readable match explanations

## Hybrid Ranking Formula

```
Final Score =
  filename_score  * 0.30
+ tag_score       * 0.20
+ content_score   * 0.25
+ semantic_score  * 0.20   ← 0 in V1
+ recency_score   * 0.05
```

## Search Rules

- Search must only use pre-built indexes
- Never scan folders during live search
- Never extract text during live search
- Return top 20–50 results
- Include match explanation for every result

> ⏳ Not implemented yet — awaiting Step 8.
