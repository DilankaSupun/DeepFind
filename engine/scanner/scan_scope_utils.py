import logging
from database.repositories import ScanScopeRepository

log = logging.getLogger(__name__)

def is_path_allowed(path: str, exclusions: set[str] = None, roots: list[str] = None) -> bool:
    """
    Determines if a given file/folder path is allowed under the current scan scope.
    Rules:
    1. Must not fall under any system or user exclusion.
    2. Must fall under at least one effective scan root.
    """
    if not path:
        return False

    if exclusions is None:
        try:
            exclusions = ScanScopeRepository.get_excluded_path_strings()
        except Exception:
            exclusions = set()
            
    if roots is None:
        try:
            roots = ScanScopeRepository.get_effective_scan_roots()
        except Exception:
            roots = []

    norm = path.replace("\\", "/").lower().rstrip("/")

    # 1. Check exclusions (highest priority)
    for excl in exclusions:
        excl_norm = excl.replace("\\", "/").lower().rstrip("/")
        if norm == excl_norm or norm.startswith(excl_norm + "/"):
            return False

    # 2. Check roots
    # If no roots are configured at all, we technically can't allow anything,
    # but practically we might want to fail safe.
    if not roots:
        return False

    for root in roots:
        root_norm = root.replace("\\", "/").lower().rstrip("/")
        if norm == root_norm or norm.startswith(root_norm + "/"):
            return True

    return False

def filter_allowed_files(files: list[dict], path_key: str = "path") -> list[dict]:
    """
    Filters a list of file dictionaries, returning only those whose path is allowed.
    """
    exclusions = ScanScopeRepository.get_excluded_path_strings()
    roots = ScanScopeRepository.get_effective_scan_roots()
    
    return [f for f in files if is_path_allowed(f.get(path_key, ""), exclusions, roots)]
