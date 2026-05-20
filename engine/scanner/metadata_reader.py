"""
DeepFind Engine — File Metadata Reader

Reads stat() metadata from a single file path.
No file content is read — metadata only.
Step 7: metadata collection only.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


def read_metadata(path: Path) -> dict | None:
    """
    Read file metadata via stat(). Returns None on any error.

    Fields returned:
      path, name, extension, size, created_at, modified_at
    """
    try:
        stat = path.stat()
        # On Windows st_ctime is creation time; on Linux it's metadata-change time
        return {
            "path":        path.as_posix(),
            "name":        path.name,
            "extension":   path.suffix.lower() if path.suffix else None,
            "size":        stat.st_size,
            "created_at":  _ts(stat.st_ctime),
            "modified_at": _ts(stat.st_mtime),
        }
    except (PermissionError, OSError, FileNotFoundError, ValueError):
        return None


def _ts(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
