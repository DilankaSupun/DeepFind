"""
DeepFind Engine — FTS5 Full-Text Content Search (Step 10)

Searches extracted_text using the SQLite files_fts virtual table.
Returns ranked results with snippets. No disk scanning. No AI.
Step 11.5: Uses parsed query parts (content_terms) with OR-logic fallback.
Step 25:   Snippet marker safety — literal [[HL]]/[[/HL]] in file content are
           neutralised before returning to the API to prevent fake highlights.
"""

import logging
import re
from database.db import get_connection

log = logging.getLogger(__name__)

SNIPPET_LEN = 250          # characters for snippet preview
MAX_FTS_RESULTS = 200      # internal cap before offset/limit


# ── Public API ─────────────────────────────────────────────────────────────────

def search_content(parsed: dict, limit: int = 50, offset: int = 0) -> dict:
    """
    Run FTS5 full-text search over extracted file content using parsed terms.
    """
    if not parsed.get("normalized"):
        return {"total": 0, "results": [], "no_content": False}

    content_terms = parsed.get("content_terms", [])
    
    # Fallback to metadata/tag terms if no content terms
    if not content_terms:
        content_terms = parsed.get("metadata_terms", []) + parsed.get("tag_terms", [])
        
    if not content_terms:
        # Absolute fallback to normalized words
        content_terms = parsed.get("normalized").split()

    # Deduplicate terms and strip empty
    content_terms = list(dict.fromkeys(w.strip() for w in content_terms if w.strip()))
    if not content_terms:
         return {"total": 0, "results": [], "no_content": False}

    phrase_candidates = parsed.get("phrase_candidates", [])
    
    queries = []
    # 1. Exact Phrase
    if phrase_candidates:
        q_phrase = _build_fts_query([], phrase_candidates=phrase_candidates)
        if q_phrase and q_phrase != '""':
            queries.append((q_phrase, 1, "content_phrase"))
            
    # 2. All Terms (AND)
    if len(content_terms) > 1:
        q_all = _build_fts_query(content_terms, match_all=True)
        if q_all and q_all != '""':
            queries.append((q_all, 2, "content_all_terms"))
            
    # 3. Partial Terms (OR)
    q_partial = _build_fts_query(content_terms, match_all=False)
    if q_partial and q_partial != '""':
        queries.append((q_partial, 3, "content_partial"))
        
    if not queries:
        return {"total": 0, "results": [], "no_content": False}

    orig_q = parsed.get("normalized", "")
    drive_filters = parsed.get("drive_filters", [])
    folder_filters = parsed.get("folder_filters", [])
    folder_phrase_filters = parsed.get("folder_phrase_filters", [])
    date_filters = parsed.get("date_filters", {})

    seen_ids = set()
    combined_results = []
    combined_total = 0
    
    for q_str, tier, source in queries:
        if len(combined_results) >= limit:
            break
            
        remaining_limit = limit - len(combined_results)
        
        try:
            res = _run_fts(q_str, orig_q, content_terms, drive_filters, folder_filters, folder_phrase_filters, date_filters, remaining_limit, offset)
        except Exception as exc:
            log.warning("FTS query failed (%s), retrying with sanitized query: %s", exc, q_str)
            if tier == 3:
                simple = _sanitize_fts(content_terms)
                if not simple:
                    continue
                try:
                    res = _run_fts(simple, orig_q, content_terms, drive_filters, folder_filters, folder_phrase_filters, date_filters, remaining_limit, offset)
                except Exception as exc2:
                    log.error("FTS fallback also failed: %s", exc2)
                    continue
            else:
                continue
                
        for r in res.get("results", []):
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                r["match_tier"] = tier
                r["match_source"] = source
                combined_results.append(r)
                
        combined_total += res.get("total", 0)
        
    return {"total": combined_total, "results": combined_results, "no_content": False}


