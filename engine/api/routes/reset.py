"""
DeepFind Engine — Reset Routes (Step 19)
Allows clearing search indexes or performing a full app data reset.
"""

import os
import logging
from fastapi import APIRouter
from pathlib import Path

from database.db import get_connection, init_db
from config import DB_PATH, DATA_DIR
from scanner.file_watcher import get_watcher
from database.repositories import SettingsRepository

log = logging.getLogger(__name__)

router = APIRouter(prefix="/reset", tags=["Reset"])

def _stop_workers():
    import time
    # Stop pipeline safely
    from indexer.background_pipeline import stop_pipeline
    stop_pipeline()
    
    # Stop watcher if running
    watcher = get_watcher()
    if watcher.is_running:
        watcher.stop()
        
    # Give background threads (like watcher's worker_loop which has a 2s timeout) time to release DB locks
    time.sleep(2.5)

def _execute_with_retry(conn, query, retries=5):
    import time
    for i in range(retries):
        try:
            conn.execute(query)
            return
        except Exception as e:
            if "locked" in str(e).lower() and i < retries - 1:
                time.sleep(1.5)
            else:
                raise

def _fast_clear_files(conn):
    """
    Clearing 100k+ files takes minutes if we don't drop FTS triggers first.
    This drops triggers, truncates files, rebuilds FTS (to empty it), 
    and lets init_db() recreate the triggers later.
    """
    conn.execute("DROP TRIGGER IF EXISTS files_ai")
    conn.execute("DROP TRIGGER IF EXISTS files_ad")
    conn.execute("DROP TRIGGER IF EXISTS files_au")
    
    _execute_with_retry(conn, "DELETE FROM files")
    
    try:
        conn.execute("INSERT INTO files_fts(files_fts) VALUES('rebuild')")
    except Exception as e:
        log.warning("FTS rebuild failed: %s", e)

def _get_table_count(conn, table_name: str) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()["count"]
    except Exception:
        return 0

def _get_human_size(path: Path) -> str:
    if not path.exists():
        return "0 MB"
    size = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

@router.get("/preview")
def preview_reset():
    db_size = _get_human_size(DB_PATH)
    faiss_path = DATA_DIR / "faiss.index"
    faiss_exists = faiss_path.exists()
    faiss_size = _get_human_size(faiss_path)

    stats = {
        "files": 0,
        "folders": 0,
        "chunks": 0,
        "embeddings": 0,
        "search_history": 0,
        "faiss_index_exists": faiss_exists,
        "faiss_index_size_human": faiss_size,
        "database_size_human": db_size
    }

    try:
        with get_connection() as conn:
            stats["files"] = _get_table_count(conn, "files")
            stats["folders"] = _get_table_count(conn, "indexed_folders")
            stats["chunks"] = _get_table_count(conn, "file_chunks")
            stats["embeddings"] = _get_table_count(conn, "embeddings")
            stats["search_history"] = _get_table_count(conn, "search_history")
    except Exception as e:
        log.error("Preview failed to read DB: %s", e)

    return {"status": "ok", "index": stats}

