from fastapi import APIRouter
from database.repositories import SearchHistoryRepository

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/searches")
def get_searches(limit: int = 10):
    """Return recent search queries."""
    searches = SearchHistoryRepository.get_recent(limit=limit)
    return {
        "status": "ok",
        "searches": searches
    }

@router.delete("/searches")
def clear_searches():
    """Clear all search history."""
    SearchHistoryRepository.clear_all()
    return {
        "status": "ok",
        "message": "Search history cleared"
    }
