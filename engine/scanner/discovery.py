"""
DeepFind Engine — Folder & Drive Discovery

Detects common user folders and available local drives on the current system.
No file scanning happens here — only folder/drive paths are returned.

Step 6: Discovery only.
Step 7: Will scan within discovered folders using SCAN_EXCLUSIONS.
"""

import os
import string
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ── Exclusion list (used by the scanner in Step 7) ────────────────────────────
#
# Directory names that will be skipped during file indexing.
# Listed here as a single source of truth — imported by the scanner module.
#
SCAN_EXCLUSIONS: frozenset[str] = frozenset({
    # Windows system directories
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
    "AppData",
    "Recovery",
    "System Volume Information",
    "$RECYCLE.BIN",
    "$SysReset",
    "$Windows.~BT",
    "$Windows.~WS",

    # Dev / virtual environments
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".eggs",

    # Build artifacts
    "dist",
    "build",
    ".next",
    "out",
    ".nuxt",

    # Temp / cache
    "Temp",
    "tmp",
    "temp",
    "cache",
    ".cache",

    # macOS
    ".DS_Store",
    ".Spotlight-V100",
    ".Trashes",
})

# ── Common folder definitions ─────────────────────────────────────────────────
#
# Each tuple: (display_name, home-relative path, active_by_default)
# active_by_default = False for potentially large folders.
#
_COMMON_FOLDER_DEFS: list[tuple[str, str, bool]] = [
    ("Desktop",   "Desktop",   True),
    ("Documents", "Documents", True),
    ("Downloads", "Downloads", True),
    ("Pictures",  "Pictures",  True),
    ("Videos",    "Videos",    False),   # Can be very large
    ("Music",     "Music",     False),   # Can be large
]


def discover_common_folders() -> list[dict]:
    """
    Returns common user folders that actually exist on this system.

    - Paths are normalized to forward slashes (POSIX style).
    - Only includes directories that exist and are accessible.
    - Uses Path.home() — never hardcodes a username.
    """
    home = Path.home()
    results: list[dict] = []

    for display_name, rel_path, is_active_default in _COMMON_FOLDER_DEFS:
        full_path = home / rel_path
        try:
            exists = full_path.exists() and full_path.is_dir()
        except (PermissionError, OSError):
            exists = False

        if exists:
            results.append({
                "name":              display_name,
                "path":              full_path.as_posix(),
                "is_active_default": is_active_default,
                "source_type":       "auto_common_folder",
            })

    log.debug("Discovered %d common folders", len(results))
    return results


def discover_drives() -> list[dict]:
    """
    Detects available local drive letters on Windows (A: → Z:).

    - All drives default to inactive (full drives = potentially huge).
    - Skips inaccessible or non-existent drive letters silently.
    - Returns empty list on non-Windows systems.
    """
    if os.name != "nt":
        log.debug("Drive discovery skipped (not Windows)")
        return []

    drives: list[dict] = []

    for letter in string.ascii_uppercase:
        drive = Path(f"{letter}:\\")
        try:
            if drive.exists():
                drives.append({
                    "name":              f"Local Disk {letter}:",
                    "path":              f"{letter}:/",
                    "is_active_default": False,   # Never index full drives by default
                    "source_type":       "auto_drive",
                })
        except (PermissionError, OSError):
            pass  # Skip inaccessible drives quietly

    log.debug("Discovered %d drives", len(drives))
    return drives


def discover_all() -> dict:
    """
    Run full discovery and return a combined result.
    Used by GET /folders/discover.
    """
    common = discover_common_folders()
    drives = discover_drives()

    log.info(
        "Discovery complete: %d common folders, %d drives",
        len(common), len(drives),
    )

    return {
        "common_folders": common,
        "drives":         drives,
    }