@router.post("/index")
def reset_index():
    _stop_workers()

    cleared = {
        "files": False,
        "chunks": False,
        "fts": False,
        "embeddings": False,
        "search_history": False,
        "faiss_index": False
    }

    try:
        with get_connection() as conn:
            # Set high busy timeout for this connection
            conn.execute("PRAGMA busy_timeout = 15000")
            
            # Fast clear files and FTS
            _fast_clear_files(conn)
            cleared["files"] = True
            cleared["fts"] = True
            
            try:
                _execute_with_retry(conn, "DELETE FROM file_chunks")
                cleared["chunks"] = True
            except Exception:
                pass
                
            try:
                _execute_with_retry(conn, "DELETE FROM embeddings")
                cleared["embeddings"] = True
            except Exception:
                pass
                
            try:
                _execute_with_retry(conn, "DELETE FROM search_history")
                cleared["search_history"] = True
            except Exception:
                pass
                
        # Recreate dropped triggers
        init_db()

        # FAISS index
        faiss_path = DATA_DIR / "faiss.index"
        if faiss_path.exists():
            try:
                faiss_path.unlink()
                cleared["faiss_index"] = True
            except Exception as e:
                log.warning("Could not delete FAISS index: %s", e)
        else:
            cleared["faiss_index"] = True

        # Vacuum to shrink file
        try:
            with get_connection() as conn:
                conn.execute("VACUUM")
        except Exception:
            pass

        return {
            "status": "ok",
            "message": "Search index cleared. Indexed folders were kept.",
            "cleared": cleared
        }
    except Exception as e:
        log.error("Failed to reset index: %s", e)
        return {"status": "error", "message": f"Reset index failed: {str(e)}"}

@router.post("/app-data")
def reset_app_data():
    _stop_workers()

    cleared = {
        "files": False,
        "indexed_folders": False,
        "chunks": False,
        "fts": False,
        "embeddings": False,
        "search_history": False,
        "settings": False,
        "faiss_index": False
    }

    try:
        with get_connection() as conn:
            conn.execute("PRAGMA busy_timeout = 15000")
            
            _fast_clear_files(conn)
            cleared["files"] = True
            cleared["fts"] = True
            
            _execute_with_retry(conn, "DELETE FROM indexed_folders")
            cleared["indexed_folders"] = True
            
            try:
                _execute_with_retry(conn, "DELETE FROM file_chunks")
                cleared["chunks"] = True
            except Exception:
                pass
                
            try:
                _execute_with_retry(conn, "DELETE FROM embeddings")
                cleared["embeddings"] = True
            except Exception:
                pass
                
            try:
                _execute_with_retry(conn, "DELETE FROM search_history")
                cleared["search_history"] = True
            except Exception:
                pass
                
            try:
                _execute_with_retry(conn, "DELETE FROM settings")
                cleared["settings"] = "reset_to_defaults"
            except Exception:
                pass
                
        # Recreate dropped triggers and default settings
        init_db()

        try:
            from database.repositories import ScanScopeRepository
            ScanScopeRepository.clear_user_rules()
            ScanScopeRepository.initialize_system_exclusions()
            cleared["scan_scope"] = "reset_to_defaults"
        except Exception as e:
            log.warning("Could not reset scan scope: %s", e)

        # FAISS index
        faiss_path = DATA_DIR / "faiss.index"
        if faiss_path.exists():
            try:
                faiss_path.unlink()
                cleared["faiss_index"] = True
            except Exception as e:
                log.warning("Could not delete FAISS index: %s", e)
        else:
            cleared["faiss_index"] = True

        # Vacuum to shrink file
        try:
            with get_connection() as conn:
                conn.execute("VACUUM")
        except Exception:
            pass

        return {
            "status": "ok",
            "message": "DeepFind app data reset successfully.",
            "cleared": cleared
        }
    except Exception as e:
        log.error("Failed to reset app data: %s", e)
        return {"status": "error", "message": f"Reset app data failed: {str(e)}"}


@router.post("/scan-scope")
def reset_scan_scope():
    """
    Reset scan scope: clear all user rules and re-seed system exclusions.
    Does NOT reset indexed file data — use /reset/index for that.
    Called automatically as part of /reset/app-data.
    """
    try:
        from database.repositories import ScanScopeRepository
        ScanScopeRepository.clear_all()
        seeded = ScanScopeRepository.initialize_system_exclusions()
        return {
            "status":  "ok",
            "message": f"Scan scope reset. {seeded} system exclusions re-seeded.",
            "seeded":  seeded,
        }
    except Exception as e:
        log.error("Failed to reset scan scope: %s", e)
        return {"status": "error", "message": f"Scan scope reset failed: {str(e)}"}
