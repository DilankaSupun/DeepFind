import logging
from fastapi import APIRouter
from utils.resource_monitor import get_system_resources

log = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["System"])

@router.get("/resources")
def get_resources():
    """
    Get live system resources including storage sizes, backend RAM, and CPU.
    """
    try:
        return get_system_resources()
    except Exception as e:
        log.error(f"Failed to fetch system resources: {e}")
        return {"status": "error", "error": str(e)}
