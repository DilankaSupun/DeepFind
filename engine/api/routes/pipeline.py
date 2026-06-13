"""
DeepFind Engine — /pipeline Routes (Step 18)

Endpoints to control and monitor the background automation pipeline.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from indexer import background_pipeline

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

class SettingsRequest(BaseModel):
    auto_processing_enabled: bool

@router.get("/status")
def get_status():
    return background_pipeline.get_status()

@router.post("/start")
def start():
    started = background_pipeline.start_pipeline()
    if started:
        return {"status": "ok", "message": "Pipeline started"}
    else:
        return {"status": "already_running", "message": "Pipeline is already active"}

@router.post("/pause")
def pause():
    background_pipeline.pause_pipeline()
    return {"status": "ok", "message": "Pipeline paused"}

@router.post("/resume")
def resume():
    background_pipeline.resume_pipeline()
    return {"status": "ok", "message": "Pipeline resumed"}

@router.post("/stop")
def stop():
    background_pipeline.stop_pipeline()
    return {"status": "ok", "message": "Pipeline stopping"}

@router.post("/settings")
def update_settings(req: SettingsRequest):
    background_pipeline.set_auto_processing(req.auto_processing_enabled)
    return {"status": "ok", "auto_processing_enabled": req.auto_processing_enabled}
