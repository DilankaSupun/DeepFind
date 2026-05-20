"""
DeepFind Engine — /db/status Route

Step 5: Confirms the database is initialized and all tables exist.
"""

from fastapi import APIRouter
from database.db import get_db_info

router = APIRouter()


@router.get("/db/status")
def db_status():
    """
    Database status check.

    Returns:
      status         — "ok" if database is connected and tables exist
      database       — "connected" or "error"
      tables_created — true when all required tables are present
      path           — absolute path to the .db file (for debugging)
      size_bytes     — .db file size on disk
      tables         — list of all tables in the database
    """
    info = get_db_info()

    return {
        "status":         "ok"          if info["tables_ok"] else "error",
        "database":       "connected"   if info["connected"] else "error",
        "tables_created": info["tables_ok"],
        "db_path":        info["path"],
        "size_bytes":     info["size_bytes"],
        "tables":         info["tables"],
    }
