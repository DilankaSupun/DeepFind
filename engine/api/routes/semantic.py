from fastapi import APIRouter
from pydantic import BaseModel
from indexer import embedding_manager

router = APIRouter(prefix="/semantic")

@router.post("/build-index")
async def build_semantic_index():
    started = embedding_manager.start_embedding()
    if not started:
        return {"status": "already_running", "message": "Semantic indexing is already in progress."}
    return {"status": "ok", "message": "Semantic index build started"}

@router.get("/status")
async def get_semantic_status():
    return embedding_manager.get_status()

@router.get("/summary")
async def get_semantic_summary():
    return embedding_manager.get_summary()
