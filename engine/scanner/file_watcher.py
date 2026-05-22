"""
DeepFind Engine — Background File Watcher (Step 17)
Monitors active indexed folders and dynamically updates the SQLite database.
"""
import os
import time
import logging
import threading
from queue import Queue, Empty
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pathlib import Path
from database.db import get_connection
from database.repositories import FoldersRepository
from scanner.metadata_reader import read_metadata

log = logging.getLogger(__name__)

# Single instance state
watcher_instance = None


class DebouncedFileEventHandler(FileSystemEventHandler):
    def __init__(self, event_queue: Queue):
        super().__init__()
        self.queue = event_queue

    def _enqueue(self, event_type, path, old_path=None):
        # Ignore obvious temp/system files
        if "\\$RECYCLE.BIN\\" in path or "/.git/" in path or "/node_modules/" in path:
            return
        if "/.venv/" in path or "/__pycache__/" in path:
            return
            
        self.queue.put({
            "type": event_type,
            "path": path,
            "old_path": old_path,
            "time": time.time()
        })

    def on_created(self, event):
        if not event.is_directory:
            self._enqueue("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._enqueue("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._enqueue("deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._enqueue("moved", event.dest_path, old_path=event.src_path)


class FileWatcher:
    def __init__(self):
        self.observer = None
        self.event_queue = Queue()
        self.worker_thread = None
        self.is_running = False
        self.stats = {
            "processed_events": 0,
            "queued_events": 0,
            "errors": 0,
            "last_event_at": None,
            "last_processed_at": None,
            "watched_folders": 0
        }

    def start(self):
        if self.is_running:
            return False

        active_folders = [f["folder_path"] for f in FoldersRepository.list_folders(active_only=True)]
        if not active_folders:
            log.warning("FileWatcher: No active folders to watch.")
            return False

        self.observer = Observer()
        handler = DebouncedFileEventHandler(self.event_queue)

        watched_count = 0
        for f in active_folders:
            if os.path.exists(f):
                self.observer.schedule(handler, f, recursive=True)
                watched_count += 1
            else:
                log.warning(f"FileWatcher: Path not found {f}")

        if watched_count == 0:
            return False

        self.stats["watched_folders"] = watched_count
        self.is_running = True

        self.observer.start()
        
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        log.info(f"FileWatcher started for {watched_count} folders.")
        return True

    def stop(self):
        if not self.is_running:
            return False
            
        self.is_running = False
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=3)
        self.observer = None
        log.info("FileWatcher stopped.")
        return True

    def reload(self):
        self.stop()
        time.sleep(0.5)
        self.start()

    def get_status(self):
        self.stats["queued_events"] = self.event_queue.qsize()
        return {
            "status": "ok",
            "active": self.is_running,
            **self.stats
        }

    def _worker_loop(self):
        """Processes events in batches with debounce logic."""
        # Simple debounce: group by path within a 1s window
        batch_delay = 1.0
        
        while self.is_running:
            try:
                # Wait for at least one event
                item = self.event_queue.get(timeout=2)
            except Empty:
                continue

            self.stats["last_event_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

            # Collect all items arriving in the next `batch_delay` seconds
            batch = [item]
            end_time = time.time() + batch_delay
            while True:
                time_left = end_time - time.time()
                if time_left <= 0:
                    break
                try:
                    next_item = self.event_queue.get(timeout=time_left)
                    batch.append(next_item)
                except Empty:
                    break
            
            # Reduce to latest event per path (crude debounce)
            processed_map = {}
            for e in batch:
                if e["type"] == "moved":
                    # For move, we process delete of old and create of new
                    processed_map[e["old_path"]] = {"type": "deleted", "path": e["old_path"]}
                    processed_map[e["path"]] = {"type": "created", "path": e["path"]}
                else:
                    processed_map[e["path"]] = e
            
            self._process_batch(list(processed_map.values()))

    def _process_batch(self, events):
        try:
            with get_connection() as conn:
                for e in events:
                    path = e["path"].replace("\\", "/")
                    etype = e["type"]
                    
                    if etype in ("created", "modified"):
                        meta = read_metadata(Path(path))
                        if meta:
                            conn.execute("""
                                INSERT INTO files (path, name, extension, size, created_at, modified_at, status, last_indexed_at)
                                VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
                                ON CONFLICT(path) DO UPDATE SET
                                    name=excluded.name,
                                    size=excluded.size,
                                    modified_at=excluded.modified_at,
                                    status='active',
                                    last_indexed_at=CURRENT_TIMESTAMP
                            """, (
                                meta["path"], meta["name"], meta["extension"],
                                meta["size"], meta["created_at"], meta["modified_at"]
                            ))
                        else:
                            # if extracting failed, might be missing/locked
                            pass
                            
                    elif etype == "deleted":
                        conn.execute("UPDATE files SET status='missing' WHERE path=?", (path,))
                        
                conn.commit()
                
            self.stats["processed_events"] += len(events)
            self.stats["last_processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            
        except Exception as ex:
            log.error(f"Watcher batch error: {ex}")
            self.stats["errors"] += 1


def get_watcher():
    global watcher_instance
    if not watcher_instance:
        watcher_instance = FileWatcher()
    return watcher_instance