def check_has_extracted_content() -> bool:
    """Return True if at least one file has status='content_extracted'."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM files WHERE status = 'content_extracted'"
        ).fetchone()
    return (row["n"] if row else 0) > 0


def rebuild_fts_index() -> dict:
    """
    Rebuild the files_fts virtual table from scratch.
    """
    import time
    start = time.monotonic()

    with get_connection() as conn:
        conn.execute("DELETE FROM files_fts")
        conn.execute("""
            INSERT INTO files_fts(rowid, name, path, extracted_text, tags)
            SELECT id, name, path, extracted_text, tags
            FROM files
            WHERE status != 'missing'
              AND extracted_text IS NOT NULL
              AND extracted_text != ''
        """)
        count = conn.execute("SELECT COUNT(*) AS n FROM files_fts").fetchone()["n"]

    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info("FTS index rebuilt: %d rows in %dms", count, elapsed_ms)
    return {"inserted": count, "duration_ms": elapsed_ms}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _run_fts(fts_query: str, original_query: str, content_terms: list, drive_filters: list, folder_filters: list, folder_phrase_filters: list, date_filters: dict, limit: int, offset: int) -> dict:
    """Execute the FTS5 query and return structured results."""

    drive_sql = ""
    params = [fts_query]
    
    if drive_filters:
        d_clauses = []
        for d in drive_filters:
            params.append(f"{d}%")
            d_clauses.append("f.path LIKE ?")
        drive_sql = " AND (" + " OR ".join(d_clauses) + ")"
        
    folder_sql = ""
    if folder_filters:
        f_clauses = []
        for f in folder_filters:
            params.append(f"%{f}%")
            f_clauses.append("f.path LIKE ?")
            
        for fp in folder_phrase_filters:
            params.append(f"%{fp}%")
            f_clauses.append("f.path LIKE ?")
            
        folder_sql = " AND " + " AND ".join(f_clauses)

    date_sql = ""
    fallback_date_sql = ""
    fallback_params = []
    
    if date_filters:
        field = date_filters.get("field", "modified_at")
        if field not in ["modified_at", "created_at", "last_indexed_at"]:
            field = "modified_at"
            
        def _add_date_clauses(fld, pf, curr_params):
            d_sql = ""
            if date_filters.get(f"{pf}after"):
                curr_params.append(date_filters[f"{pf}after"])
                d_sql += f" AND f.{fld} >= ?"
            if date_filters.get(f"{pf}before"):
                curr_params.append(date_filters[f"{pf}before"])
                d_sql += f" AND f.{fld} < ?"
            if date_filters.get(f"{pf}year"):
                y = date_filters[f"{pf}year"]
                curr_params.append(f"{y}-01-01T00:00:00")
                curr_params.append(f"{y+1}-01-01T00:00:00")
                d_sql += f" AND f.{fld} >= ? AND f.{fld} < ?"
            return d_sql
            
        if field == "created_at":
            date_sql = _add_date_clauses("created_at", "created_", params)
            if date_filters.get("fallback_to_modified"):
                fallback_params = params.copy()
                # we need to remove the created_ parameters that were just added to params
                # Actually, wait, simpler to just rebuild params
                fallback_params = [fts_query]
                if drive_filters:
                    for d in drive_filters: fallback_params.append(f"{d}%")
                if folder_filters:
                    for f in folder_filters: fallback_params.append(f"%{f}%")
                if folder_phrase_filters:
                    for fp in folder_phrase_filters: fallback_params.append(f"%{fp}%")
                    
                fallback_date_sql = _add_date_clauses("modified_at", "modified_", fallback_params)
                fallback_params.extend([limit, offset])
        elif field == "last_indexed_at":
            date_sql = _add_date_clauses("last_indexed_at", "indexed_", params)
        else:
            date_sql = _add_date_clauses("modified_at", "modified_", params)

    params.extend([limit, offset])

    def _run_query(d_sql, query_params):
        sql = f"""
            SELECT
                f.id, f.name, f.path, f.extension, f.size, f.modified_at, f.status,
                f.tags,
                rank AS fts_rank,
                snippet(files_fts, 2, '[[HL]]', '[[/HL]]', '...', 40) AS snippet_text
            FROM files_fts
            JOIN files f ON files_fts.rowid = f.id
            WHERE files_fts MATCH ?
              AND f.status != 'missing'
              AND f.extracted_text IS NOT NULL
              AND f.extracted_text != ''
              {drive_sql} {folder_sql} {d_sql}
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        with get_connection() as conn:
            return conn.execute(sql, query_params).fetchall()
            
    rows = _run_query(date_sql, params)
    fallback_used = False
    if not rows and fallback_date_sql:
        rows = _run_query(fallback_date_sql, fallback_params)
        fallback_used = True

    total = offset + limit + 1 if len(rows) == limit else offset + len(rows)
    has_content = total > 0 or check_has_extracted_content()

    results = []
    q_lower = original_query.lower()
    for row in rows:
        d = dict(row)
        tags_str = (d.get("tags") or "").lower()

        # FTS5 returns snippet_text; if the match wasn’t in extracted_text it just
        # returns the start of the text with no markers.
        # We sanitize first (neutralise any literal [[HL]] from file content), then
        # check if real FTS5 highlights are present.
        raw_snippet = d.pop("snippet_text", "") or ""
        raw_snippet = _sanitize_snippet(raw_snippet)
        has_real_highlight = "[[HL]]" in raw_snippet
        snippet = raw_snippet if has_real_highlight else ""

        raw_rank = d.get("fts_rank") or 0
        score = max(0.0, min(1.0, 1.0 / (1.0 + abs(raw_rank))))

        # Note: We aren't loading full extracted_text anymore, so we only loosely match content terms here.
        matched_content = [term for term in content_terms if term in snippet.lower()]
        
        p = d.get("path", "").lower()
        matched_drive = [d_filt for d_filt in drive_filters if p.startswith(d_filt.lower()) or p.startswith(d_filt.lower().replace(":", ""))]
        matched_folder = [f_filt for f_filt in folder_filters if f_filt.lower() in p]
        
        d["exact_name_match"] = False
        d["matched_metadata_terms"] = []
        d["matched_extensions"] = []
        d["matched_tag_terms"] = []
        d["matched_weak_tag_terms"] = []
        d["matched_content_terms"] = matched_content
        
        d["matched_drive_filters"] = matched_drive
        d["matched_folder_filters"] = matched_folder
        d["matched_location"] = bool(matched_drive or matched_folder)
        
        d["matched_date_filter_field"] = None
        has_active_date = date_filters and any(date_filters.get(k) for k in ["modified_after", "modified_year", "created_after", "created_year", "indexed_after", "indexed_year", "modified_before", "created_before", "indexed_before"])
        
        if has_active_date:
            d["matched_date_filter_field"] = "modified_at" if fallback_used else date_filters.get("field", "modified_at")
            d["fallback_to_modified_used"] = fallback_used
            d["matched_date_filter"] = True
        
        # Temp score
        d["score"]          = round(score, 3)
        d["match_type"]     = "content"
        d["snippet"]        = snippet
        if snippet:
            d["snippet_source"] = "extracted_text"
            d["has_content_snippet"] = True
        else:
            d["snippet_source"] = None
            d["has_content_snippet"] = False
        d["size_human"]     = _human_size(d.get("size") or 0)
        results.append(d)

    return {"total": total, "results": results, "no_content": not has_content}


