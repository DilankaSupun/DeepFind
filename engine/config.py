"""
DeepFind Engine — Configuration

Single source of truth for paths, limits, and defaults.
All other modules import from here — never hardcode paths elsewhere.

Packaging note (Step 21):
  In development, DATA_DIR lives inside engine/ which is always writable.
  After PyInstaller bundling, ENGINE_DIR points INSIDE the frozen .exe bundle
  (read-only). DATA_DIR must be redirected to a writable user-data directory.

  Future packaging change:
    import sys, os
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        _appdata = os.environ.get('DEEPFIND_DATA_DIR') or os.path.expanduser('~')
        DATA_DIR = Path(_appdata) / 'AppData' / 'Roaming' / 'DeepFind' / 'data'
    else:
        DATA_DIR = ENGINE_DIR / 'data'

  The Electron backend-manager (Step 21) will pass DEEPFIND_DATA_DIR as an
  environment variable when launching the bundled engine executable.
"""

import os
import sys
from pathlib import Path

# ── Directory layout ───────────────────────────────────────────────────────────

IS_PACKAGED = getattr(sys, 'frozen', False)

# Root of the engine/ directory (where this file lives)
ENGINE_DIR = Path(__file__).parent

# Resolving writable user data directory
if IS_PACKAGED:
    _appdata = os.environ.get('DEEPFIND_USER_DATA_DIR') or os.path.expanduser('~')
    USER_DATA_DIR = Path(_appdata)
    DATA_DIR = USER_DATA_DIR / "data"
    LOG_DIR = USER_DATA_DIR / "logs"
else:
    USER_DATA_DIR = ENGINE_DIR
    DATA_DIR = ENGINE_DIR / "data"
    LOG_DIR = DATA_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Resolving the semantic model directory
_env_model = os.environ.get('DEEPFIND_MODEL_DIR')
if _env_model:
    MODEL_DIR = Path(_env_model)
else:
    MODEL_DIR = ENGINE_DIR / "bundled_models" / "all-MiniLM-L6-v2"

# SQLite database file
DB_PATH = DATA_DIR / "deepfind.db"

# FAISS vector index (created in Step 15 / V2)
FAISS_INDEX_PATH = DATA_DIR / "faiss.index"

# ── API server ─────────────────────────────────────────────────────────────────

API_HOST = "127.0.0.1"
API_PORT = int(os.environ.get("DEEPFIND_PORT", 8765))
APP_VERSION = "0.1.0"

# ── Indexing limits (resource-friendly defaults) ───────────────────────────────

# Skip text extraction for files larger than this
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024   # 25 MB

# Maximum characters of extracted text to embed
MAX_EMBED_CHARS = 20_000

# Maximum text chunks per file for embedding
MAX_CHUNKS_PER_FILE = 20

# Target chunk size in words
CHUNK_SIZE_WORDS = 400

# Embedding batch size (chunks processed at once)
EMBED_BATCH_SIZE = 32

# ── File type filters ──────────────────────────────────────────────────────────

# Extensions supported for text extraction (Step 9)
SUPPORTED_TEXT_EXTENSIONS = {
    # Plain text / documents
    ".txt", ".md", ".csv", ".json", ".xml",
    # Code files
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".php", ".java", ".html", ".css", ".sql",
    ".c", ".cpp", ".cs", ".go", ".rs",
    # Document formats
    ".pdf", ".docx",
}

# Directories to always skip during scanning (matched by directory NAME, not path)
SKIP_DIRECTORIES = {
    # Windows system directories (name match)
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
}

# ── Scan Scope defaults ────────────────────────────────────────────────────────
#
# Automatic scanning is ON by default.
# Full drives are not auto-scanned — only common user folders are.
AUTO_SCAN_ENABLED = True

# System-level path exclusions (matched by path prefix, not just directory name).
# These are seeded into the scan_scope table on first run and after full reset.
# Paths use forward slashes. Drive letter is uppercase.
SYSTEM_EXCLUDED_PATHS: list[str] = [
    "C:/Windows",
    "C:/Program Files",
    "C:/Program Files (x86)",
    "C:/ProgramData",
    "C:/Recovery",
    "C:/System Volume Information",
    "C:/$RECYCLE.BIN",
]

if IS_PACKAGED:
    # Exclude the backend distribution directory (where this file is located)
    SYSTEM_EXCLUDED_PATHS.append(ENGINE_DIR.as_posix())
    # Exclude the user data directory where DB/logs reside
    SYSTEM_EXCLUDED_PATHS.append(USER_DATA_DIR.as_posix())
else:
    # In development mode, don't exclude the entire source tree
    # Instead, exclude specific runtime or generated directories
    SYSTEM_EXCLUDED_PATHS.extend([
        DATA_DIR.as_posix(),
        LOG_DIR.as_posix(),
        MODEL_DIR.as_posix(),
        (ENGINE_DIR / ".venv").as_posix(),
        (ENGINE_DIR / "build").as_posix(),
        (ENGINE_DIR / "dist").as_posix(),
    ])

