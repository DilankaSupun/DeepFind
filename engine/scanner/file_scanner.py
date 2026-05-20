"""
DeepFind Engine — File System Scanner

Walks active indexing folders and yields file metadata dicts.
No file contents are read — metadata only (Step 7).

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
_EXTRA_SKIP = frozenset({
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData", "AppData", "Recovery",
    "System Volume Information", "$RECYCLE.BIN",
    "Temp", "temp", "cache", "Cache",
    ".mypy_cache", ".pytest_cache",
})

_ALL_SKIP = SKIP_DIRECTORIES | _EXTRA_SKIP


def scan_folder(
    folder_path: str,
    on_error: callable | None = None,
) -> Generator[dict, None, None]:
    """
    Walk *folder_path* recursively and yield file metadata dicts.

    Args:
        folder_path: absolute path string (forward slashes OK on Windows)
        on_error: optional callback(path, error) for logging skipped items

    Yields:
        dict from metadata_reader.read_metadata() — one per accessible file
    """
    root = Path(folder_path)

    if not root.exists():
        log.warning("Scan target does not exist: %s", folder_path)
        return
    if not root.is_dir():
        log.warning("Scan target is not a directory: %s", folder_path)
        return

    try:
        walker = os.walk(root, onerror=lambda e: _handle_walk_error(e, on_error))
    except (PermissionError, OSError) as exc:
        log.warning("Cannot walk %s: %s", folder_path, exc)
        return

    for dirpath, dirnames, filenames in walker:
        # Prune excluded directories in-place so os.walk won't descend into them
        dirnames[:] = [
            d for d in dirnames
            if d not in _ALL_SKIP
        ]

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
