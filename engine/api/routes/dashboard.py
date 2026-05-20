from fastapi import APIRouter
from database.repositories import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def get_summary():
    """Return useful home screen counts."""
    summary = get_dashboard_summary()
    return {
        "status": "ok",
        "summary": summary
    }
