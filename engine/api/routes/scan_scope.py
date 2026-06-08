"""
DeepFind Engine — /scan-scope Routes (Step 19)

Replaces the old manual folder toggle model with an automatic scan scope.
DeepFind scans allowed locations automatically; users manage exclusions.

Endpoints:
  GET    /scan-scope/status         — current scan scope (roots, exclusions)
  POST   /scan-scope/initialize     — auto-discover + seed defaults (first run / reset)
  POST   /scan-scope/exclude        — add a user exclusion path
  DELETE /scan-scope/exclude/{id}   — remove a user exclusion
  POST   /scan-scope/reload         — reload watcher to pick up scope changes
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from database.repositories import FoldersRepository, ScanScopeRepository
from scanner.discovery import discover_all
from config import SYSTEM_EXCLUDED_PATHS, AUTO_SCAN_ENABLED

log = logging.getLogger(__name__)
router = APIRouter(prefix="/scan-scope")


# ── Request models ─────────────────────────────────────────────────────────────

class PathRequest(BaseModel):
    path: str

    @field_validator("path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("path must not be empty")
        # Normalize to forward slashes
        return v.replace("\\", "/").rstrip("/")


# ── Static routes ──────────────────────────────────────────────────────────────

@router.get("/status")
def get_scan_scope_status():
    """
    Returns the full current scan scope:
    - automatic_scan:    always True in new model
    - scan_roots:        all automatically detected local drives and user folders
    - user_exclusions:   user-added exclusion paths
    - system_exclusions: built-in system paths that are always excluded
    """
    all_folders = FoldersRepository.list_all()
    
    # In the new model, all active folders are scan roots (drives and common folders)
    scan_roots = [f for f in all_folders if f.get("is_active") == 1]

    # Scan scope rules
    all_rules = ScanScopeRepository.get_all()
    system_exclusions = [r for r in all_rules if r["source_type"] == "system" and r["scan_mode"] == "exclude"]
    user_exclusions   = [r for r in all_rules if r["source_type"] == "user"   and r["scan_mode"] == "exclude"]

    effective_roots = ScanScopeRepository.get_effective_scan_roots()

    return {
        "status":            "ok",
        "automatic_scan":    AUTO_SCAN_ENABLED,
        "initialized":       len(scan_roots) > 0,
        "scan_roots_count":  len(scan_roots),
        "effective_roots_count": len(effective_roots),
        "scan_roots":        scan_roots,
        "user_exclusions":   user_exclusions,
        "system_exclusions": system_exclusions,
        "total_excluded":    len(system_exclusions) + len(user_exclusions),
    }


@router.post("/initialize")
def initialize_scan_scope():
    """
    Auto-discover drives and common user folders, then:
    1. Save all common folders as active scan roots (is_active = 1).
    2. Save all drives as active scan roots (is_active = 1).
    3. Seed built-in system exclusions into scan_scope table.

    Safe to call multiple times (idempotent).
    """
    discovery = discover_all()
    common_folders = discovery["common_folders"]
    drives = discovery["drives"]

    saved_roots = []
    
    # Save all common folders as ACTIVE scan roots
    for item in common_folders:
        folder = FoldersRepository.add(
            folder_path=item["path"],
            source_type="auto_common_folder",
            is_active=1,
        )
        saved_roots.append(folder)

    # Save all local drives as ACTIVE scan roots
    for item in drives:
        folder = FoldersRepository.add(
            folder_path=item["path"],
            source_type="auto_drive",
            is_active=1,
        )
        saved_roots.append(folder)

    # Seed system exclusions
    seeded = ScanScopeRepository.initialize_system_exclusions()

    log.info(
        "Scan scope initialized: %d auto-scan roots (folders + drives), %d system exclusions seeded",
        len(saved_roots), seeded,
    )

    return {
        "status":            "ok",
        "message":           "Scan scope initialized. Drives and common folders are automatically scanned.",
        "scan_roots":        saved_roots,
        "system_exclusions_seeded": seeded,
    }


# ── Exclusion management ───────────────────────────────────────────────────────

@router.post("/exclude")
def add_exclusion(body: PathRequest):
    """
    Add a user-defined exclusion path.
    The scanner and watcher will skip this path from the next run.
    """
    rule = ScanScopeRepository.add_rule(
        path=body.path,
        scan_mode="exclude",
        source_type="user",
    )
    log.info("User exclusion added: %s", body.path)
    return {"status": "ok", "rule": rule}


@router.delete("/exclude/{rule_id}")
def remove_exclusion(rule_id: int):
    """
    Remove a user-defined exclusion by ID.
    System exclusions (source_type = 'system') should not be removed via this endpoint.
    """
    # Prevent removal of system exclusions via this endpoint
    all_rules = ScanScopeRepository.get_all()
    rule = next((r for r in all_rules if r["id"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Exclusion rule id={rule_id} not found")
    if rule.get("source_type") == "system":
        raise HTTPException(
            status_code=403,
            detail="System exclusions cannot be removed. They protect system folders."
        )

    removed = ScanScopeRepository.remove_rule(rule_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Exclusion rule id={rule_id} not found")

    log.info("User exclusion removed: id=%d path=%s", rule_id, rule.get("path", ""))
    return {"status": "ok", "message": f"Exclusion removed: {rule.get('path', '')}"}




# ── Reload watcher ─────────────────────────────────────────────────────────────

@router.post("/reload")
def reload_scan_scope():
    """
    Reload the file watcher to pick up scope changes.
    Called after adding/removing exclusions or includes.
    """
    try:
        from scanner.file_watcher import get_watcher
        watcher = get_watcher()
        watcher.reload()
        return {"status": "ok", "message": "Scan scope reloaded. Watcher restarted."}
    except Exception as exc:
        log.warning("Watcher reload failed: %s", exc)
        return {"status": "ok", "message": "Scope saved. Watcher reload failed (may not be running)."}
