"""
DeepFind Engine — Extraction Manager

Background text extraction worker. Mirrors the indexer/index_manager.py pattern.
Module-level state shared across all requests; thread-safe via lock.

Public API:
  start_extraction() -> bool    Start extraction; False if already running
  is_running()       -> bool
  get_status()       -> dict
"""

import threading
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import SUPPORTED_TEXT_EXTENSIONS, MAX_FILE_SIZE_BYTES

log = logging.getLogger(__name__)

# ── State ──────────────────────────────────────────────────────────────────────

_lock = threading.Lock()

_state: dict = {
    "status":          "idle",   # idle | running | completed | error
    "active":          False,
    "files_checked":   0,
    "files_extracted": 0,
    "files_skipped":   0,
    "files_failed":    0,
    "chunks_created":  0,
    "current_path":    "",
    "started_at":      "",
    "completed_at":    "",
    "error_message":   "",
}

_thread: threading.Thread | None = None


# ── Public API ─────────────────────────────────────────────────────────────────

def is_running() -> bool:
    with _lock:
        return _state["active"]


def get_status() -> dict:
    with _lock:
        return dict(_state)


def start_extraction() -> bool:
    """
    Start background extraction. Returns False if already running.
    Resets all counters on each new run.
    """
    global _thread
    with _lock:
        if _state["active"]:
            return False
        _state.update({
            "status":          "running",
            "active":          True,
            "files_checked":   0,
            "files_extracted": 0,
            "files_skipped":   0,
            "files_failed":    0,
            "chunks_created":  0,
            "current_path":    "",
            "started_at":      _now(),
            "completed_at":    "",
            "error_message":   "",
        })

    _thread = threading.Thread(
        target=_run, daemon=True, name="DeepFind-Extractor"
    )
    _thread.start()
    log.info("Extraction thread started")
    return True


# ── Background worker ──────────────────────────────────────────────────────────

def _run() -> None:
    try:
        _do_extract()
    except Exception as exc:
        log.exception("Extraction crashed: %s", exc)
        with _lock:
            _state.update({
                "status":        "error",
                "active":        False,
                "error_message": str(exc),
                "completed_at":  _now(),
            })


def _do_extract() -> None:
    from database.repositories import FilesRepository, ChunksRepository
    from extractors.extractor_dispatcher import extract_file, chunk_text

    # Fetch all eligible files in one query (avoids holding connection open)
    candidates = FilesRepository.get_files_for_extraction(SUPPORTED_TEXT_EXTENSIONS)

    if not candidates:
        log.info("No files eligible for text extraction")
        with _lock:
            _state.update({"status": "completed", "active": False, "completed_at": _now()})
        return

    log.info("Starting extraction for %d candidate file(s)", len(candidates))

    for file_meta in candidates:
        file_id   = file_meta["id"]
        file_path = Path(file_meta["path"])
        file_size = file_meta.get("size") or 0

        with _lock:
            _state["files_checked"] += 1
            _state["current_path"]   = str(file_path)

        # ── Check file exists ────────────────────────────────────────────────
        if not file_path.exists():
            _mark_failed(file_id, "File no longer exists")
            continue

        # ── Skip large files ─────────────────────────────────────────────────
        if file_size > MAX_FILE_SIZE_BYTES:
            log.debug("Skip large file (%.1f MB): %s",
                      file_size / (1024 * 1024), file_path.name)
            FilesRepository.update_extracted_text(
                file_id,
                text=None,
                status="content_skipped_large_file",
                error_message=f"File exceeds {MAX_FILE_SIZE_BYTES // (1024*1024)} MB limit",
            )
            with _lock:
                _state["files_skipped"] += 1
            continue

        # ── Extract text ─────────────────────────────────────────────────────
        try:
            text, err = extract_file(file_path)
        except Exception as exc:
            _mark_failed(file_id, f"Extraction error: {exc}")
            continue

        if err:
            _mark_failed(file_id, err)
            continue

        # ── Save text + chunks ───────────────────────────────────────────────
        try:
            FilesRepository.update_extracted_text(
                file_id,
                text=text or None,
                status="content_extracted",
            )

            # Chunk and store for future semantic search
            chunks = chunk_text(text) if text else []
            if chunks:
                ChunksRepository.clear_for_file(file_id)
                n = ChunksRepository.insert_batch(file_id, chunks)
                with _lock:
                    _state["chunks_created"] += n

            with _lock:
                _state["files_extracted"] += 1

            log.debug(
                "Extracted %s → %d chars, %d chunks",
                file_path.name, len(text or ""), len(chunks),
            )

        except Exception as exc:
            _mark_failed(file_id, f"DB write error: {exc}")

    with _lock:
        _state.update({
            "status":       "completed",
            "active":       False,
            "current_path": "",
            "completed_at": _now(),
        })
        extracted = _state["files_extracted"]
        skipped   = _state["files_skipped"]
        failed    = _state["files_failed"]
        chunks    = _state["chunks_created"]

    log.info(
        "Extraction complete — extracted=%d skipped=%d failed=%d chunks=%d",
        extracted, skipped, failed, chunks,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mark_failed(file_id: int, error_msg: str) -> None:
    from database.repositories import FilesRepository
    try:
        FilesRepository.update_extracted_text(
            file_id,
            text=None,
            status="extraction_failed",
            error_message=error_msg[:500],  # cap length
        )
    except Exception as exc:
        log.error("Failed to mark file %d as failed: %s", file_id, exc)

    with _lock:
        _state["files_failed"] += 1

    log.debug("Extraction failed [id=%d]: %s", file_id, error_msg)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
