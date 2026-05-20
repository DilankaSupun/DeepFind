"""
DeepFind Engine — /extract Routes

Step 9: Text content extraction from indexed files.

Endpoints:
  POST /extract/start   — start background extraction
  GET  /extract/status  — live progress
  GET  /extract/summary — DB summary counts
"""

from fastapi import APIRouter
from indexer.extraction_manager import start_extraction, get_status, is_running
from database.repositories import get_extraction_summary

router = APIRouter(prefix="/extract")


@router.post("/start")
def extract_start():
    """
    Start background text extraction for all eligible metadata-indexed files.
    Returns 'already_running' if extraction is already in progress.
    """
    if is_running():
        return {"status": "already_running", "message": "Extraction is already in progress"}

    started = start_extraction()
    if started:
        return {"status": "ok", "message": "Text extraction started"}
    return {"status": "already_running", "message": "Extraction is already in progress"}


@router.get("/status")
def extract_status():
    """Return live extraction progress."""
    state = get_status()
    return {
        "status":          state["status"],
        "active":          state["active"],
        "files_checked":   state["files_checked"],
        "files_extracted": state["files_extracted"],
        "files_skipped":   state["files_skipped"],
        "files_failed":    state["files_failed"],
        "chunks_created":  state["chunks_created"],
        "current_path":    state["current_path"],
        "started_at":      state["started_at"],
        "completed_at":    state["completed_at"],
        "error_message":   state["error_message"],
    }


@router.get("/summary")
def extract_summary():
    """Return extraction summary from the database."""
    data = get_extraction_summary()
    return {"status": "ok", **data}
