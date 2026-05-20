"""
DeepFind Engine — /tags Routes (Step 11)

Endpoints for background auto-tagging.
"""

import logging
from fastapi import APIRouter, Query
from indexer.tagging_manager import start_tagging, get_status
from database.repositories import get_tagging_summary

log = logging.getLogger(__name__)
router = APIRouter(prefix="/tags")


@router.post("/generate")
def generate(force: bool = Query(default=False, description="Regenerate tags for all files")):
    """
    Start background tag generation.
    Returns already_running if a tagging process is active.
    """
    started = start_tagging(force=force)
    if started:
        return {"status": "ok", "message": "Tag generation started"}
    else:
        return {"status": "already_running", "message": "Tagging is already in progress"}


@router.get("/status")
def status():
    """Get the current progress of the background tagging process."""
    return get_status()


@router.get("/summary")
def summary():
    """Get a summary of tags in the database."""
    return get_tagging_summary()
