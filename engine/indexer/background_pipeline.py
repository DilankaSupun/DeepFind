"""
DeepFind Engine — Background Automation Pipeline (Step 18)

Orchestrates existing jobs sequentially without rewriting their internal logic:
Metadata Indexing -> Extraction -> Tagging -> Semantic Embedding

Supports start, pause, stop, resume, and debounce-triggered runs from the Watcher.
"""

import threading
import logging
import time
from datetime import datetime, timezone

from indexer import index_manager
from indexer import extraction_manager
from indexer import tagging_manager
from indexer import embedding_manager
from database.repositories import SettingsRepository

log = logging.getLogger(__name__)

# ── Pipeline State ─────────────────────────────────────────────────────────────

_lock = threading.Lock()

# Load auto-processing preference from database, default to True
_persisted_auto = SettingsRepository.get("auto_processing_enabled", "true")
_auto_processing = _persisted_auto.lower() == "true"

_state = {
    "active": False,
    "paused": False,
    "current_stage": "idle", # idle, indexing, extraction, tagging, semantic, error
    "auto_processing_enabled": _auto_processing,
    "last_error": None,
    "last_started_at": None,
    "last_completed_at": None,
    "pending_run": False, # Used for debounce trigger
}

_thread: threading.Thread | None = None
_stop_event = threading.Event()

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ── Public API ─────────────────────────────────────────────────────────────────

def get_status() -> dict:
    with _lock:
        st = dict(_state)
        
    st["indexing"] = index_manager.get_status()
    st["extraction"] = extraction_manager.get_status()
    st["tagging"] = tagging_manager.get_status()
    st["semantic"] = embedding_manager.get_status()
    
    # Check watcher status without cyclical import issues if possible, or leave it to the router
    from scanner.file_watcher import watcher_instance, get_watcher
    st["watcher_running"] = get_watcher().is_running
    
    return st

def set_auto_processing(enabled: bool):
    with _lock:
        _state["auto_processing_enabled"] = enabled
        
    try:
        SettingsRepository.set("auto_processing_enabled", "true" if enabled else "false")
    except Exception as e:
        log.error(f"Failed to persist auto_processing_enabled setting: {e}")
        
    # Dynamically start or stop the watcher
    from scanner.file_watcher import get_watcher
    if enabled:
        get_watcher().start()
    else:
        get_watcher().stop()

def trigger_pipeline():
    """
    Called by Watcher or external events.
    If the pipeline is idle and auto_processing is enabled, starts it.
    If it is already running, marks it as pending to run again after current run.
    """
    with _lock:
        if not _state["auto_processing_enabled"]:
            return
            
        if _state["active"]:
            _state["pending_run"] = True
            log.info("Pipeline already running. Scheduled a pending run.")
            return

    start_pipeline()

def start_pipeline() -> bool:
    global _thread
    
    with _lock:
        if _state["active"]:
            return False
            
        _state.update({
            "active": True,
            "paused": False,
            "last_error": None,
            "last_started_at": _now(),
            "current_stage": "starting",
            "pending_run": False
        })
        _stop_event.clear()
        
    _thread = threading.Thread(target=_worker_loop, daemon=True, name="DeepFind-Pipeline")
    _thread.start()
    log.info("Background pipeline started.")
    return True

def pause_pipeline():
    with _lock:
        if _state["active"]:
            _state["paused"] = True

def resume_pipeline():
    with _lock:
        if _state["active"] and _state["paused"]:
            _state["paused"] = False

def stop_pipeline():
    """Signals the pipeline to stop after the current active stage finishes."""
    _stop_event.set()
    with _lock:
        if _state["active"]:
            _state["paused"] = False # Unpause so it can exit
            
# ── Orchestration Loop ─────────────────────────────────────────────────────────

def _wait_for_stage(manager_is_running_fn):
    """Blocks until the stage finishes or pipeline is stopped/paused."""
    while manager_is_running_fn():
        if _stop_event.is_set():
            return False # Stopped
            
        # Handle pause
        while True:
            with _lock:
                paused = _state["paused"]
            if not paused:
                break
            if _stop_event.is_set():
                return False
            time.sleep(1)
            
        time.sleep(1)
    return True

def _run_stage(stage_name: str, start_fn, is_running_fn):
    with _lock:
        _state["current_stage"] = stage_name
        
    log.info(f"Pipeline running stage: {stage_name}")
    started = start_fn()
    
    # If the manager was already running externally, we just wait for it to finish
    if not started and not is_running_fn():
        return True # Nothing to do
        
    return _wait_for_stage(is_running_fn)

def _worker_loop():
    try:
        while True:
            try:
                # 1. Indexing
                if not _stop_event.is_set():
                    if not _run_stage("indexing", index_manager.start_indexing, index_manager.is_running):
                        break
                        
                # 2. Extraction
                if not _stop_event.is_set():
                    if not _run_stage("extraction", extraction_manager.start_extraction, extraction_manager.is_running):
                        break
                        
                # 3. Tagging
                if not _stop_event.is_set():
                    if not _run_stage("tagging", tagging_manager.start_tagging, tagging_manager.is_running):
                        break
                        
                # 4. Semantic Embedding
                if not _stop_event.is_set():
                    def semantic_is_running():
                        return embedding_manager.get_status()["active"]
                    if not _run_stage("semantic", embedding_manager.start_embedding, semantic_is_running):
                        break
                        
                # Completed
                with _lock:
                    _state["current_stage"] = "idle"
                    _state["last_completed_at"] = _now()
                    
                    # If a trigger happened while we were running, loop again!
                    if _state["pending_run"] and not _stop_event.is_set():
                        _state["pending_run"] = False
                        log.info("Pipeline restarting for pending events...")
                        continue
                    else:
                        log.info("Background pipeline completed sequentially.")
                        break
                        
            except Exception as exc:
                log.exception(f"Pipeline crash: {exc}")
                with _lock:
                    _state["current_stage"] = "error"
                    _state["last_error"] = str(exc)
                break
    finally:
        with _lock:
            _state["active"] = False
            if _state["current_stage"] not in ("idle", "error"):
                _state["current_stage"] = "stopped"
            log.info("Pipeline worker loop exited. State reset.")
