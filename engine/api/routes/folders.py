"""
DeepFind Engine — /folders Routes

Step 6: Folder discovery and management.

Endpoints:
  GET    /folders                    — List all folders (active + inactive)
  POST   /folders                    — Add a folder path manually
  GET    /folders/discover           — Detect common folders and drives (no DB write)
  POST   /folders/initialize-defaults — Save detected defaults to DB
  PATCH  /folders/{id}/toggle        — Enable / disable a folder
  DELETE /folders/{id}               — Soft-delete a folder (set is_active=0)

IMPORTANT: Static paths (/discover, /initialize-defaults) MUST be registered
           BEFORE dynamic paths (/{folder_id}) to avoid FastAPI routing conflicts.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from database.repositories import FoldersRepository
from scanner.discovery import discover_all

router = APIRouter(prefix="/folders")


# ── Request models ─────────────────────────────────────────────────────────────

class AddFolderRequest(BaseModel):
    folder_path: str
    source_type: str = "manual"
    is_active:   int = 1

    @field_validator("folder_path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("folder_path must not be empty")
        return v


# ── Static routes (must come before /{folder_id}) ─────────────────────────────

@router.get("/discover")
def discover_folders():
    """
    Detect common user folders and available local drives — NO database writes.

    Returns:
      common_folders — list of detected user folders (Desktop, Documents, etc.)
      drives         — list of available local drive letters (C:, D:, etc.)

    Active defaults:
      Desktop, Documents, Downloads, Pictures → is_active_default = true
      Videos, Music, all drives              → is_active_default = false
    """
    result = discover_all()
    return {
        "status":         "ok",
        "common_folders": result["common_folders"],
        "drives":         result["drives"],
        "total_detected": len(result["common_folders"]) + len(result["drives"]),
    }


@router.post("/initialize-defaults")
def initialize_defaults():
    """
    Detect common folders and drives, then save them all to indexed_folders.

    - Idempotent: existing paths are updated (not duplicated).
    - Common folders use their is_active_default value.
    - Drives are always saved as inactive.
    - Returns a summary of what was saved.
    """
    result = discover_all()
    all_discovered = result["common_folders"] + result["drives"]

    saved = []
    for item in all_discovered:
        folder = FoldersRepository.add(
            folder_path=item["path"],
            source_type=item["source_type"],
            is_active=1 if item["is_active_default"] else 0,
        )
        saved.append(folder)

    return {
        "status":      "ok",
        "initialized": len(saved),
        "folders":     saved,
    }


# ── Dynamic routes ─────────────────────────────────────────────────────────────

@router.patch("/{folder_id}/toggle")
def toggle_folder(folder_id: int):
    """
    Flip is_active for a folder (1→0 or 0→1).
    Returns the updated folder record.
    """
    updated = FoldersRepository.toggle(folder_id)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Folder with id={folder_id} not found",
        )
    return {
        "status": "ok",
        "folder": updated,
    }


@router.delete("/{folder_id}")
def remove_folder(folder_id: int):
    """
    Soft-delete a folder (is_active=0).
    Returns 404 if not found or already inactive.
    """
    removed = FoldersRepository.deactivate(folder_id)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Folder with id={folder_id} not found or already inactive",
        )
    return {
        "status":  "ok",
        "message": f"Folder {folder_id} deactivated",
    }


# ── Collection routes ──────────────────────────────────────────────────────────

@router.get("")
def list_folders():
    """Return ALL indexed folders (active and inactive) for display in the UI."""
    folders = FoldersRepository.list_all()
    return {
        "status":  "ok",
        "count":   len(folders),
        "folders": folders,
    }


@router.post("")
def add_folder(body: AddFolderRequest):
    """
    Manually add a folder path (from Electron dialog).
    Idempotent: adding an existing path re-activates it.
    """
    folder = FoldersRepository.add(
        folder_path=body.folder_path,
        source_type=body.source_type,
        is_active=body.is_active,
    )
    return {
        "status": "ok",
        "folder": folder,
    }
