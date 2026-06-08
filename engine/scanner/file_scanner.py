"""
DeepFind Engine — File System Scanner

Walks active indexing folders and yields file metadata dicts.
No file contents are read — metadata only (Step 7).

Step 19: Accepts excluded_paths set. Prunes both directory-name exclusions
         (SKIP_DIRECTORIES) and absolute-path-prefix exclusions (scan_scope rules).

Key design decisions:
  - os.walk with in-place dirnames pruning for efficient directory exclusion
  - Generator pattern: yields one file at a time (constant memory usage)
  - Errors on individual files/dirs are caught and counted, never raise
"""

import os
import logging
from pathlib import Path
from typing import Generator

from config import SKIP_DIRECTORIES
from scanner.metadata_reader import read_metadata

log = logging.getLogger(__name__)

# Additional dir-name exclusions beyond config (Windows system dirs)
_EXTRA_SKIP: frozenset[str] = frozenset({
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData", "AppData", "Recovery",
    "System Volume Information", "$RECYCLE.BIN",
    "Temp", "temp", "cache", "Cache",
    ".mypy_cache", ".pytest_cache",
})

_ALL_SKIP: frozenset[str] = SKIP_DIRECTORIES | _EXTRA_SKIP


def _is_excluded_by_path(abs_path: str, excluded_paths: set[str]) -> bool:
    """
    Returns True if abs_path starts with any excluded path prefix.
    Comparison is done with forward slashes, case-insensitive on Windows.
    """
    if not excluded_paths:
        return False
    norm = abs_path.replace("\\", "/")
    norm_lower = norm.lower()
    for excl in excluded_paths:
        excl_lower = excl.lower().rstrip("/")
        if norm_lower == excl_lower or norm_lower.startswith(excl_lower + "/"):
            return True
    return False


def scan_folder(
    folder_path: str,
    on_error: callable | None = None,
    excluded_paths: set[str] | None = None,
    stats: dict | None = None
) -> Generator[dict, None, None]:
    """
    Walk *folder_path* recursively and yield file metadata dicts.

    Args:
        folder_path:    Absolute path string (forward slashes OK on Windows).
        on_error:       Optional callback(path, error) for logging skipped items.
        excluded_paths: Set of absolute path strings to skip (from scan_scope rules).
                        Matched by prefix — subpaths are also excluded.
        stats:          Optional dict to track scan statistics.

    Yields:
        dict from metadata_reader.read_metadata() — one per accessible file.
    """
    _excluded = excluded_paths or set()
    root = Path(folder_path)

    if not root.exists():
        log.warning("Scan target does not exist: %s", folder_path)
        return
    if not root.is_dir():
        log.warning("Scan target is not a directory: %s", folder_path)
        return

    # Skip scanning if the root itself is excluded
    if _is_excluded_by_path(str(root), _excluded):
        log.info("Scan root excluded by scope rule: %s", folder_path)
        return

    try:
        walker = os.walk(root, onerror=lambda e: _handle_walk_error(e, on_error))
    except (PermissionError, OSError) as exc:
        log.warning("Cannot walk %s: %s", folder_path, exc)
        return
        
    root_depth = len(root.parts)

    for dirpath, dirnames, filenames in walker:
        abs_dirpath = str(Path(dirpath)).replace("\\", "/")
        
        if stats is not None:
            stats["scanned_folders"] += 1
            current_depth = len(Path(dirpath).parts) - root_depth
            if current_depth > stats["max_depth_reached"]:
                stats["max_depth_reached"] = current_depth

        # Prune 1: skip by directory NAME (fast set lookup)
        original_dirnames = set(dirnames)
        dirnames[:] = [
            d for d in dirnames
            if d not in _ALL_SKIP
        ]
        if stats is not None:
            stats["skipped_folders"] += len(original_dirnames) - len(dirnames)

        # Prune 2: skip by absolute PATH prefix (scan_scope exclusions)
        if _excluded:
            original_dirnames = set(dirnames)
            dirnames[:] = [
                d for d in dirnames
                if not _is_excluded_by_path(abs_dirpath + "/" + d, _excluded)
            ]
            if stats is not None:
                stats["excluded_folders"] += len(original_dirnames) - len(dirnames)

        for filename in filenames:
            file_path = Path(dirpath) / filename
            try:
                meta = read_metadata(file_path)
                if meta:
                    yield meta
            except Exception as exc:
                if on_error:
                    on_error(str(file_path), exc)
                log.debug("Skipped file %s: %s", file_path, exc)


def _handle_walk_error(err: OSError, on_error: callable | None) -> None:
    log.debug("Walk error in %s: %s", err.filename, err)
    if on_error:
        on_error(str(err.filename), err)
