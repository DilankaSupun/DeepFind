"""
DeepFind Engine — Hybrid Search

Combines metadata and FTS5 content search.
Step 11.5: Match Coverage Scoring
Calculates a final score based on match coverage across parsed query parts.
"""

import logging
from datetime import datetime, timezone

from search.filename_search import search_files as metadata_search
from search.fulltext_search import (
    search_content,
    check_has_extracted_content,
    _human_size,
)
from search.query_parser import parse_query

log = logging.getLogger(__name__)

_RECENCY_DAYS = 30      # Files modified within N days get a recency boost


def unified_search(
    query: str,
    mode: str = "all",      # "all" | "metadata" | "content"
    limit: int = 50,
    offset: int = 0,
    debug: bool = False,
) -> dict:
    import time
    timing = {}
    
    t0 = time.monotonic()
    q = query.strip()
    if not q:
        return _empty(mode)

    parsed = parse_query(q)
    timing["query_parse"] = int((time.monotonic() - t0) * 1000)

    mode = mode.lower()
    if mode not in ("all", "metadata", "content"):
        mode = "all"

    has_content = check_has_extracted_content()

    # ── Pure metadata ────────────────────────────────────────────────────────
    if mode == "metadata":
        t1 = time.monotonic()
        data = metadata_search(parsed, limit=limit, offset=offset)
        timing["metadata_search"] = int((time.monotonic() - t1) * 1000)
        
        t2 = time.monotonic()
        for r in data["results"]:
            r["match_type"] = "metadata"
            r.setdefault("snippet", "")
            _calculate_score(r, parsed)
            
        # Re-sort after scoring
        sorted_results = sorted(data["results"], key=lambda r: r["score"], reverse=True)
        timing["merge_rank"] = int((time.monotonic() - t2) * 1000)
        timing["content_search"] = 0
        timing["total"] = int((time.monotonic() - t0) * 1000)
        
        ret = {
            "total": data["total"],
            "results": sorted_results,
            "mode": mode,
            "has_extracted_content": has_content,
            "no_content_warning": False,
            "timing_ms": timing
        }
        if debug: ret["parsed_query"] = parsed
        return ret

    # ── Pure content ─────────────────────────────────────────────────────────
    if mode == "content":
        t1 = time.monotonic()
        data = search_content(parsed, limit=limit, offset=offset)
        timing["content_search"] = int((time.monotonic() - t1) * 1000)
        
        t2 = time.monotonic()
        no_content = data.get("no_content", False)
        for r in data["results"]:
            _calculate_score(r, parsed)
            
        sorted_results = sorted(data["results"], key=lambda r: r["score"], reverse=True)
        timing["merge_rank"] = int((time.monotonic() - t2) * 1000)
        timing["metadata_search"] = 0
        timing["total"] = int((time.monotonic() - t0) * 1000)
        
        ret = {
            "total": data["total"],
            "results": sorted_results,
            "mode": mode,
            "has_extracted_content": not no_content,
            "no_content_warning": no_content,
            "timing_ms": timing
        }
        if debug: ret["parsed_query"] = parsed
        return ret

    # ── Hybrid (all) ─────────────────────────────────────────────────────────
    # Fetch both result sets (over-fetch to allow dedup + re-rank)
    FETCH = min(limit * 4, 200)

    t1 = time.monotonic()
    meta_data    = metadata_search(parsed, limit=FETCH, offset=0)
    timing["metadata_search"] = int((time.monotonic() - t1) * 1000)
    
    t2 = time.monotonic()
    content_data = search_content(parsed, limit=FETCH, offset=0)
    timing["content_search"] = int((time.monotonic() - t2) * 1000)

    t3 = time.monotonic()
    # Index metadata results by file id
    by_id: dict[int, dict] = {}
    for r in meta_data["results"]:
        r["match_type"] = "metadata"
        r.setdefault("snippet", "")
        by_id[r["id"]] = r

    # Merge content results
    for cr in content_data["results"]:
        fid = cr["id"]
        if fid in by_id:
            # Exists in metadata — upgrade to hybrid
            mr = by_id[fid]
            mr["match_type"] = "hybrid"
            mr["snippet"] = cr.get("snippet", "")
            
            mr["matched_metadata_terms"] = list(set(mr.get("matched_metadata_terms", []) + cr.get("matched_metadata_terms", [])))
            mr["matched_extensions"] = list(set(mr.get("matched_extensions", []) + cr.get("matched_extensions", [])))
            mr["matched_tag_terms"] = list(set(mr.get("matched_tag_terms", []) + cr.get("matched_tag_terms", [])))
            mr["matched_weak_tag_terms"] = list(set(mr.get("matched_weak_tag_terms", []) + cr.get("matched_weak_tag_terms", [])))
            mr["matched_content_terms"] = list(set(mr.get("matched_content_terms", []) + cr.get("matched_content_terms", [])))
            
            if cr.get("exact_name_match"):
                mr["exact_name_match"] = True
        else:
            cr["match_type"] = "content"
            by_id[fid] = cr

    # Calculate final scores
    for r in by_id.values():
        _calculate_score(r, parsed)

    # Sort merged results
    merged = sorted(by_id.values(), key=lambda r: r["score"], reverse=True)

    # Apply offset + limit
    total    = len(merged)
    paginated = merged[offset : offset + limit]
    
    timing["merge_rank"] = int((time.monotonic() - t3) * 1000)
    timing["total"] = int((time.monotonic() - t0) * 1000)

    ret = {
        "total":   total,
        "results": paginated,
        "mode":    mode,
        "has_extracted_content": has_content,
        "no_content_warning": False,
        "timing_ms": timing
    }
    if debug: ret["parsed_query"] = parsed
    return ret


