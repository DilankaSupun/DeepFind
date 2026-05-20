from fastapi import APIRouter
from database.repositories import FilesRepository

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/recent")
def get_recent_files(limit: int = 10):
    """Return recently modified indexed files."""
    files = FilesRepository.get_recent_modified(limit=limit)
    return {
        "status": "ok",
        "files": files
    }

@router.get("/recent-indexed")
def get_recent_indexed_files(limit: int = 10):
    """Return files most recently added or updated in DeepFind's index."""
    files = FilesRepository.get_recent_indexed(limit=limit)
    return {
        "status": "ok",
        "files": files
    }
