import re

def normalize_path(path_str: str) -> str:
    """
    Normalizes a file or folder path to ensure uniqueness in the database.
    - Replaces backslashes with forward slashes
    - Removes duplicate slashes
    - Lowercases the path (since Windows is case-insensitive, this ensures d:/games and D:/Games map to the same DB row)
    - Removes trailing slashes (unless it's a drive root like 'd:/')
    """
    if not path_str:
        return ""
        
    # 1. Backslashes to forward slashes
    p = path_str.replace("\\", "/")
    
    # 2. Remove duplicate slashes
    p = re.sub(r'/+', '/', p)
    
    # 3. Lowercase
    p = p.lower()
    
    # 4. Strip trailing slash unless it's just "d:/"
    if p.endswith("/") and not (len(p) == 3 and p[1] == ':'):
        p = p.rstrip("/")
        
    return p
