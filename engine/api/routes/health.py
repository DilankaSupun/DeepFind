"""
DeepFind Engine — /health Route

Step 3: Health check endpoint only.
Returns JSON confirming the engine is alive and reachable.

Future routes added in later steps:
  /index   — trigger folder indexing
  /search  — search files
  /files   — file detail lookup
  /folders — manage indexed folders
  /settings — app settings
"""

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint.

    Returns engine status, service name, version, and current UTC timestamp.
    The React frontend will poll this to confirm the backend is running.
    """
    import os
    return {
        "status": "ok",
        "service": "deepfind-engine",
        "instance_id": os.environ.get("DEEPFIND_INSTANCE_ID", "dev-instance"),
        "api_version": "1",
        "version": "0.1.0",
        "ready": True,
        "backend": "FastAPI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
