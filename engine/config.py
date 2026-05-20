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

# Directories to always skip during scanning
SKIP_DIRECTORIES = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".idea", ".vscode", "dist", "build", ".next", "out",
    "$RECYCLE.BIN", "System Volume Information",
}
