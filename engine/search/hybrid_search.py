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
        from scanner.scan_scope_utils import filter_allowed_files
        data["results"] = filter_allowed_files(data["results"])
        
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
        
        from scanner.scan_scope_utils import filter_allowed_files
        data["results"] = filter_allowed_files(data["results"])
        
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
        
        from scanner.scan_scope_utils import filter_allowed_files
        data["results"] = filter_allowed_files(data["results"])
        
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
        r["match_sources"] = ["metadata"]
        r.setdefault("snippet", "")
        by_id[r["id"]] = r

    # Merge content results
    for cr in content_data["results"]:
        fid = cr["id"]
        if fid in by_id:
            mr = by_id[fid]
            if "content" not in mr.get("match_sources", []):
                mr.setdefault("match_sources", []).append("content")
            
            # Update snippet only if it exists
            if not mr.get("snippet") and cr.get("snippet"):
                mr["snippet"] = cr.get("snippet")
            
            mr["matched_metadata_terms"] = list(set(mr.get("matched_metadata_terms", []) + cr.get("matched_metadata_terms", [])))
            mr["matched_extensions"] = list(set(mr.get("matched_extensions", []) + cr.get("matched_extensions", [])))
            mr["matched_tag_terms"] = list(set(mr.get("matched_tag_terms", []) + cr.get("matched_tag_terms", [])))
            mr["matched_weak_tag_terms"] = list(set(mr.get("matched_weak_tag_terms", []) + cr.get("matched_weak_tag_terms", [])))
            mr["matched_content_terms"] = list(set(mr.get("matched_content_terms", []) + cr.get("matched_content_terms", [])))
            
            if cr.get("exact_name_match"):
                mr["exact_name_match"] = True
        else:
            cr["match_sources"] = ["content"]
            by_id[fid] = cr
            
    # Merge semantic results
    for sr in semantic_data["results"]:
        fid = sr["id"]
        if fid in by_id:
            mr = by_id[fid]
            if "semantic" not in mr.get("match_sources", []):
                mr.setdefault("match_sources", []).append("semantic")
            
            # Update snippet only if no snippet exists
            if not mr.get("snippet") and sr.get("snippet"):
                mr["snippet"] = sr.get("snippet")
            mr.setdefault("matched_reasons", []).append("Semantic meaning matched your query")
            mr["semantic_score"] = sr.get("semantic_score", 0)
        else:
            sr["match_sources"] = ["semantic"]
            by_id[fid] = sr

    # Calculate final scores
    for r in by_id.values():
        _calculate_score(r, parsed)
        
    # Filter out results with score 0 (which includes hard-filtered out items)
    valid_results = [r for r in by_id.values() if r.get("score", 0) > 0]
    
    from scanner.scan_scope_utils import filter_allowed_files
    valid_results = filter_allowed_files(valid_results)

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
    Calculates final score using match coverage and weighted signals based on exact points.
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

    if total_important >= 2 and matched_important == 0:
        r["score"] = 0
        return
        
    if r.get("match_type") == "semantic" and total_important >= 1 and matched_important == 0:
        r["score"] = 0
        return
            
    # ── Separate Scores ───────────────────────────────────────────────────────
    
    filename_score = 0
    folder_score = 0
    path_score = 0
    extension_score = 0
    file_category_score = 0
    content_score = 0
    tag_score = 0
    semantic_score = 0
    internal_file_penalty = 0

    reasons = []
    
    n_tokens = set([t for t in n_lower.replace(".", " ").replace("_", " ").replace("-", " ").split() if t])
    p_tokens = set([t for t in p_lower.replace("\\", "/").split("/") if t])
    
    ext = (r.get("extension") or "").lower()
    if not ext and n_lower and "." in n_lower:
        ext = "." + n_lower.rsplit(".", 1)[-1]
        
    internal_exts = {".dll", ".dat", ".bin", ".pak", ".rpf", ".qvm", ".cfg", ".ini", ".tmp", ".log"}
    is_internal = ext in internal_exts
    
    # Check Candidate Sources from our bucketed queries
    candidate_sources = r.get("candidate_sources", [])
    
    # Exact Matches
    if "exact_name" in candidate_sources or r.get("exact_name_match"):
        filename_score = max(filename_score, 900)
        reasons.append(f"Exact filename matched: {r.get('name')}")
    elif "exact_stem" in candidate_sources or r.get("exact_stem_match"):
        filename_score = max(filename_score, 850)
        reasons.append(f"Exact filename stem matched: {r.get('name')}")
        
    if "exact_folder" in candidate_sources or r.get("exact_folder_match") or r.get("folder_phrase_match"):
        folder_score = max(folder_score, 800)
        reasons.append("Exact folder matched")
    elif matched_folder:
        folder_score = max(folder_score, 250)
        reasons.append("File inside matching folder")
        
    # Prefix and Contains
    if "name_contains" in candidate_sources:
        # Check if it's a prefix
        is_prefix = False
        for m in (matched_meta + matched_literal):
            if n_lower.startswith(m.lower()):
                is_prefix = True
                break
        if is_prefix:
            filename_score = max(filename_score, 700)
            reasons.append("Filename prefix matched")
        else:
            filename_score = max(filename_score, 600)
            reasons.append("Filename contains matched")
    else:
        # Fallback to manual token check just in case
        for m in (matched_meta + matched_literal):
            m_norm = m.lower()
            if m_norm in n_tokens:
                filename_score = max(filename_score, 600)
                if f"Filename token matched: {m}" not in reasons and not filename_score >= 850:
                    reasons.append(f"Filename token matched: {m}")
            elif n_lower.startswith(m_norm):
                filename_score = max(filename_score, 700)
                if f"Filename starts with: {m}" not in reasons and not filename_score >= 850:
                    reasons.append(f"Filename starts with: {m}")
            elif m_norm in n_lower:
                filename_score = max(filename_score, 600)
                if f"Filename matched: {m}" not in reasons and not filename_score >= 850:
                    reasons.append(f"Filename matched: {m}")
    
    # Path matches
    if "path_segment" in candidate_sources:
        path_score = max(path_score, 180)
        reasons.append("Path segment matched")
    else:
        for m in (matched_meta + matched_literal):
            m_norm = m.lower()
            if m_norm in p_tokens:
                path_score = max(path_score, 180)
                if f"Path segment matched: {m}" not in reasons:
                    reasons.append(f"Path segment matched: {m}")
            elif m_norm in p_lower:
                path_score = max(path_score, 90)
                if f"Path matched: {m}" not in reasons:
                    reasons.append(f"Path matched: {m}")
            else:
                path_score = max(path_score, 5) # weak path substring
                
    # File Category / Alias
    if matched_exts or "extension_match" in candidate_sources:
        extension_score += 350
        user_asked_for_ext = False
        for m in (matched_meta + matched_literal):
            if ext and ext.lstrip(".") == m.lower():
                user_asked_for_ext = True
                break
        if user_asked_for_ext:
            is_internal = False
            
        from search.file_type_registry import label_for_extension
        labels = [label_for_extension(e) for e in matched_exts]
        reasons.append(f"File type matched: {', '.join(labels)}")
    else:
        top_tier_exts = {
            ".exe", ".lnk", ".bat", ".cmd", ".msi", ".appx", ".url",
            ".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".txt", ".md",
            ".mp4", ".mkv", ".avi", ".mov", ".webm",
            ".mp3", ".wav", ".m4a", ".flac",
            ".jpg", ".png", ".webp", ".gif", ".svg",
            ".zip", ".rar", ".7z"
        }
        if ext in top_tier_exts:
            file_category_score += 350
            if filename_score >= 600:
                if ext in {".exe", ".lnk", ".bat", ".cmd", ".msi", ".appx", ".url"}:
                    if "Application file matched" not in reasons:
                        reasons.append("Application file matched")
                elif ext in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
                    if "Media file matched" not in reasons:
                        reasons.append("Media file matched")
                elif ext in {".pdf", ".docx", ".txt", ".md"}:
                    if "Document file matched" not in reasons:
                        reasons.append("Document file matched")
                        
    # Penalties
    support_folders = {"_redist", "redist", "redistributable", "redistributables", "directx", "vc_redist", "vcredist", "dependencies", "dependency", "setup_files", "installer", "commonredist", "__pycache__", "node_modules", ".git", ".venv", "cache", "temp"}
    support_folder_found = None
    for f in p_tokens:
        if f.lower() in support_folders:
            support_folder_found = f
            break
            
    asked_internal = False
    if is_internal:
        if ext:
            ext_clean = ext.lstrip(".")
            for m in (matched_meta + matched_literal):
                if ext_clean == m.lower() or ext == m.lower():
                    asked_internal = True
                    break
        if not asked_internal:
            internal_file_penalty = -150
            
    internal_names = {"vcredist_x86.exe", "vcredist_x64.exe", "dxwebsetup.exe", "uninstall.exe", "unins000.exe"}
    if n_lower in internal_names or (n_lower == "setup.exe" and support_folder_found):
        asked_name = False
        for m in (matched_meta + matched_literal):
            if m.lower() in n_lower:
                asked_name = True
                break
        if not asked_name:
            internal_file_penalty = -150
            
    support_folder_penalty = 0
    if support_folder_found:
        asked_support = False
        for m in (matched_meta + matched_literal):
            if m.lower() in support_folder_found.lower():
                asked_support = True
                break
        if not asked_support:
            support_folder_penalty = -150
            reasons.append(f"Internal file penalty applied (inside {support_folder_found})")
            
    # Boosts
    main_executable_boost = 0
    if ext in {".exe", ".lnk", ".bat", ".cmd", ".url", ".msi"}:
        if filename_score >= 600 or folder_score >= 800:
            main_executable_boost = 250
            
    doc_media_boost = 0
    if ext in {".pdf", ".docx", ".mp4", ".mp3", ".jpg", ".zip", ".png", ".txt"}:
        if filename_score >= 600:
            doc_media_boost = 150
            
    # Path-only penalty
    path_only_match_penalty = 0
    if path_score > 0 and filename_score == 0 and folder_score == 0:
        path_only_match_penalty = -100
        reasons.append("Path-only match penalty applied")
            
    # Tags
    if "tag_match" in candidate_sources or matched_tags:
        tag_score += 250
        reasons.append(f"Tag matched")
    if matched_weak_tags:
        tag_score += 50
        
    # Content
    if "content" in r.get("match_sources", []) or matched_content:
        content_score += 120
        reasons.append(f"Content matched extracted text")
        
    # Semantic
    if r.get("match_type") == "semantic" or r.get("semantic_score", 0) > 0:
        sem_score = r.get("semantic_score", 0)
        if search_intent == "semantic":
            semantic_score += (sem_score * 80)
        else:
            semantic_score += (sem_score * 40)
        
        if semantic_score > 20 and r["score"] > 0 and len(reasons) == 0:
            reasons.append("Semantic meaning matched your query")
            
    # Date filters
    if r.get("matched_date_filter"):
        extension_score += 130
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

    if matched_drive:
        if f"Location matched: {', '.join(matched_drive)}" not in reasons:
            reasons.append(f"Location matched: {', '.join(matched_drive)}")

    # Calculate final score
    base_score = (filename_score + folder_score + path_score + extension_score + 
                  file_category_score + content_score + tag_score + semantic_score + 
                  main_executable_boost + doc_media_boost + internal_file_penalty + 
                  support_folder_penalty + path_only_match_penalty)

    # Apply coverage multiplier
    final_score = base_score * (0.6 + coverage_score)
    
    # Generic tag gating
    if not matched_meta and not matched_exts and not matched_content and matched_weak_tags:
        if search_intent == "structured":
            final_score = 0
        else:
            final_score -= 100
            
    # Remove duplicates from reasons while preserving order
    deduped_reasons = []
    seen = set()
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            deduped_reasons.append(reason)

    # Store scores for debug mode
    r["score_breakdown"] = {
        "filename_score": filename_score,
        "folder_score": folder_score,
        "path_score": path_score,
        "extension_score": extension_score,
        "file_category_score": file_category_score,
        "content_score": content_score,
        "tag_score": tag_score,
        "semantic_score": semantic_score,
        "main_executable_boost": main_executable_boost,
        "doc_media_boost": doc_media_boost
    }
    
    r["penalties_applied"] = {
        "support_folder_penalty": support_folder_penalty,
        "internal_file_penalty": internal_file_penalty,
        "path_only_match_penalty": path_only_match_penalty
    }
    
    r["base_score"] = base_score
            
    r["score"] = round(max(0, final_score), 2)
    r["coverage_score"] = round(coverage_score, 2)
    r["matched_important_terms"] = matched_important_terms_set
    r["total_important_terms"] = total_important
    r["matched_signal_count"] = matched_signals
    r["total_signal_count"] = total_signals
    r["matched_reasons"] = deduped_reasons
    
    # Evidence-based match type selection
    primary = None
    sources = r.get("match_sources", [])
    
    is_meta = "metadata" in sources
    is_content = "content" in sources
    is_semantic = "semantic" in sources
    
    # Priority hierarchy: exact_name > name > app > folder > tag > path > content > semantic
    if is_meta:
        if "exact_name" in candidate_sources or filename_score >= 850:
            primary = "exact_name"
        elif filename_score >= 600:
            primary = "name"
        elif file_category_score > 0 or extension_score > 0:
            primary = "app"
        elif "exact_folder" in candidate_sources or folder_score >= 600:
            primary = "folder"
        elif tag_score > 0:
            primary = "tag"
        elif path_score > 0:
            primary = "path"
            
    # If no metadata hit was strong enough, fallback to content/semantic
    if not primary:
        if is_content:
            primary = "content"
        elif is_semantic:
            primary = "semantic"
        elif is_meta:
            primary = "name" # absolute fallback for metadata
            
    # Assign for frontend compatibility
    r["primary_match_type"] = primary
    r["match_type"] = primary
    
    # Debug fields
    r["has_extracted_text"] = bool(r.get("snippet"))
    r["fts_content_match"] = is_content
    r["snippet_source"] = "extracted_text" if is_content else None


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
