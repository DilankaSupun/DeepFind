"""
DeepFind Engine — Filename / Path / Extension Search

Uses parameterized SQLite LIKE queries for metadata-only search.
Step 11.5: Uses parsed query parts (metadata_terms, extension_filters, tag_terms)
Step 23: Stabilized Search Recall with Bucketed Queries
"""

import logging
from database.db import get_connection
from scanner.scan_scope_utils import filter_allowed_files

log = logging.getLogger(__name__)

def search_files(parsed: dict, limit: int = 50, offset: int = 0) -> dict:
    """
    Search the files table using bucketed relevance queries to guarantee exact recall.
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
    folder_phrase_filters = parsed.get("folder_phrase_filters", [])
    date_filters = parsed.get("date_filters", {})
    literal_terms = parsed.get("literal_terms", [])
    
    # Fallback
    if not meta_terms and not ext_filters and not tag_terms and not weak_tag_terms and not literal_terms:
        meta_terms = content_terms

    combined_terms = list(set(meta_terms + literal_terms))
    
    # Build date/location SQL filters that apply to ALL buckets
    loc_sql, loc_params = _build_location_sql(drive_filters, folder_filters, folder_phrase_filters)
    date_sql, date_params, fallback_date_sql, fallback_date_params, matched_date_field, matched_fallback_field = _build_date_sql(date_filters)
    
    base_filters = f"status != 'missing' {loc_sql}"
    base_params = list(loc_params)

    # We will collect rows in a dict by ID to deduplicate
    by_id = {}
    
    def _execute_bucket(bucket_name, sql_condition, params, limit_per_bucket=100):
        # We try main date filter
        full_sql = f"""
            SELECT id, path, name, extension, size, created_at, modified_at, status, tags
            FROM files
            WHERE {base_filters} {date_sql} AND {sql_condition}
            ORDER BY modified_at DESC LIMIT ?
        """
        full_params = base_params + date_params + params + [limit_per_bucket]
        
        with get_connection() as conn:
            rows = conn.execute(full_sql, full_params).fetchall()
            
            # Fallback date filter if no results
            if not rows and fallback_date_sql:
                full_sql = f"""
                    SELECT id, path, name, extension, size, created_at, modified_at, status, tags
                    FROM files
                    WHERE {base_filters} {fallback_date_sql} AND {sql_condition}
                    ORDER BY modified_at DESC LIMIT ?
                """
                full_params = base_params + fallback_date_params + params + [limit_per_bucket]
                rows = conn.execute(full_sql, full_params).fetchall()
                
            for row in rows:
                fid = row["id"]
                if fid not in by_id:
                    d = dict(row)
                    d["candidate_sources"] = [bucket_name]
                    by_id[fid] = d
                else:
                    if bucket_name not in by_id[fid]["candidate_sources"]:
                        by_id[fid]["candidate_sources"].append(bucket_name)

    # ── BUCKET 1: Exact Name ──────────────────────────────────────────────────
    for term in combined_terms:
        _execute_bucket("exact_name", "lower(name) = lower(?)", [term], 50)
        
    # ── BUCKET 2: Exact Stem (Name without extension) ─────────────────────────
    for term in combined_terms:
        # Match where name is exactly term + . + anything
        _execute_bucket("exact_stem", "lower(name) LIKE lower(?)", [f"{term}.%"], 50)
        
    # ── BUCKET 3: Exact Folder Segment ────────────────────────────────────────
    for term in combined_terms:
        # Match where path contains /term/ or \term\
        _execute_bucket("exact_folder", "(lower(path) LIKE lower(?) OR lower(path) LIKE lower(?))", [f"%/{term}/%", f"%\\{term}\\%"], 50)
        
    # ── BUCKET 4: Extension Matches ───────────────────────────────────────────
    for ext in ext_filters:
        ext_clean = ext if ext.startswith(".") else f".{ext}"
        _execute_bucket("extension_match", "lower(extension) = lower(?)", [ext_clean], limit * 2)

    # ── BUCKET 5: Name Contains ───────────────────────────────────────────────
    for term in combined_terms:
        _execute_bucket("name_contains", "lower(name) LIKE lower(?)", [f"%{term}%"], limit * 2)

    # ── BUCKET 6: Tag Match ───────────────────────────────────────────────────
    for term in tag_terms + weak_tag_terms:
        _execute_bucket("tag_match", "lower(tags) LIKE lower(?)", [f"%{term}%"], limit * 2)

    # ── BUCKET 7: Path Segment (lower priority) ───────────────────────────────
    for term in combined_terms:
        _execute_bucket("path_segment", "lower(path) LIKE lower(?)", [f"%{term}%"], limit * 2)

    # Convert merged rows to list
    results = list(by_id.values())
    
    # ── EXCLUSION FILTERING ───────────────────────────────────────────────────
    # Enforce scan scope filtering before we even pass to hybrid engine
    results = filter_allowed_files(results, path_key="path")

    # Final post-processing (attach match boolean flags for hybrid scoring)
    for d in results:
        n = (d.get("name") or "").lower()
        p = (d.get("path") or "").lower()
        e = (d.get("extension") or "").lower()
        t = (d.get("tags") or "").lower()
        
        d["exact_name_match"] = "exact_name" in d["candidate_sources"]
        d["exact_stem_match"] = "exact_stem" in d["candidate_sources"]
        d["exact_folder_match"] = "exact_folder" in d["candidate_sources"]
        
        # Track literal match arrays for highlighting
        d["matched_metadata_terms"] = [m for m in meta_terms if m in n or m in p]
        d["matched_extensions"] = [ext for ext in ext_filters if e == (ext if ext.startswith(".") else f".{ext}")]
        d["matched_tag_terms"] = [tag for tag in tag_terms if tag in t or tag in n]
        d["matched_weak_tag_terms"] = [tag for tag in weak_tag_terms if tag in t]
        d["matched_literal_terms"] = [lit for lit in literal_terms if lit in n or lit in p]
        d["matched_content_terms"] = []
        
        matched_drive = [dr for dr in drive_filters if p.startswith(dr.lower()) or p.startswith(dr.lower().replace(":", ""))]
        matched_folder = [f for f in folder_filters if f.lower() in p]
        d["matched_drive_filters"] = matched_drive
        d["matched_folder_filters"] = matched_folder
        d["matched_location"] = bool(matched_drive or matched_folder)
        d["folder_phrase_match"] = any(fp.lower() in p for fp in folder_phrase_filters)
        
        d["size_human"] = _human_size(d.get("size") or 0)
        d["item_type"] = "file"
        d["dedupe_key"] = f"file:{p}"
        d["score"] = 0.0

    log.debug("Metadata search bucketed fetch: %d unique allowed results", len(results))
    
    # We don't limit/offset here, we let hybrid_search handle it after scoring
    return {"total": len(results), "results": results}


def _build_location_sql(drive_filters, folder_filters, folder_phrase_filters):
    sql = ""
    params = []
    
    if drive_filters:
        d_clauses = []
        for d in drive_filters:
            d_clauses.append("path LIKE ?")
            params.append(f"{d}%")
        sql += " AND (" + " OR ".join(d_clauses) + ")"
        
    if folder_filters or folder_phrase_filters:
        f_clauses = []
        for f in folder_filters:
            f_clauses.append("path LIKE ?")
            params.append(f"%{f}%")
        for fp in folder_phrase_filters:
            f_clauses.append("path LIKE ?")
            params.append(f"%{fp}%")
        sql += " AND " + " AND ".join(f_clauses)
        
    return sql, params


def _build_date_sql(date_filters):
    if not date_filters:
        return "", [], "", [], None, None
        
    field = date_filters.get("field", "modified_at")
    if field not in ["modified_at", "created_at", "last_indexed_at"]:
        field = "modified_at"
        
    def _create_clauses(fld, pf):
        s = ""
        p = []
        if date_filters.get(f"{pf}after"):
            s += f" AND {fld} >= ?"
            p.append(date_filters[f"{pf}after"])
        if date_filters.get(f"{pf}before"):
            s += f" AND {fld} < ?"
            p.append(date_filters[f"{pf}before"])
        if date_filters.get(f"{pf}year"):
            y = date_filters[f"{pf}year"]
            s += f" AND {fld} >= ? AND {fld} < ?"
            p.extend([f"{y}-01-01T00:00:00", f"{y+1}-01-01T00:00:00"])
        return s, p

    date_sql, date_params = "", []
    fallback_date_sql, fallback_date_params = "", []
    matched_field = field
    matched_fallback_field = None
    
    if field == "created_at":
        date_sql, date_params = _create_clauses("created_at", "created_")
        if date_filters.get("fallback_to_modified"):
            fallback_date_sql, fallback_date_params = _create_clauses("modified_at", "modified_")
            matched_fallback_field = "modified_at"
    elif field == "last_indexed_at":
        date_sql, date_params = _create_clauses("last_indexed_at", "indexed_")
    else:
        date_sql, date_params = _create_clauses("modified_at", "modified_")
        
    return date_sql, date_params, fallback_date_sql, fallback_date_params, matched_field, matched_fallback_field


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
