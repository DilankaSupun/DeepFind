r"""
DeepFind Engine — Filename / Path / Extension Search

Uses parameterized SQLite LIKE queries for metadata-only search.
Step 11.5:  Uses parsed query parts (metadata_terms, extension_filters, tag_terms)
Step 23:    Stabilized Search Recall with Bucketed Queries
Step 24:    Exact Metadata Fast Path — merged buckets, expression-index alignment,
            early-exit on strong direct matches to dramatically reduce round-trips.
Step 25:    LIKE wildcard safety — all user-supplied terms are escaped with
            escape_like() before embedding in LIKE patterns, preventing
            unintended wildcard expansion from %, _, and \ in filenames.
"""

import logging
import time
from database.db import get_connection
from scanner.scan_scope_utils import filter_allowed_files
from search.like_utils import escape_like

log = logging.getLogger(__name__)

# SQLite ESCAPE character for LIKE patterns.
# In Python: "ESCAPE '\\'" produces the SQL text:  ESCAPE '\'
# SQLite requires exactly one character after ESCAPE.
_LIKE_ESC = "ESCAPE '\\'"


def search_files(parsed: dict, limit: int = 50, offset: int = 0) -> dict:
    """
    Search the files table using bucketed relevance queries.

    Optimisation path (Step 24):
      1. Run exact-name + exact-stem fast-path in a SINGLE merged query.
         If enough strong direct-match candidates are found, skip the
         expensive broad LIKE and path-segment scans entirely.
      2. Run name-prefix / name-contains / extension / tag / path-segment
         buckets only when the fast-path did not yield sufficient results.
      3. Each term-group fires a SINGLE query rather than one query per
         bucket per term, cutting the number of SQLite round-trips.
    """
    if not parsed.get("normalized"):
        return {"total": 0, "results": []}

    meta_terms        = parsed.get("metadata_terms", [])
    ext_filters       = parsed.get("extension_filters", [])
    tag_terms         = parsed.get("tag_terms", [])
    content_terms     = parsed.get("content_terms", [])
    weak_tag_terms    = parsed.get("weak_tag_terms", [])
    drive_filters     = parsed.get("drive_filters", [])
    folder_filters    = parsed.get("folder_filters", [])
    folder_phrase_filters = parsed.get("folder_phrase_filters", [])
    date_filters      = parsed.get("date_filters", {})
    literal_terms     = parsed.get("literal_terms", [])

    # Fallback: if nothing usable, promote content_terms to metadata_terms
    if not meta_terms and not ext_filters and not tag_terms and not weak_tag_terms and not literal_terms:
        meta_terms = content_terms

    combined_terms = list(dict.fromkeys(meta_terms + literal_terms))  # deduplicated, ordered

    # Pre-build shared filter clauses (location + date)
    loc_sql, loc_params = _build_location_sql(drive_filters, folder_filters, folder_phrase_filters)
    (date_sql, date_params,
     fallback_date_sql, fallback_date_params,
     _matched_date_field, _matched_fallback_field) = _build_date_sql(date_filters)

    base_where = f"status != 'missing'{loc_sql}"
    base_params = list(loc_params)

    # Accumulate unique rows keyed by file id
    by_id: dict[int, dict] = {}
    bucket_timings: dict[str, float] = {}

    # ── Shared query executor ────────────────────────────────────────────────

    def _run(bucket_name: str, condition: str, extra_params: list, cap: int) -> None:
        """Execute one bucket query and merge results into by_id."""
        t0 = time.monotonic()
        sql = f"""
            SELECT id, path, name, extension, size, created_at, modified_at, status, tags
            FROM files
            WHERE {base_where} {date_sql} AND {condition}
            ORDER BY modified_at DESC
            LIMIT ?
        """
        params = base_params + date_params + extra_params + [cap]

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

            # Fallback date if no results
            if not rows and fallback_date_sql:
                fb_sql = f"""
                    SELECT id, path, name, extension, size, created_at, modified_at, status, tags
                    FROM files
                    WHERE {base_where} {fallback_date_sql} AND {condition}
                    ORDER BY modified_at DESC
                    LIMIT ?
                """
                fb_params = base_params + fallback_date_params + extra_params + [cap]
                rows = conn.execute(fb_sql, fb_params).fetchall()

        for row in rows:
            fid = row["id"]
            if fid not in by_id:
                d = dict(row)
                d["candidate_sources"] = [bucket_name]
                by_id[fid] = d
            elif bucket_name not in by_id[fid]["candidate_sources"]:
                by_id[fid]["candidate_sources"].append(bucket_name)

        elapsed = (time.monotonic() - t0) * 1000
        bucket_timings[bucket_name] = bucket_timings.get(bucket_name, 0) + elapsed

    # ════════════════════════════════════════════════════════════════════════
    # STEP 1 — EXACT FAST PATH
    # Run exact-name and exact-stem for ALL combined_terms in a SINGLE
    # merged query (one OR clause per term).
    #
    # Key SQL design:
    #   lower(name) = ?   — exact equality; uses idx_files_name_lower
    #   lower(name) LIKE ? where param is already lowercased (e.g. 'term.%')
    #                     — prefix range scan; uses idx_files_name_lower
    # We pre-lowercase params in Python so the bind value does not wrap
    # lower() on the right-hand side, which would block index range scans.
    # ════════════════════════════════════════════════════════════════════════
    if combined_terms:
        exact_clauses: list[str] = []
        stem_clauses:  list[str] = []
        exact_params:  list      = []
        stem_params:   list      = []

        for term in combined_terms:
            t_lo = term.lower()
            exact_clauses.append("lower(name) = ?")
            exact_params.append(t_lo)
            # Pre-lowercased param allows expression index range scan.
            # Escape user term for LIKE safety (%, _, \), then append '.%'
            # which is application-controlled and must not be escaped.
            stem_clauses.append(f"lower(name) LIKE ? {_LIKE_ESC}")
            stem_params.append(f"{escape_like(t_lo)}.%")

        t0 = time.monotonic()
        exact_cond = " OR ".join(exact_clauses)
        stem_cond  = " OR ".join(stem_clauses)
        fast_cond  = f"({exact_cond} OR {stem_cond})"
        fast_sql   = f"""
            SELECT id, path, name, extension, size, created_at, modified_at, status, tags
            FROM files
            WHERE {base_where} {date_sql} AND {fast_cond}
            ORDER BY modified_at DESC
            LIMIT ?
        """
        fast_params = base_params + date_params + exact_params + stem_params + [100]

        with get_connection() as conn:
            fast_rows = conn.execute(fast_sql, fast_params).fetchall()
            if not fast_rows and fallback_date_sql:
                fb_fast_sql = f"""
                    SELECT id, path, name, extension, size, created_at, modified_at, status, tags
                    FROM files
                    WHERE {base_where} {fallback_date_sql} AND {fast_cond}
                    ORDER BY modified_at DESC
                    LIMIT ?
                """
                fb_fast_params = base_params + fallback_date_params + exact_params + stem_params + [100]
                fast_rows = conn.execute(fb_fast_sql, fb_fast_params).fetchall()

        elapsed_fast = (time.monotonic() - t0) * 1000
        bucket_timings["exact_fast_path"] = elapsed_fast

        # Tag each row with its strongest match bucket
        exact_terms_lower = {t.lower() for t in combined_terms}
        for row in fast_rows:
            n_lower = (row["name"] or "").lower()
            d = dict(row)
            is_exact   = n_lower in exact_terms_lower
            bucket_tag = "exact_name" if is_exact else "exact_stem"
            d["candidate_sources"] = [bucket_tag]
            by_id[row["id"]] = d

        # ── Decide which fallback buckets to skip ────────────────────────────
        # name_contains (%term%) and path_segment (%term%) are the most
        # expensive buckets (~60ms each, full-scan).  We skip them when we
        # already have sufficient direct-name matches AND the caller did not
        # supply constraints (folder/date) that would require the broader scan.
        #
        # We intentionally allow ext_filters and tag_terms to still run —
        # those use the expression index or a separate field and are important
        # for result recall (e.g. all .js files for a dashboard.js search).
        is_exact_filename_query = any("." in t for t in literal_terms)
        exact_name_hits = sum(
            1 for r in by_id.values()
            if "exact_name" in r["candidate_sources"]
        )
        exact_stem_hits = sum(
            1 for r in by_id.values()
            if "exact_stem" in r["candidate_sources"]
        )
        all_terms_have_direct_match = (
            exact_name_hits + exact_stem_hits >= len(combined_terms)
        )

        # Structural constraints that require the broader fallback scan
        has_structural_constraint = bool(
            folder_filters
            or folder_phrase_filters
            or drive_filters
            or date_filters.get("modified_after")
            or date_filters.get("modified_year")
            or date_filters.get("created_after")
            or date_filters.get("created_year")
        )

        skip_fallback_name_path = (
            not has_structural_constraint
            and (
                (is_exact_filename_query and exact_name_hits > 0)
                or all_terms_have_direct_match
            )
        )

        if skip_fallback_name_path:
            log.debug(
                "Exact fast-path: %d exact-name + %d exact-stem hits in %.1f ms — "
                "skipping name_contains / path_segment",
                exact_name_hits, exact_stem_hits, elapsed_fast,
            )
            # Run extension + folder + tag buckets only
            if combined_terms:
                folder_clauses: list[str] = []
                folder_params:  list      = []
                for term in combined_terms:
                    t_lo = term.lower()
                    e_lo = escape_like(t_lo)
                    folder_clauses.append(
                        f"(lower(path) LIKE ? {_LIKE_ESC} OR lower(path) LIKE ? {_LIKE_ESC})"
                    )
                    # Unix-style: %/term/% and Windows-style: %\term\%
                    folder_params.extend([f"%/{e_lo}/%", f"%\\{e_lo}\\%"])
                _run("exact_folder", " OR ".join(folder_clauses), folder_params, 50)

            _run_extension_and_tag_buckets(
                _run, combined_terms, ext_filters, tag_terms, weak_tag_terms, limit
            )
            log.info("Metadata Bucket Timings: %s", bucket_timings)
            return _finalize(
                by_id, meta_terms, literal_terms, ext_filters, tag_terms,
                weak_tag_terms, drive_filters, folder_filters, folder_phrase_filters,
            )


    # ════════════════════════════════════════════════════════════════════════
    # STEP 2 — EXACT FOLDER (only when combined_terms present)
    # Merged across all terms in a single query.
    # ════════════════════════════════════════════════════════════════════════
    if combined_terms:
        folder_clauses = []
        folder_params:  list = []
        for term in combined_terms:
            t_lo = term.lower()
            e_lo = escape_like(t_lo)
            folder_clauses.append(
                f"(lower(path) LIKE ? {_LIKE_ESC} OR lower(path) LIKE ? {_LIKE_ESC})"
            )
            # Unix-style: %/term/% and Windows-style: %\term\%
            folder_params.extend([f"%/{e_lo}/%", f"%\\{e_lo}\\%"])

        _run("exact_folder", " OR ".join(folder_clauses), folder_params, 50)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 3 — EXTENSION MATCH, TAG MATCH
    # ════════════════════════════════════════════════════════════════════════
    _run_extension_and_tag_buckets(
        _run, combined_terms, ext_filters, tag_terms, weak_tag_terms, limit
    )

    # ════════════════════════════════════════════════════════════════════════
    # STEP 4 — NAME CONTAINS (prefix + substring, merged across terms)
    # ════════════════════════════════════════════════════════════════════════
    if combined_terms:
        contains_clauses: list[str] = []
        contains_params:  list      = []
        for term in combined_terms:
            contains_clauses.append(f"lower(name) LIKE ? {_LIKE_ESC}")
            contains_params.append(f"%{escape_like(term.lower())}%")

        _run("name_contains", " OR ".join(contains_clauses), contains_params, limit * 2)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 5 — PATH SEGMENT (merged, lower priority)
    # ════════════════════════════════════════════════════════════════════════
    if combined_terms:
        path_clauses: list[str] = []
        path_params:  list      = []
        for term in combined_terms:
            path_clauses.append(f"lower(path) LIKE ? {_LIKE_ESC}")
            path_params.append(f"%{escape_like(term.lower())}%")

        _run("path_segment", " OR ".join(path_clauses), path_params, limit * 2)

    log.info("Metadata Bucket Timings: %s", bucket_timings)

    return _finalize(by_id, meta_terms, literal_terms, ext_filters, tag_terms,
                     weak_tag_terms, drive_filters, folder_filters, folder_phrase_filters)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_extension_and_tag_buckets(
    _run_fn,
    combined_terms: list,
    ext_filters: list,
    tag_terms: list,
    weak_tag_terms: list,
    limit: int,
) -> None:
    """Run extension and tag buckets, shared by fast-path and full-path."""
    # Extension: single merged query using OR across extensions
    if ext_filters:
        ext_clauses: list[str] = []
        ext_params:  list      = []
        for ext in ext_filters:
            ext_clean = (ext if ext.startswith(".") else f".{ext}").lower()
            ext_clauses.append("lower(extension) = ?")
            ext_params.append(ext_clean)
        _run_fn("extension_match", " OR ".join(ext_clauses), ext_params, limit * 2)

    # Tags: single merged query using OR across tag/weak-tag terms
    all_tag_terms = list(dict.fromkeys(tag_terms + weak_tag_terms))
    if all_tag_terms:
        tag_clauses: list[str] = []
        tag_params:  list      = []
        for term in all_tag_terms:
            tag_clauses.append(f"lower(tags) LIKE ? {_LIKE_ESC}")
            tag_params.append(f"%{escape_like(term.lower())}%")
        _run_fn("tag_match", " OR ".join(tag_clauses), tag_params, limit * 2)


