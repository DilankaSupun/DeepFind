# DeepFind Test Results Report

**Date:** June 13, 2026
**Component:** DeepFind Search Engine (Python Backend)
**Test Framework:** pytest (Unit Tests) & Custom Scripts (Live Regression)
**Overall Status:** **PASS** (27/27 Tests Passed)

---

## Part 1: Unit & Integration Tests (pytest)

**Command:** `python -m pytest -v -m live_db`
**Status:** **PASS** (18/18)

### Full-Text Search (FTS) Snippet Handling (`test_fts_snippets.py`)
Verifies that search hit highlights (`[[HL]]...[[/HL]]`) are correctly sanitized, merged, and presented safely to the frontend without breaking HTML or being injected maliciously.

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_single_word` | Preserves FTS markers for single-word matches. | ✅ PASS |
| `test_multiple_words` | Correctly handles multiple disjoint highlight matches. | ✅ PASS |
| `test_phrase_query` | Ensures multi-word phrases appear highlighted and in order. | ✅ PASS |
| `test_case_insensitive` | Original casing is preserved when matching case-insensitively. | ✅ PASS |
| `test_unicode_content` | Safe handling of multi-byte characters (e.g., Japanese, Cyrillic). | ✅ PASS |
| `test_html_in_content` | Content containing raw HTML (`<script>`) passes through without execution. | ✅ PASS |
| `test_literal_hl_in_content` | Prevents snippet injection if a file literally contains `[[HL]]` text. | ✅ PASS |
| `test_malformed_markers` | Gracefully handles unbalanced or broken highlight tags. | ✅ PASS |
| `test_metadata_only_snippet` | Generates a valid fallback folder-path snippet if file has no text content. | ✅ PASS |
| `test_pagination_snippets` | Ensures snippets still generate correctly on offset > 0 (Page 2+). | ✅ PASS |
| `test_ranking_regression` | Validates snippet generation does not disrupt exact-match ranking. | ✅ PASS |
| `test_no_n_plus_one` | Verifies the DB connection pool doesn't spam queries per snippet. | ✅ PASS |
| `test_fts_query_builder` | Validates correct SQLite FTS query syntax generation (quotes, ORs). | ✅ PASS |
| `test_snippet_source_preservation` | Ensures the origin tag (`extracted_text` vs `path_context`) is kept. | ✅ PASS |

### SQL Wildcard & Injection Safety (`test_like_wildcard.py`)
Ensures user input is safely parameterized and escaped when querying the SQLite database using `LIKE` clauses.

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_escape_like_function` | Verifies `\`, `%`, and `_` are explicitly escaped. | ✅ PASS |
| `test_search_files_normal_queries` | Normal queries without wildcards resolve accurately. | ✅ PASS |
| `test_wildcard_injection_prevention` | Queries like `a%` do not mistakenly trigger wildcard full-table scans. | ✅ PASS |
| `test_special_chars_no_sql_injection` | Quotes and apostrophes (`' ; DROP TABLE`) are parameterized safely. | ✅ PASS |

---

## Part 2: End-to-End Search Regression

**Command:** `python scripts/maintenance/test_regression_final.py`
**Status:** **PASS** (9/9 Canonical Queries)

These regression tests query the *live production database* to ensure the complex hybrid search (Filename + Structure + Semantic + FTS) correctly parses intents, routes queries, applies filters, and returns accurate file hits quickly.

| Query Target | Intent & Execution Strategy | Hits | Warm Latency | Result |
| :--- | :--- | :--- | :--- | :--- |
| **`dashboard.js`** | Exact filename match | `117` | `~200 ms` | ✅ PASS |
| **`setup.exe`** | Exact executable | `109` | `~201 ms` | ✅ PASS |
| **`IGI`** | App / folder name | `52` | `~162 ms` | ✅ PASS |
| **`report`** | Common stem | `32` | `~329 ms` | ✅ PASS |
| **`assignment`** | Common stem | `98` | `~247 ms` | ✅ PASS |
| **`movie.mp4`** | Exact filename + Extension | `195` | `~363 ms` | ✅ PASS |
| **`pdfs in Ayya folder`** | Structured filter (`folder=ayya`, `ext=.pdf`) | `2` | `~7 ms` | ✅ PASS |
| **`Buddhism and the History of Nursing`** | Multi-word FTS fast-path | `8` | `~411 ms` | ✅ PASS |
| **`payment gateway setup`** | Multi-word semantic fallback | `101` | `~442 ms` | ✅ PASS |

### Verification of Constraints
- **Structured filters strictly applied:** The query "pdfs in Ayya folder" accurately isolated `folder=ayya` and `ext=.pdf`, proving natural language filter extraction is functioning perfectly.
- **Fast paths active:** Filename match queries successfully short-circuited the expensive FAISS semantic lookup, dropping latency well beneath the `500ms` SLA.
