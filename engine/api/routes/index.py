"""
DeepFind Engine — /index Routes

Step 7: Metadata scanning.

Endpoints:
  POST /index/start    — Start background scan (idempotent)
  GET  /index/status   — Polling endpoint for live scan progress
  GET  /index/summary  — DB-level summary (total files, by status)
"""

from fastapi import APIRouter

from indexer.index_manager import start_indexing, is_running, get_status
from database.repositories import FilesRepository, FoldersRepository

router = APIRouter(prefix="/index")


@router.post("/start")
def start():
    """
    Start the file metadata scanner in the background.
    Returns 'already_running' if a scan is already in progress.
    """
    if is_running():
        return {"status": "already_running", "message": "Indexing is already in progress"}
    start_indexing()
    return {"status": "ok", "message": "Indexing started"}


@router.get("/status")
def status():
    """Return live indexing progress. Poll this while active=true."""
    return get_status()


@router.get("/summary")
def summary():
    """Return DB-level file statistics."""
    by_status    = FilesRepository.count_by_status()
    active_count = len(FoldersRepository.list_folders(active_only=True))
    total        = sum(by_status.values())
    return {
        "status":           "ok",
        "total_files":      total,
        "metadata_indexed": by_status.get("metadata_indexed", 0),
        "missing":          by_status.get("missing", 0),
        "active_sources":   active_count,
        "by_status":        by_status,
    }
