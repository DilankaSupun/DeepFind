"""
DeepFind Engine — /search Routes

Step 8:  Metadata search by filename, path, and extension.
Step 10: Added type parameter (metadata | content | all) + FTS5 content search.
         Added POST /search/rebuild-fts for dev use.

Endpoints:
  GET  /search?q=<query>&type=all&limit=50&offset=0
  POST /search/rebuild-fts
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from search.hybrid_search import unified_search
from search.fulltext_search import rebuild_fts_index

log = logging.getLogger(__name__)
router = APIRouter(prefix="/search")


@router.get("")
def search(
    q:      str = Query(default="",    description="Search query"),
    type:   str = Query(default="all", description="Search mode: all | metadata | content"),
    limit:  int = Query(default=50,   ge=1, le=200),
    offset: int = Query(default=0,    ge=0),
    debug:  bool = Query(default=False, description="Include debug parsed_query"),
):
    """
    Search indexed file metadata and/or extracted content.

    type=metadata  — filename, path, extension only (Step 8 behaviour)
    type=content   — SQLite FTS5 full-text search over extracted_text
    type=all       — merged hybrid search (default)
    """
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty")

    data = unified_search(q, mode=type, limit=limit, offset=offset, debug=debug)

    import time
    t_hist = time.monotonic()
    # Step 12: Save search history
    from database.repositories import SearchHistoryRepository
    SearchHistoryRepository.add_search(q, data["total"])
    
    timing_ms = data.get("timing_ms", {})
    timing_ms["history_save"] = int((time.monotonic() - t_hist) * 1000)
    timing_ms["total"] = timing_ms.get("total", 0) + timing_ms["history_save"]

    response = {
        "status":                "ok",
        "query":                 q,
        "mode":                  data["mode"],
        "total":                 data["total"],
        "count":                 len(data["results"]),
        "limit":                 limit,
        "offset":                offset,
        "has_extracted_content": data.get("has_extracted_content", True),
        "no_content_warning":    data.get("no_content_warning", False),
        "results":               data["results"],
    }
    
    if debug:
        if "parsed_query" in data:
            response["parsed_query"] = data["parsed_query"]
        response["timing_ms"] = timing_ms
        
    log.info("Search timing: " + ", ".join(f"{k}: {v}ms" for k, v in timing_ms.items()))
        
    return response

@router.post("/rebuild-fts")
def rebuild_fts():
    """
    Developer utility: rebuild the FTS5 index from the files table.
    Clears files_fts and repopulates from all non-missing files.
    """
    try:
        result = rebuild_fts_index()
        return {
            "status":      "ok",
            "message":     "FTS index rebuilt successfully",
            "inserted":    result["inserted"],
            "duration_ms": result["duration_ms"],
        }
    except Exception as exc:
        log.error("FTS rebuild failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"FTS rebuild failed: {exc}")
