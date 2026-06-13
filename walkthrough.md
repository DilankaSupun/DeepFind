# Step 25 — FTS Highlighting Snippets + LIKE Wildcard Safety: Walkthrough

## Files Changed

| File | Type | Summary |
|------|------|---------|
| [`engine/search/like_utils.py`](file:///d:/External Works/Portfolio/FileMind/DeepFind/engine/search/like_utils.py) | NEW | `escape_like()` helper — escapes `%`, `_`, `\` in user-supplied terms |
| [`engine/search/filename_search.py`](file:///d:/External Works/Portfolio/FileMind/DeepFind/engine/search/filename_search.py) | MODIFY | Import + apply `escape_like()` to all 6 user-term LIKE patterns; add `ESCAPE '\\'` clause; define `_LIKE_ESC` constant |
| [`engine/search/fulltext_search.py`](file:///d:/External Works/Portfolio/FileMind/DeepFind/engine/search/fulltext_search.py) | MODIFY | Add `_sanitize_snippet()` — neutralises literal `[[HL]]`/`[[/HL]]` in non-match segments of FTS output |
| [`engine/search/hybrid_search.py`](file:///d:/External Works/Portfolio/FileMind/DeepFind/engine/search/hybrid_search.py) | MODIFY | Preserve `snippet_source` in `_calculate_score()`; add `_add_path_fallback_snippet()`; call it in all 3 search paths |
| [`app/frontend/src/components/SearchResults/SearchResults.jsx`](file:///d:/External Works/Portfolio/FileMind/DeepFind/app/frontend/src/components/SearchResults/SearchResults.jsx) | MODIFY | Add `path_context` label ("Location") and skip `renderHighlightedText` for location snippets |
| [`app/frontend/src/components/SearchResults/SearchResults.css`](file:///d:/External Works/Portfolio/FileMind/DeepFind/app/frontend/src/components/SearchResults/SearchResults.css) | MODIFY | Add `.result-card__snippet--location` variant + `.result-card--missing` style |
| [`tests/test_fts_snippets.py`](file:///d:/External Works/Portfolio/FileMind/DeepFind/tests/test_fts_snippets.py) | NEW | 49 FTS snippet tests (all 12 required scenarios + extras) |
| [`tests/test_like_wildcard.py`](file:///d:/External Works/Portfolio/FileMind/DeepFind/tests/test_like_wildcard.py) | NEW | 30 LIKE wildcard safety tests |

---

## Backend Snippet-Generation Flow

```
User query: "Buddhism and the History of Nursing"
        │
        ▼
query_parser.parse_query()
  → content_terms: ["buddhism", "nursing", "history"]
  → phrase_candidates: ["Buddhism and the History of Nursing"]
        │
        ▼
fulltext_search.search_content()
  → _build_fts_query(terms, phrase_candidates)
      → SQL: extracted_text : "Buddhism and the History of Nursing"
  → SQLite FTS5 query with:
      snippet(files_fts, 2, '[[HL]]', '[[/HL]]', '...', 40)
  → raw_snippet = "...the [[HL]]history[[/HL]] of [[HL]]nursing[[/HL]] was..."
  → _sanitize_snippet(raw_snippet)
      → splits on [[HL]]..[[/HL]] pairs
      → strips any literal [[HL]] from non-match segments (file content)
      → reassembles with real FTS markers intact
  → has_real_highlight = True  → snippet = sanitised text
  → snippet_source = "extracted_text"
        │
        ▼
hybrid_search.unified_search()
  → merge content result into by_id dict
  → _calculate_score(r, parsed)
      → does NOT overwrite snippet_source (guard: "if 'snippet_source' not in r")
  → _add_path_fallback_snippet(r)
      → only called if r.get("snippet") is falsy
      → for content results: skipped (snippet already set)
        │
        ▼
API: /search response
  → result["snippet"]        = "...the [[HL]]history[[/HL]] of [[HL]]nursing[[/HL]]..."
  → result["snippet_source"] = "extracted_text"
```

**Metadata-only result flow** (e.g. `dashboard.js`):
```
search_files() → no snippet field set
hybrid_search() → _calculate_score() → no snippet
              → _add_path_fallback_snippet(r)
                  → path = "C:/Projects/frontend/dashboard.js"
                  → preview = "frontend / dashboard.js"
                  → r["snippet"] = "frontend / dashboard.js"
                  → r["snippet_source"] = "path_context"
API: result["snippet"] = "frontend / dashboard.js"
     result["snippet_source"] = "path_context"
```

---

## Frontend Marker-Parsing Flow

```
result.snippet = "...the [[HL]]history[[/HL]] of [[HL]]nursing[[/HL]] was..."
result.snippet_source = "extracted_text"
        │
        ▼
ResultCard renders:
  <span className="result-card__snippet-label">Content preview:</span>
  <p className="result-card__snippet">
    {renderHighlightedText(file.snippet)}
  </p>

renderHighlightedText():
  text.split(/\[\[HL\]\](.*?)\[\[\/HL\]\]/g)
  → ["...the ", "history", " of ", "nursing", " was..."]
  → parts[0] → <span>...the </span>
  → parts[1] → <mark className="highlighted-term">history</mark>
  → parts[2] → <span> of </span>
  → parts[3] → <mark className="highlighted-term">nursing</mark>
  → parts[4] → <span> was...</span>
```

**Path-context snippet** (`snippet_source = "path_context"`):
```jsx
<span className="result-card__snippet-label">Location:</span>
<p className="result-card__snippet result-card__snippet--location">
  {file.snippet}   ← plain text, React escapes it naturally
</p>
```

**No `dangerouslySetInnerHTML` used anywhere.** React's JSX renders all file content as text nodes.

---

## Security Safeguards

| Threat | Mitigation |
|--------|-----------|
| LIKE `%`, `_` wildcard injection | `escape_like()` applied to all 6 user-term LIKE patterns; `ESCAPE '\\'` added to all affected clauses |
| LIKE `\` injection | `escape_like()` escapes `\` first (before `%` and `_`) to prevent double-escape issues |
| SQL injection | All queries use parameterised `?` placeholders — unchanged from before |
| HTML injection in snippet content | Backend returns `[[HL]]` markers, not HTML. React escapes all string children natively. |
| Marker injection from file content | `_sanitize_snippet()` splits on real FTS5 markers (alternating non-match/match pattern) and strips any `[[HL]]`/`[[/HL]]` found in non-match segments |
| XSS via path/filename | React renders as text nodes — escaped automatically |
| `None`/`null` snippet | `_add_path_fallback_snippet()` always sets a string; FTS path is guarded with `or ""` |

---

## Fallback Behaviour

| Situation | Snippet value | `snippet_source` | Frontend label |
|-----------|--------------|------------------|---------------|
| FTS5 content match with highlights | `"...[[HL]]word[[/HL]]..."` | `"extracted_text"` | "Content preview" |
| FTS5 content match, no highlights in snippet | `""` (discarded) | → falls through to path fallback | |
| Semantic match with chunk | `"semantic chunk text"` | `"semantic_chunk"` | "Semantic preview" |
| Metadata-only match | `"ParentFolder / filename.ext"` | `"path_context"` | "Location" |
| Empty path | `""` (nothing set) | not set | snippet not rendered |

---

## Query Count / Performance Impact

**Zero additional queries per result:**
- FTS5 `snippet()` is computed by SQLite as part of the single FTS query — no extra round-trip
- `_sanitize_snippet()` is pure Python string processing — no I/O
- `_add_path_fallback_snippet()` uses the already-loaded `path` field — no query

**Step 24 performance preserved after Step 25 changes (warm avg, 5 runs):**

| Query | Step 24 warm | Step 25 warm | Delta |
|-------|-------------|-------------|-------|
| `dashboard.js` | 208ms | 203ms | -5ms |
| `setup.exe` | 187ms | 200ms | +13ms |
| `IGI` | 145ms | 160ms | +15ms |
| `report` | 335ms | 320ms | -15ms |
| `assignment` | 292ms | 245ms | -47ms |
| `movie.mp4` | 379ms | 359ms | -20ms |
| `pdfs in Ayya folder` | 8ms | 8ms | 0ms |

All timings within normal measurement variance. No material regression.

> [!NOTE]
> `dashboard.js` at 203ms is near-target, not strictly meeting <200ms. This is a correct characterisation — the measurement at 208ms in the Step 24 report was similarly near-target.

---

## Tests Added and Results

### LIKE Wildcard Tests (`tests/test_like_wildcard.py`) — 30 PASS / 0 FAIL

| Category | Tests | Result |
|----------|-------|--------|
| `escape_like()` unit: `%`, `_`, `\`, apostrophe, quote, unicode, combined | 14 | ✅ All pass |
| Normal query correctness after escaping (dashboard.js, setup.exe, IGI, report) | 4 | ✅ All pass |
| Wildcard injection prevention (`%`, `_`, backslash queries) | 4 | ✅ All pass |
| SQL injection safety (apostrophes, quotes, SQL DROP statement) | 8 | ✅ All pass |

### FTS Snippet Tests (`tests/test_fts_snippets.py`) — 49 PASS / 0 FAIL

| Test | Result |
|------|--------|
| 1. Single matching word — `[[HL]]` preserved | ✅ |
| 2. Multiple matching words — 2 HL pairs in snippet | ✅ |
| 3. Phrase query — all terms highlighted in order | ✅ |
| 4. Different letter casing — original casing preserved | ✅ |
| 5. Unicode (Japanese, Cyrillic) — highlights work | ✅ |
| 6. HTML `<script>` in content — returned as literal text, no `<mark>` | ✅ |
| 7. Literal `[[HL]]` in file content — unmatched markers neutralised | ✅ |
| 8. Malformed/unbalanced markers — no exception, safe return | ✅ |
| 9. Metadata-only result — path_context snippet, no None/null | ✅ |
| 10. Pagination — stable total count across pages | ✅ |
| 11. No ranking regression — exact_name captured; IGI direct matches in top 5 | ✅ |
| 12. No N+1 — 4 DB calls for limit=50 and limit=10 (constant) | ✅ |
| FTS query builder — OR logic, column restriction, quoting | ✅ |
| snippet_source preservation — `extracted_text` guard, path_context fallback | ✅ |

### Regression Queries (all from `test_regression_final.py`) — All return results ✅

| Query | Hits | Warm avg | Notes |
|-------|------|---------|-------|
| `dashboard.js` | 115 | 203ms | Near-target (<200ms) |
| `setup.exe` | 109 | 200ms | Near-target |
| `IGI` | 52 | 160ms | ✅ <300ms |
| `report` | 32 | 320ms | ✅ <500ms |
| `assignment` | 98 | 245ms | ✅ <300ms |
| `movie.mp4` | 195 | 359ms | ⚠️ ~359ms (target 300ms; no exact name match) |
| `pdfs in Ayya folder` | 2 | 8ms | ✅ all_pdf=True, all_in_ayya=True |
| `Buddhism and the History of Nursing` | 8 | 418ms | ✅ returns results |
| `payment gateway setup` | 101 | 449ms | ✅ returns results |

---

## Step 24 Verification Fixes Applied

1. **`dashboard.js` 208ms** — corrected in all reports to "near-target", not strictly meeting `<200ms`. The warm average oscillates between 197–208ms depending on OS scheduling; this is acceptable and well below the pre-Step 24 baseline of 932ms.

2. **LIKE wildcard handling** — confirmed not escaped before Step 25. Now fixed with `escape_like()` across all 6 user-term LIKE patterns. Verified with both unit tests and live DB queries.

---

## Limitations

1. **`movie.mp4` ~359ms warm** — still above the 300ms target. Root cause: 7 video extension aliases + no exact `movie.mp4` filename in the index means all 5 buckets run. Cannot be reduced further without pruning the video alias list in `file_type_registry.py`.

2. **FTS snippets only show for content-extracted files** — files without extracted text will only show the path-context snippet. This is by design; the user must run Content Extraction to enable content snippets.

3. **`_sanitize_snippet()` preserves both FTS markers and content markers that appear as FTS matches** — if a file contains exactly `[[HL]]word[[/HL]]` and FTS5 also matches `word`, the output will show `word` as a highlight from both sources. This is harmless (correctly highlighted) but technically not distinguishable as "from content injection". It is safe because the markers appear inside a `[[HL]]..[[/HL]]` pair, not as unmatched text.

4. **Pagination** — `search_files()` does not slice by offset; the hybrid layer handles offset/limit. The path-fallback snippet is applied after scoring, so paginated results at offset > 0 also receive path-context snippets.
