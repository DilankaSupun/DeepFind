from fastapi import APIRouter
from scanner.file_watcher import get_watcher

router = APIRouter(prefix="/watcher", tags=["Watcher"])

@router.get("/status")
def get_watcher_status():
    return get_watcher().get_status()

@router.post("/start")
def start_watcher():
    watcher = get_watcher()
    if watcher.is_running:
        return {"status": "already_running", "active": True}
    
    success = watcher.start()
    if success:
        return {"status": "ok", "message": "File watcher started"}
    else:
        return {"status": "error", "message": "Failed to start watcher (no active folders?)"}

@router.post("/stop")
def stop_watcher():
    get_watcher().stop()
    return {"status": "ok", "message": "File watcher stopped"}

@router.post("/reload")
def reload_watcher():
    get_watcher().reload()
    return {"status": "ok", "message": "File watcher reloaded"}
