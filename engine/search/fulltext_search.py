"""
DeepFind Engine — FTS5 Full-Text Content Search (Step 10)

Searches extracted_text using the SQLite files_fts virtual table.
Returns ranked results with snippets. No disk scanning. No AI.
Step 11.5: Uses parsed query parts (content_terms) with OR-logic fallback.
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

    fts_query = _build_fts_query(content_terms)
    
    # Extract original string for snippet generation
    orig_q = parsed.get("normalized", "")
    
    drive_filters = parsed.get("drive_filters", [])
    folder_filters = parsed.get("folder_filters", [])

    try:
        return _run_fts(fts_query, orig_q, content_terms, drive_filters, folder_filters, limit, offset)
    except Exception as exc:
        log.warning("FTS query failed (%s), retrying with sanitized query: %s", exc, fts_query)
        # Fall back to single-token OR query
        simple = _sanitize_fts(content_terms)
        if not simple:
            return {"total": 0, "results": [], "no_content": False}
        try:
            return _run_fts(simple, orig_q, content_terms, drive_filters, folder_filters, limit, offset)
        except Exception as exc2:
            log.error("FTS fallback also failed: %s", exc2)
            return {"total": 0, "results": [], "no_content": False}


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
        """)
        count = conn.execute("SELECT COUNT(*) AS n FROM files_fts").fetchone()["n"]

    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info("FTS index rebuilt: %d rows in %dms", count, elapsed_ms)
    return {"inserted": count, "duration_ms": elapsed_ms}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _run_fts(fts_query: str, original_query: str, content_terms: list, drive_filters: list, folder_filters: list, limit: int, offset: int) -> dict:
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
        folder_sql = " AND " + " AND ".join(f_clauses)

    params.extend([limit, offset])

    sql = f"""
        SELECT
            f.id, f.name, f.path, f.extension, f.size, f.modified_at, f.status,
            f.tags,
            rank AS fts_rank,
            snippet(files_fts, 2, '', '', '...', 40) AS snippet_text
        FROM files_fts
        JOIN files f ON files_fts.rowid = f.id
        WHERE files_fts MATCH ?
          AND f.status != 'missing'
          {drive_sql} {folder_sql}
        ORDER BY rank
        LIMIT ? OFFSET ?
    """

    with get_connection() as conn:
        rows  = conn.execute(sql, params).fetchall()

    total = offset + limit + 1 if len(rows) == limit else offset + len(rows)
    has_content = total > 0 or check_has_extracted_content()

    results = []
    q_lower = original_query.lower()
    for row in rows:
        d = dict(row)
        tags_str = (d.get("tags") or "").lower()

        # FTS5 returns a snippet_text without formatting (using empty string boundaries)
        snippet = d.pop("snippet_text", "") or ""

        raw_rank = d.get("fts_rank") or 0
        score = max(0.0, min(1.0, 1.0 / (1.0 + abs(raw_rank))))

        # Note: We aren't loading full extracted_text anymore, so we only loosely match content terms here.
        # Strict matching would require FTS highlight data or keeping full text. We use the snippet for a quick check.
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
        
        # Temp score
        d["score"]          = round(score, 3)
        d["match_type"]     = "content"
        d["snippet"]        = snippet
        d["size_human"]     = _human_size(d.get("size") or 0)
        results.append(d)

    return {"total": total, "results": results, "no_content": not has_content}


def _build_fts_query(terms: list) -> str:
    """
    Convert a list of terms into a safe FTS5 query using OR.
    """
    safe_terms = []
    for term in terms:
        cleaned = re.sub(r'["\'\(\)\*\:\^]', ' ', term).strip()
        if cleaned:
            # We wrap in quotes and add * for prefix match
            safe_terms.append(f'"{cleaned}"*')
            
    if not safe_terms:
        return '""'
        
    return " OR ".join(safe_terms)


def _sanitize_fts(terms: list) -> str:
    """
    Absolute fallback if FTS syntax error occurs. Just grab the first purely alphanumeric word.
    """
    for term in terms:
        alpha = re.sub(r'[^a-zA-Z0-9]', '', term)
        if alpha:
            return f'"{alpha}"*'
    return '""'


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
