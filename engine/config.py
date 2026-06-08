"""
DeepFind Engine — Configuration

Single source of truth for paths, limits, and defaults.
All other modules import from here — never hardcode paths elsewhere.
"""

from pathlib import Path

# ── Directory layout ───────────────────────────────────────────────────────────

# Root of the engine/ directory (where this file lives)
ENGINE_DIR = Path(__file__).parent

# data/ directory: holds the SQLite database and FAISS index
# Lives at engine/data/ — excluded from git via .gitignore
DATA_DIR = ENGINE_DIR / "data"

# SQLite database file
DB_PATH = DATA_DIR / "deepfind.db"

# FAISS vector index (created in Step 15 / V2)
FAISS_INDEX_PATH = DATA_DIR / "faiss.index"

# ── API server ─────────────────────────────────────────────────────────────────

API_HOST = "127.0.0.1"
API_PORT = 8765
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