# ── Helpers ────────────────────────────────────────────────────────────────────

def _calculate_score(r: dict, parsed: dict) -> None:
    """
    Calculates final score using match coverage and weighted signals.
    """
    meta_terms = parsed.get("metadata_terms", [])
    ext_filters = parsed.get("extension_filters", [])
    tag_terms = parsed.get("tag_terms", [])
    content_terms = parsed.get("content_terms", [])
    drive_filters = parsed.get("drive_filters", [])
    folder_filters = parsed.get("folder_filters", [])
    
    total_signals_set = set(meta_terms + ext_filters + tag_terms + content_terms + drive_filters + folder_filters)
    total_signals = len(total_signals_set)
    
    matched_meta = r.get("matched_metadata_terms", [])
    matched_exts = r.get("matched_extensions", [])
    matched_tags = r.get("matched_tag_terms", [])
    matched_weak_tags = r.get("matched_weak_tag_terms", [])
    matched_content = r.get("matched_content_terms", [])
    matched_drive = r.get("matched_drive_filters", [])
    matched_folder = r.get("matched_folder_filters", [])
    
    matched_signals_set = set(matched_meta + matched_exts + matched_tags + matched_content + matched_drive + matched_folder)
    matched_signals = len(matched_signals_set)
    
    coverage_score = (matched_signals / total_signals) if total_signals > 0 else 1.0
    
    base_score = 0
    match_types = 0
    
    n = (r.get("name") or "").lower()
    p = (r.get("path") or "").lower()

    if r.get("exact_name_match"):
        base_score += 100
        match_types += 1
    elif matched_meta:
        name_match = any(m in n for m in matched_meta)
        path_match = any(m in p for m in matched_meta)
        if name_match: 
            base_score += 70
            match_types += 1
        elif path_match: 
            base_score += 70
            match_types += 1
            
    if matched_drive:
        base_score += 100
        match_types += 1
        
    if matched_folder:
        base_score += (90 * len(matched_folder))
        match_types += 1
            
    if matched_exts:
        base_score += 80
        match_types += 1
        
    if matched_tags:
        base_score += 60
        match_types += 1
        
    if matched_content:
        base_score += (60 * len(matched_content))
        match_types += 1
        
    if match_types > 1:
        base_score += 50
        
    # Recency max +10
    base_score += (_recency_score(r.get("modified_at")) * 10)
    
    # Penalize if extension filters are required but missed
    if ext_filters and not matched_exts:
        if meta_terms or content_terms or tag_terms:
            base_score -= 150 # Strong penalty
            
    # Apply coverage multiplier
    final_score = base_score * (0.5 + coverage_score)
    
    # Penalize weak single-term matches (unless they matched an exact name or extension)
    if total_signals >= 2 and matched_signals == 1 and not matched_exts and not r.get("exact_name_match"):
        final_score -= 40
        
    # If the file matches ONLY a weak tag (like "document"), apply huge penalty
    if not matched_meta and not matched_exts and not matched_tags and not matched_content and matched_weak_tags:
        final_score -= 100
        
    r["score"] = round(max(0, final_score), 2)
    r["coverage_score"] = round(coverage_score, 2)
    r["matched_signal_count"] = matched_signals
    r["total_signal_count"] = total_signals
    
    reasons = []
    
    if matched_drive:
        reasons.append(f"Location matched: {', '.join(matched_drive)}")
    if matched_folder:
        reasons.append(f"Folder matched: {', '.join(matched_folder)}")
        
    if r.get("exact_name_match"):
        reasons.append("Filename exact match")
    elif matched_meta:
        reasons.append(f"Name/Path matched: {', '.join(matched_meta)}")
        
    if matched_exts:
        reasons.append(f"File type matched: {', '.join([e.replace('.','') for e in matched_exts])}")
        
    if matched_tags:
        reasons.append(f"Tag matched: {', '.join(matched_tags)}")
        
    if matched_content:
        reasons.append(f"Content matched: {', '.join(matched_content)}")
        
    if total_signals > 0:
        reasons.append(f"Matched {matched_signals}/{total_signals} important query parts")
    
    r["matched_reasons"] = reasons
    
    # Update match type logic so it doesn't say "Name match" if it only matched weak tags
    if r.get("match_type") == "metadata":
        if matched_meta and matched_exts:
            r["match_type"] = "metadata_type" # Custom type for React
        elif not matched_meta and not matched_exts and (matched_tags or matched_weak_tags):
            r["match_type"] = "tag"


def _recency_score(modified_at: str | None) -> float:
    """0.0–1.0 based on how recently the file was modified."""
    if not modified_at:
        return 0.0
    try:
        dt = datetime.fromisoformat(modified_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
        return max(0.0, 1.0 - (age_days / _RECENCY_DAYS))
    except Exception:
        return 0.0


def _empty(mode: str) -> dict:
    return {
        "total": 0,
        "results": [],
        "mode": mode,
        "has_extracted_content": False,
        "no_content_warning": False,
    }