def _build_fts_query(terms: list, phrase_candidates: list = None, match_all: bool = False) -> str:
    """
    Convert a list of terms into a safe FTS5 query.
    If phrase_candidates are provided, it attempts an exact phrase match FIRST.
    Restricts search exclusively to the extracted_text column.
    """
    if phrase_candidates:
        # FTS5 exact phrase syntax: "word1 word2"
        # We take the first candidate
        phrase = phrase_candidates[0]
        cleaned_phrase = re.sub(r'["\'\(\)\*\:\^]', ' ', phrase).strip()
        if cleaned_phrase:
            return f'extracted_text : "{cleaned_phrase}"'

    safe_terms = []
    for term in terms:
        cleaned = re.sub(r'["\'\(\)\*\:\^]', ' ', term).strip()
        if cleaned:
            # We wrap in quotes and add * for prefix match
            safe_terms.append(f'"{cleaned}"*')
            
    if not safe_terms:
        return '""'
        
    operator = " AND " if match_all else " OR "
    query_body = operator.join(safe_terms)
    return f"extracted_text : ({query_body})"


def _sanitize_fts(terms: list) -> str:
    """
    Absolute fallback if FTS syntax error occurs. Just grab the first purely alphanumeric word.
    """
    for term in terms:
        alpha = re.sub(r'[^a-zA-Z0-9]', '', term)
        if alpha:
            return f'extracted_text : "{alpha}"*'
    return '""'


def _sanitize_snippet(snippet: str) -> str:
    """
    Neutralise literal [[HL]] / [[/HL]] that exist in the file's source content
    and would otherwise produce fake highlights in the frontend.

    Strategy (Step 25):
      FTS5 snippet() produces output like:
        "...plain text [[HL]]matched_word[[/HL]] more plain text..."

      The matched segments (between [[HL]]...[[/HL]]) are injected by FTS5
      and are trustworthy.  The non-match segments (outside the markers) are
      verbatim file content and may contain literal [[HL]] / [[/HL]] strings.

      We split on the FTS5 markers using a capture group so that the resulting
      list alternates:  [non-match, match, non-match, match, ...]
      Even indices (0, 2, 4, ...) are non-match (file content) — strip markers.
      Odd indices (1, 3, 5, ...) are matched terms from FTS5 — keep as-is.

      After stripping, we reassemble with the real markers.
    """
    if not snippet or ("[[HL]]" not in snippet and "[[/HL]]" not in snippet):
        return snippet

    # Split while capturing the content between markers
    parts = re.split(r"\[\[HL\]\](.*?)\[\[/HL\]\]", snippet)
    # parts[0], parts[1], parts[2], ... = non-match, match, non-match, match, ...

    sanitized_parts: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Non-match segment: strip any literal [[HL]]/[[/HL]] from file content
            # Replace with a visually neutral equivalent so the text is still readable
            clean = part.replace("[[HL]]", "[HL]").replace("[[/HL]]", "[/HL]")
            sanitized_parts.append(clean)
        else:
            # Match segment injected by FTS5: wrap with real markers
            sanitized_parts.append(f"[[HL]]{part}[[/HL]]")

    return "".join(sanitized_parts)


def _make_snippet(text: str, q: str, length: int) -> str:
    """
    Create a short preview snippet centered around the first occurrence of the query.
    If the query has multiple words, we just search for the first term for the snippet.
    """
    if not text:
        return ""
    
    first_term = q.split()[0] if q else ""
    idx = text.lower().find(first_term) if first_term else -1
    
    if idx == -1:
        snippet = text[:length].replace("\n", " ").strip()
        return snippet + "..." if len(text) > length else snippet

    start = max(0, idx - (length // 2))
    end = start + length

    snippet = text[start:end].replace("\n", " ")
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet.strip()


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
