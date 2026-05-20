"""
DeepFind Engine — Index Manager

Manages a single background indexing job.
Module-level state is shared across all requests (thread-safe via lock).

Public API:
  start_indexing() -> bool     Start scan; False if already running
  is_running()     -> bool
  get_status()     -> dict
"""

import threading
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# ── State ──────────────────────────────────────────────────────────────────────

_lock = threading.Lock()

_state: dict = {
    "status":        "idle",   # idle | running | completed | error
    "active":        False,
    "files_scanned": 0,
    "files_added":   0,
    "files_updated": 0,
    "files_skipped": 0,
    "errors":        0,
    "current_path":  "",
    "started_at":    "",
    "completed_at":  "",
    "error_message": "",
}

_thread: threading.Thread | None = None

# ── Public API ─────────────────────────────────────────────────────────────────

def is_running() -> bool:
    with _lock:
        return _state["active"]


def get_status() -> dict:
    with _lock:
        return dict(_state)


def start_indexing() -> bool:
    """
    Start background indexing. Returns False if already running.
    Resets all counters on each new run.
    """
    global _thread
    with _lock:
        if _state["active"]:
            return False
        _state.update({
            "status":        "running",
            "active":        True,
            "files_scanned": 0,
            "files_added":   0,
            "files_updated": 0,
            "files_skipped": 0,
            "errors":        0,
            "current_path":  "",
            "started_at":    _now(),
            "completed_at":  "",
            "error_message": "",
        })

    _thread = threading.Thread(
        target=_run, daemon=True, name="DeepFind-Indexer"
    )
    _thread.start()
    log.info("Indexing thread started")
    return True


# ── Background worker ──────────────────────────────────────────────────────────

def _run() -> None:
    try:
        _do_index()
    except Exception as exc:
        log.exception("Indexing crashed: %s", exc)
        with _lock:
            _state.update({
                "status":        "error",
                "active":        False,
                "error_message": str(exc),
                "completed_at":  _now(),
            })


def _do_index() -> None:
    # Imports here to avoid circular import at module load
    from database.repositories import FoldersRepository, FilesRepository
    from scanner.file_scanner import scan_folder

    folders = FoldersRepository.list_folders(active_only=True)
    if not folders:
        log.info("No active folders to index")
        with _lock:
            _state.update({"status": "completed", "active": False, "completed_at": _now()})
        return

    log.info("Starting scan of %d active folder(s)", len(folders))

    BATCH = 100
    batch: list[dict] = []
    scanned_paths: set[str] = set()

    def on_error(path: str, exc: Exception) -> None:
        with _lock:
            _state["errors"] += 1
        log.debug("Scan error [%s]: %s", path, exc)

    for folder in folders:
        folder_path = folder["folder_path"]
        with _lock:
            _state["current_path"] = folder_path

        log.info("Scanning: %s", folder_path)

        for meta in scan_folder(folder_path, on_error=on_error):
            scanned_paths.add(meta["path"])
            batch.append(meta)
            with _lock:
                _state["files_scanned"] += 1

            if len(batch) >= BATCH:
                counts = FilesRepository.upsert_batch(batch)
                _add_counts(counts)
                batch.clear()

    # Flush remaining
    if batch:
        counts = FilesRepository.upsert_batch(batch)
        _add_counts(counts)

    # Mark missing (files in DB from these folders that weren't seen)
    folder_paths = [f["folder_path"] for f in folders]
    missing = FilesRepository.mark_missing(folder_paths, scanned_paths)
    if missing:
        log.info("Marked %d file(s) as missing", missing)

    with _lock:
        _state.update({
            "status":       "completed",
            "active":       False,
            "current_path": "",
            "completed_at": _now(),
        })
    log.info(
        "Indexing complete — added=%d updated=%d skipped=%d errors=%d missing=%d",
        _state["files_added"], _state["files_updated"],
        _state["files_skipped"], _state["errors"], missing,
    )


def _add_counts(counts: dict) -> None:
    with _lock:
        _state["files_added"]   += counts.get("added", 0)
        _state["files_updated"] += counts.get("updated", 0)
        _state["files_skipped"] += counts.get("skipped", 0)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
