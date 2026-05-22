"""
DeepFind Engine — Hybrid Search

Combines metadata and FTS5 content search.
Step 11.5: Match Coverage Scoring
Calculates a final score based on match coverage across parsed query parts.
"""

import logging
from datetime import datetime, timezone

from search.query_parser import parse_query
from search.filename_search import search_files as metadata_search
from search.fulltext_search import (
    search_content,
    check_has_extracted_content,
    _human_size,
)
from search.semantic_search import search_semantic

log = logging.getLogger(__name__)

_RECENCY_DAYS = 30      # Files modified within N days get a recency boost


def unified_search(
    query: str,
    mode: str = "all",      # "all" | "metadata" | "content" | "semantic"
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
    if mode not in ("all", "metadata", "content", "semantic"):
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
        
    # ── Pure semantic ────────────────────────────────────────────────────────
    if mode == "semantic":
        t1 = time.monotonic()
        data = search_semantic(parsed.get("normalized", query), limit=limit, offset=offset, date_filters=parsed.get("date_filters", {}))
        timing["semantic_search"] = int((time.monotonic() - t1) * 1000)
        timing["total"] = int((time.monotonic() - t0) * 1000)
        
        no_index = data.get("no_index", False)
        
        ret = {
            "total": data["total"],
            "results": data["results"],
            "mode": mode,
            "has_extracted_content": has_content,
            "no_content_warning": False,
            "no_index": no_index,
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
    semantic_data = {"results": [], "total": 0}
    if parsed.get("semantic_allowed", True) or mode == "semantic":
        semantic_data = search_semantic(parsed.get("normalized", query), limit=50, offset=0, date_filters=parsed.get("date_filters", {}))
    timing["semantic_search"] = int((time.monotonic() - t3) * 1000)

    t4 = time.monotonic()
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
            
    # Merge semantic results
    for sr in semantic_data["results"]:
        fid = sr["id"]
        if fid in by_id:
            mr = by_id[fid]
            mr["match_type"] = "hybrid"
            # Update snippet only if no snippet exists
            if not mr.get("snippet") and sr.get("snippet"):
                mr["snippet"] = sr.get("snippet")
            mr.setdefault("matched_reasons", []).append("Semantic meaning matched your query")
            mr["semantic_score"] = sr.get("semantic_score", 0)
        else:
            sr["match_type"] = "semantic"
            by_id[fid] = sr

    # Calculate final scores
    for r in by_id.values():
        _calculate_score(r, parsed)
        
    # Filter out results with score 0 (which includes hard-filtered out items)
    valid_results = [r for r in by_id.values() if r.get("score", 0) > 0]

    # Sort merged results
    merged = sorted(valid_results, key=lambda r: r["score"], reverse=True)

    # Apply offset + limit
    total    = len(merged)
    paginated = merged[offset : offset + limit]
    
    timing["merge_rank"] = int((time.monotonic() - t4) * 1000)
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
    Applies hard filters first.
    """
    meta_terms = parsed.get("metadata_terms", [])
    ext_filters = parsed.get("extension_filters", [])
    tag_terms = parsed.get("tag_terms", [])
    content_terms = parsed.get("content_terms", [])
    drive_filters = parsed.get("drive_filters", [])
    folder_filters = parsed.get("folder_filters", [])
    date_filters = parsed.get("date_filters", {})
    literal_terms = parsed.get("literal_terms", [])
    search_intent = parsed.get("search_intent", "hybrid")
    important_terms = parsed.get("important_terms", [])
    
    total_signals_set = set(meta_terms + ext_filters + tag_terms + content_terms + drive_filters + folder_filters + literal_terms)
    total_signals = len(total_signals_set)
    
    matched_meta = r.get("matched_metadata_terms", [])
    matched_exts = r.get("matched_extensions", [])
    matched_tags = r.get("matched_tag_terms", [])
    matched_weak_tags = r.get("matched_weak_tag_terms", [])
    matched_content = r.get("matched_content_terms", [])
    matched_drive = r.get("matched_drive_filters", [])
    matched_folder = r.get("matched_folder_filters", [])
    matched_literal = r.get("matched_literal_terms", [])
    
    matched_signals_set = set(matched_meta + matched_exts + matched_tags + matched_content + matched_drive + matched_folder + matched_literal)
    matched_signals = len(matched_signals_set)
    
    # ── Hard Filters ────────────────────────────────────────────────────────
    
    if search_intent == "structured":
        if ext_filters and not matched_exts and not r.get("exact_name_match"):
            r["score"] = 0
            return
            
        if folder_filters and not matched_folder and not r.get("folder_phrase_match"):
            r["score"] = 0
            return
            
        if drive_filters and not matched_drive:
            r["score"] = 0
            return
            
        has_active_date = date_filters and any(date_filters.get(k) for k in ["modified_after", "modified_year", "created_after", "created_year", "indexed_after", "indexed_year", "modified_before", "created_before", "indexed_before"])
        if has_active_date and not r.get("matched_date_filter"):
            r["score"] = 0
            return
            
        # Semantic only in structured search is not allowed unless it matched other things
        if r.get("match_type") == "semantic" and matched_signals == 0:
            r["score"] = 0
            return
            
    # ── Coverage Calculation ────────────────────────────────────────────────
    n_lower = (r.get("name") or "").lower()
    p_lower = (r.get("path") or "").lower()
    t_lower = (r.get("tags") or "").lower()
    c_lower = (r.get("snippet") or "").lower()
    
    matched_important_list = []
    for term in important_terms:
        if (term in matched_meta or term in matched_content or term in matched_tags or term in matched_literal or
            term in n_lower or term in p_lower or term in t_lower or term in c_lower):
            matched_important_list.append(term)
            
    matched_important_terms_set = list(set(matched_important_list))
    total_important = len(important_terms)
    matched_important = len(matched_important_terms_set)
    
    if total_important > 0:
        coverage_score = matched_important / total_important
    else:
        coverage_score = 1.0

    # Minimum relevance threshold for important terms
    if total_important >= 2 and matched_important == 0:
        r["score"] = 0
        return
        
    # Minimum relevance for semantic in generic search (prevent unrelated semantic matches)
    if r.get("match_type") == "semantic" and total_important >= 1 and matched_important == 0:
        r["score"] = 0
        return
            
    # ── Base Scoring ────────────────────────────────────────────────────────
    
    base_score = 0

    if r.get("exact_name_match"):
        base_score += 180
    elif r.get("exact_stem_match"):
        base_score += 160
    elif r.get("exact_folder_match") or r.get("folder_phrase_match"):
        base_score += 150
        
    if matched_exts:
        base_score += 140
        
    if r.get("matched_date_filter"):
        base_score += 130
        
    if matched_meta or matched_literal:
        for m in (matched_meta + matched_literal):
            if f"\\{m}\\" in p_lower or f"/{m}/" in p_lower or f"/{m}\\" in p_lower or f"\\{m}/" in p_lower:
                base_score += 100 # path token match
            elif n_lower.startswith(m):
                base_score += 60 # starts with
            elif m in n_lower:
                base_score += 40 # substring
            elif m in p_lower:
                base_score += 5 # weak path substring
                
        base_score += (120 * len(matched_literal)) # literal token matches

    if matched_tags:
        base_score += (80 * len(matched_tags))
        
    if matched_content:
        base_score += (80 * len(matched_content))
        
    if matched_weak_tags:
        base_score += (5 * len(matched_weak_tags))
        
    if r.get("match_type") == "semantic":
        sem_score = r.get("semantic_score", 0)
        if sem_score > 0.45:
            base_score += (sem_score * 70)
        else:
            base_score += (sem_score * 5) # weak semantic
            
    # Apply coverage multiplier
    final_score = base_score * (0.6 + coverage_score)
    
    # Generic tag gating
    if not matched_meta and not matched_exts and not matched_content and matched_weak_tags:
        if search_intent == "structured":
            final_score = 0
        else:
            final_score -= 100
            
    r["score"] = round(max(0, final_score), 2)
    r["coverage_score"] = round(coverage_score, 2)
    r["matched_important_terms"] = matched_important_terms_set
    r["total_important_terms"] = total_important
    r["matched_signal_count"] = matched_signals
    r["total_signal_count"] = total_signals
    
    reasons = []
    
    if matched_drive:
        reasons.append(f"Location matched: {', '.join(matched_drive)}")
    if matched_folder or r.get("folder_phrase_match"):
        reasons.append(f"Folder matched")
        
    if r.get("exact_name_match"):
        reasons.append("Filename exact match")
    elif matched_meta:
        reasons.append(f"Name/Path matched: {', '.join(matched_meta)}")
    elif matched_literal:
        reasons.append(f"Filename contains: {', '.join(matched_literal)}")
        
    if matched_exts:
        # Use registry label if available
        from search.file_type_registry import label_for_extension
        labels = [label_for_extension(e) for e in matched_exts]
        reasons.append(f"File type matched: {', '.join(labels)}")
        
    if matched_tags:
        reasons.append(f"Tag matched: {', '.join(matched_tags)}")
        
    if matched_content:
        reasons.append(f"Content matched: {', '.join(matched_content)}")
        
    if r.get("matched_date_filter"):
        human_time = parsed.get("date_filters", {}).get("label") or "requested timeframe"
        field_used = r.get("matched_date_filter_field")
        fallback_used = r.get("fallback_to_modified_used")
        
        if field_used == "created_at":
            reasons.append(f"Created timeframe matched: {human_time}")
        elif field_used == "last_indexed_at":
            reasons.append(f"Indexed timeframe matched: {human_time}")
        else:
            reasons.append(f"Modified timeframe matched: {human_time}")
            
        if fallback_used:
            reasons.append("Created date unavailable; used modified date fallback")
        
    if r.get("match_type") == "semantic" and r["score"] > 0 and len(reasons) == 0:
        reasons.append("Semantic meaning matched your query")
    
    r["matched_reasons"] = reasons
    
    if r.get("match_type") == "metadata":
        if matched_meta and matched_exts:
            r["match_type"] = "metadata_type"
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