def _finalize(
    by_id: dict,
    meta_terms: list,
    literal_terms: list,
    ext_filters: list,
    tag_terms: list,
    weak_tag_terms: list,
    drive_filters: list,
    folder_filters: list,
    folder_phrase_filters: list,
) -> dict:
    """Post-process merged rows: apply scope filter, attach match flags, return."""
    results = list(by_id.values())
    results = filter_allowed_files(results, path_key="path")

    for d in results:
        n = (d.get("name") or "").lower()
        p = (d.get("path") or "").lower()
        e = (d.get("extension") or "").lower()
        t = (d.get("tags") or "").lower()

        sources = d.get("candidate_sources", [])
        d["exact_name_match"]   = "exact_name" in sources
        d["exact_stem_match"]   = "exact_stem" in sources
        d["exact_folder_match"] = "exact_folder" in sources

        d["matched_metadata_terms"] = [m for m in meta_terms if m in n or m in p]
        d["matched_extensions"]     = [
            ext for ext in ext_filters
            if e == (ext if ext.startswith(".") else f".{ext}")
        ]
        d["matched_tag_terms"]      = [tag for tag in tag_terms if tag in t or tag in n]
        d["matched_weak_tag_terms"] = [tag for tag in weak_tag_terms if tag in t]
        d["matched_literal_terms"]  = [lit for lit in literal_terms if lit in n or lit in p]
        d["matched_content_terms"]  = []

        matched_drive  = [
            dr for dr in drive_filters
            if p.startswith(dr.lower()) or p.startswith(dr.lower().replace(":", ""))
        ]
        matched_folder = [f for f in folder_filters if f.lower() in p]
        d["matched_drive_filters"]  = matched_drive
        d["matched_folder_filters"] = matched_folder
        d["matched_location"]       = bool(matched_drive or matched_folder)
        d["folder_phrase_match"]    = any(fp.lower() in p for fp in folder_phrase_filters)

        d["size_human"] = _human_size(d.get("size") or 0)
        d["item_type"]  = "file"
        d["dedupe_key"] = f"file:{p}"
        d["score"]      = 0.0

    log.debug("Metadata search merged fetch: %d unique allowed results", len(results))
    return {"total": len(results), "results": results}


