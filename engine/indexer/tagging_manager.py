"""
DeepFind Engine — Tagging Manager

Background worker for automatic file tagging (Step 11).
Mirrors index_manager.py and extraction_manager.py patterns.

Public API:
  start_tagging(force: bool) -> bool
  is_running()       -> bool
  get_status()       -> dict
"""

import threading
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

# ── State ──────────────────────────────────────────────────────────────────────

_lock = threading.Lock()

_state: dict = {
    "status":        "idle",   # idle | running | completed | error
    "active":        False,
    "files_checked": 0,
    "files_tagged":  0,
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


def start_tagging(force: bool = False) -> bool:
    """
    Start background tagging. Returns False if already running.
    Resets all counters.
    """
    global _thread
    with _lock:
        if _state["active"]:
            return False
        _state.update({
            "status":        "running",
            "active":        True,
            "files_checked": 0,
            "files_tagged":  0,
            "files_skipped": 0,
            "errors":        0,
            "current_path":  "",
            "started_at":    _now(),
            "completed_at":  "",
            "error_message": "",
        })

    _thread = threading.Thread(
        target=_run, args=(force,), daemon=True, name="DeepFind-Tagger"
    )
    _thread.start()
    log.info("Tagging thread started (force=%s)", force)
    return True


# ── Background worker ──────────────────────────────────────────────────────────

def _run(force: bool) -> None:
    try:
        _do_tagging(force)
    except Exception as exc:
        log.exception("Tagging crashed: %s", exc)
        with _lock:
            _state.update({
                "status":        "error",
                "active":        False,
                "error_message": str(exc),
                "completed_at":  _now(),
            })


def _do_tagging(force: bool) -> None:
    from database.repositories import FilesRepository
    from ai.tag_generator import generate_tags

    candidates = FilesRepository.get_files_for_tagging(force=force)

    if not candidates:
        log.info("No files eligible for tagging")
        with _lock:
            _state.update({"status": "completed", "active": False, "completed_at": _now()})
        return

    log.info("Starting tagging for %d candidate file(s)", len(candidates))

    for file_meta in candidates:
        file_id = file_meta["id"]
        file_path_str = file_meta["path"]
        file_name = file_meta["name"]
        file_ext = file_meta.get("extension") or ""
        extracted_text = file_meta.get("extracted_text") or ""

        with _lock:
            _state["files_checked"] += 1
            _state["current_path"]   = file_path_str

        # ── Check file exists ────────────────────────────────────────────────
        if not Path(file_path_str).exists():
            log.debug("Skip tagging (missing): %s", file_name)
            with _lock:
                _state["files_skipped"] += 1
            continue

        # ── Generate Tags ────────────────────────────────────────────────────
        try:
            tags = generate_tags(
                name=file_name,
                path=file_path_str,
                extension=file_ext,
                extracted_text=extracted_text
            )

            if tags:
                FilesRepository.update_tags(file_id, tags)
                with _lock:
                    _state["files_tagged"] += 1
                log.debug("Tagged %s -> [%s]", file_name, tags)
            else:
                with _lock:
                    _state["files_skipped"] += 1

        except Exception as exc:
            log.error("Failed to tag file %d: %s", file_id, exc)
            with _lock:
                _state["errors"] += 1
            continue

    with _lock:
        _state.update({
            "status":       "completed",
            "active":       False,
            "current_path": "",
            "completed_at": _now(),
        })
        tagged  = _state["files_tagged"]
        skipped = _state["files_skipped"]
        errors  = _state["errors"]

    log.info(
        "Tagging complete — tagged=%d skipped=%d errors=%d",
        tagged, skipped, errors
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
