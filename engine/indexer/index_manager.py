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
    "status":            "idle",   # idle | running | completed | error
    "active":            False,
    "files_scanned":     0,
    "files_added":       0,
    "files_updated":     0,
    "files_skipped":     0,
    "errors":            0,
    "current_path":      "",
    "started_at":        "",
    "completed_at":      "",
    "error_message":     "",
    "scanned_folders":   0,
    "max_depth_reached": 0,
    "skipped_folders":   0,
    "excluded_folders":  0,
    "permission_errors": 0,
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
            "status":            "running",
            "active":            True,
            "files_scanned":     0,
            "files_added":       0,
            "files_updated":     0,
            "files_skipped":     0,
            "errors":            0,
            "current_path":      "",
            "started_at":        _now(),
            "completed_at":      "",
            "error_message":     "",
            "scanned_folders":   0,
            "max_depth_reached": 0,
            "skipped_folders":   0,
            "excluded_folders":  0,
            "permission_errors": 0,
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
    from database.repositories import FoldersRepository, FilesRepository, ScanScopeRepository
    from scanner.file_scanner import scan_folder

    # Use the new exclusion-first scan scope model
    scan_roots = ScanScopeRepository.get_effective_scan_roots()
    if not scan_roots:
        log.warning("No scan roots configured. Initialize scan scope first.")
        with _lock:
            _state.update({
                "status": "completed",
                "active": False,
                "completed_at": _now(),
                "warning": "No scan roots configured. Initialize scan scope first."
            })
        return

    # Load exclusion paths from scan_scope table
    try:
        excluded_paths = ScanScopeRepository.get_excluded_path_strings()
        log.info("Scan scope: %d exclusion path(s) loaded", len(excluded_paths))
    except Exception as exc:
        log.warning("Could not load scan scope exclusions: %s — proceeding without", exc)
        excluded_paths = set()

    log.info("Starting scan of %d active scan root(s)", len(scan_roots))

    BATCH = 100
    batch: list[dict] = []
    scanned_paths: set[str] = set()
    
    # New deep scan stats object
    scan_stats = {
        "scanned_folders": 0,
        "skipped_folders": 0,
        "excluded_folders": 0,
        "permission_errors": 0,
        "max_depth_reached": 0
    }

    def on_error(path: str, exc: Exception) -> None:
        with _lock:
            _state["errors"] += 1
            if isinstance(exc, (PermissionError, OSError)):
                scan_stats["permission_errors"] += 1
        log.debug("Scan error [%s]: %s", path, exc)

    for root_path in scan_roots:
        with _lock:
            _state["current_path"] = root_path

        log.info("Scanning: %s", root_path)

        for meta in scan_folder(root_path, on_error=on_error, excluded_paths=excluded_paths, stats=scan_stats):
            scanned_paths.add(meta["path"])
            batch.append(meta)
            with _lock:
                _state["files_scanned"] += 1
                
                # Periodically update the state with the live stats so API can see it
                if _state["files_scanned"] % 50 == 0:
                    _state["scanned_folders"] = scan_stats["scanned_folders"]
                    _state["max_depth_reached"] = scan_stats["max_depth_reached"]
                    _state["skipped_folders"] = scan_stats["skipped_folders"]
                    _state["excluded_folders"] = scan_stats["excluded_folders"]
                    _state["permission_errors"] = scan_stats["permission_errors"]

            if len(batch) >= BATCH:
                counts = FilesRepository.upsert_batch(batch)
                _add_counts(counts)
                batch.clear()

    # Flush remaining
    if batch:
        counts = FilesRepository.upsert_batch(batch)
        _add_counts(counts)

    # Mark missing (files in DB from these scanned paths that weren't seen)
    missing = FilesRepository.mark_missing(scan_roots, scanned_paths)
    if missing:
        log.info("Marked %d file(s) as missing", missing)

    with _lock:
        _state.update({
            "status":       "completed",
            "active":       False,
            "current_path": "",
            "completed_at": _now(),
            "scanned_folders": scan_stats["scanned_folders"],
            "max_depth_reached": scan_stats["max_depth_reached"],
            "skipped_folders": scan_stats["skipped_folders"],
            "excluded_folders": scan_stats["excluded_folders"],
            "permission_errors": scan_stats["permission_errors"]
        })
    log.info(
        "Indexing complete — added=%d updated=%d skipped=%d errors=%d missing=%d (max depth: %d, folders: %d)",
        _state["files_added"], _state["files_updated"],
        _state["files_skipped"], _state["errors"], missing,
        scan_stats["max_depth_reached"], scan_stats["scanned_folders"]
    )


def _add_counts(counts: dict) -> None:
    with _lock:
        _state["files_added"]   += counts.get("added", 0)
        _state["files_updated"] += counts.get("updated", 0)
        _state["files_skipped"] += counts.get("skipped", 0)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