# ── SQL clause builders ────────────────────────────────────────────────────────

def _build_location_sql(
    drive_filters: list,
    folder_filters: list,
    folder_phrase_filters: list,
) -> tuple[str, list]:
    sql    = ""
    params: list = []

    if drive_filters:
        clauses = []
        for d in drive_filters:
            clauses.append("path LIKE ?")
            params.append(f"{d}%")
        sql += " AND (" + " OR ".join(clauses) + ")"

    if folder_filters or folder_phrase_filters:
        clauses = []
        for f in folder_filters:
            clauses.append("path LIKE ?")
            params.append(f"%{f}%")
        for fp in folder_phrase_filters:
            clauses.append("path LIKE ?")
            params.append(f"%{fp}%")
        sql += " AND " + " AND ".join(clauses)

    return sql, params


def _build_date_sql(date_filters: dict):
    if not date_filters:
        return "", [], "", [], None, None

    field = date_filters.get("field", "modified_at")
    if field not in ("modified_at", "created_at", "last_indexed_at"):
        field = "modified_at"

    def _clauses(fld: str, pf: str) -> tuple[str, list]:
        s = ""
        p: list = []
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

    date_sql = fallback_date_sql = ""
    date_params: list = []
    fallback_date_params: list = []
    matched_field = field
    matched_fallback_field = None

    if field == "created_at":
        date_sql, date_params = _clauses("created_at", "created_")
        if date_filters.get("fallback_to_modified"):
            fallback_date_sql, fallback_date_params = _clauses("modified_at", "modified_")
            matched_fallback_field = "modified_at"
    elif field == "last_indexed_at":
        date_sql, date_params = _clauses("last_indexed_at", "indexed_")
    else:
        date_sql, date_params = _clauses("modified_at", "modified_")

    return (date_sql, date_params,
            fallback_date_sql, fallback_date_params,
            matched_field, matched_fallback_field)


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
