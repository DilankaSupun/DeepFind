"""
DeepFind Engine — Filename / Path / Extension Search

Uses parameterized SQLite LIKE queries for metadata-only search.
Step 11.5: Uses parsed query parts (metadata_terms, extension_filters, tag_terms)
"""

import logging
from database.db import get_connection

log = logging.getLogger(__name__)


def search_files(parsed: dict, limit: int = 50, offset: int = 0) -> dict:
    """
    Search the files table by name, extension, and tags using parsed terms.
    """
    if not parsed.get("normalized"):
        return {"total": 0, "results": []}

    meta_terms = parsed.get("metadata_terms", [])
    ext_filters = parsed.get("extension_filters", [])
    tag_terms = parsed.get("tag_terms", [])
    content_terms = parsed.get("content_terms", [])
    weak_tag_terms = parsed.get("weak_tag_terms", [])
    drive_filters = parsed.get("drive_filters", [])
    folder_filters = parsed.get("folder_filters", [])
    
    # Fallback to content terms if nothing else is available
    if not meta_terms and not ext_filters and not tag_terms and not weak_tag_terms:
        meta_terms = content_terms

    params = {"limit": limit, "offset": offset}
    where_clauses = []
    
    # 1. Metadata terms
    for i, t in enumerate(meta_terms):
        p_name = f"m_{i}"
        params[p_name] = f"%{t}%"
        params[f"{p_name}_exact"] = t
        params[f"{p_name}_start"] = f"{t}%"
        
        where_clauses.append(f"(name LIKE :{p_name} OR path LIKE :{p_name})")

    # 2. Extension filters
    for i, ext in enumerate(ext_filters):
        e_name = f"e_{i}"
        ext_clean = ext if ext.startswith(".") else f".{ext}"
        params[e_name] = ext_clean
        
        where_clauses.append(f"extension = :{e_name}")

    # 3. Tag terms
    for i, tag in enumerate(tag_terms):
        t_name = f"t_{i}"
        params[t_name] = f"%{tag}%"
        
        where_clauses.append(f"tags LIKE :{t_name}")

    # 4. Weak tag terms
    for i, tag in enumerate(weak_tag_terms):
        w_name = f"w_{i}"
        params[w_name] = f"%{tag}%"
        
        where_clauses.append(f"tags LIKE :{w_name}")

    drive_sql = ""
    if drive_filters:
        d_clauses = []
        for i, d in enumerate(drive_filters):
            d_name = f"d_{i}"
            params[d_name] = f"{d}%"
            d_clauses.append(f"path LIKE :{d_name}")
        drive_sql = " AND (" + " OR ".join(d_clauses) + ")"
        
    folder_sql = ""
    if folder_filters:
        f_clauses = []
        for i, f in enumerate(folder_filters):
            f_name = f"f_{i}"
            # acceptable simpler approach: lower(path) LIKE '%downloads%' -> sqlite LIKE is case insensitive
            params[f_name] = f"%{f}%"
            f_clauses.append(f"path LIKE :{f_name}")
        folder_sql = " AND " + " AND ".join(f_clauses)

    if not where_clauses and not drive_filters and not folder_filters:
        return {"total": 0, "results": []}

    term_sql = "(" + " OR ".join(where_clauses) + ")" if where_clauses else "1=1"
    
    sql = f"""
        SELECT
            id, path, name, extension, size, created_at, modified_at, status, tags
        FROM files
        WHERE status != 'missing' AND {term_sql} {drive_sql} {folder_sql}
        ORDER BY modified_at DESC
        LIMIT :limit OFFSET :offset
    """

    with get_connection() as conn:
        rows  = conn.execute(sql, params).fetchall()

    total = offset + limit + 1 if len(rows) == limit else offset + len(rows)
    results = []
    for row in rows:
        d = dict(row)
        n = (d.get("name") or "").lower()
        p = (d.get("path") or "").lower()
        e = (d.get("extension") or "").lower()
        t = (d.get("tags") or "").lower()
        
        matched_meta = [m for m in meta_terms if m in n or m in p]
        matched_exts = [ext for ext in ext_filters if e == (ext if ext.startswith(".") else f".{ext}")]
        matched_tags = [tag for tag in tag_terms if tag in t or tag in n]
        matched_weak_tags = [tag for tag in weak_tag_terms if tag in t]
        
        # Check location matches
        matched_drive = [d for d in drive_filters if p.startswith(d.lower()) or p.startswith(d.lower().replace(":", ""))]
        matched_folder = [f for f in folder_filters if f.lower() in p]

        # Ensure exact match is captured
        exact_name_match = any(n == m for m in meta_terms)
        d["exact_name_match"] = exact_name_match

        d["matched_metadata_terms"] = matched_meta
        d["matched_extensions"] = matched_exts
        d["matched_tag_terms"] = matched_tags
        d["matched_weak_tag_terms"] = matched_weak_tags
        d["matched_content_terms"] = []
        
        d["matched_drive_filters"] = matched_drive
        d["matched_folder_filters"] = matched_folder
        d["matched_location"] = bool(matched_drive or matched_folder)
        
        # Base score from DB is removed, will be calculated in hybrid search
        d["score"] = 0.2
        d["size_human"] = _human_size(d.get("size") or 0)
        results.append(d)

    log.debug("Search metadata: %d total, returning %d", total, len(results))
    return {"total": total, "results": results}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
