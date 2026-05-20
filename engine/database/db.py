"""
DeepFind Engine — Database Connection & Initialization

Provides:
  init_db()        — create data dir + run schema.sql (idempotent)
  get_connection() — context manager yielding a configured SQLite connection
  get_db_info()    — returns DB path, size, and table list for /db/status
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path

from config import DATA_DIR, DB_PATH

log = logging.getLogger(__name__)

# Path to the schema SQL file (same directory as this file)
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    """
    Initialize the SQLite database.

    - Creates the data/ directory if it does not exist.
    - Reads and executes schema.sql (all DDL uses IF NOT EXISTS — safe to repeat).
    - Runs incremental column migrations for existing databases.
    - Called automatically on engine startup via FastAPI lifespan.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection() as conn:
        conn.executescript(schema_sql)

    _run_migrations()

    log.info("Database initialized at: %s", DB_PATH)


def _run_migrations() -> None:
    """
    Apply incremental schema changes to existing databases.
    Each migration checks whether the change is needed before applying it,
    so this is safe to call on both fresh and pre-existing databases.
    """
    with get_connection() as conn:
        existing_cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(indexed_folders)").fetchall()
        }

        # Step 6: add source_type to indexed_folders
        if "source_type" not in existing_cols:
            conn.execute(
                "ALTER TABLE indexed_folders "
                "ADD COLUMN source_type TEXT DEFAULT 'manual'"
            )
            log.info("Migration applied: added source_type to indexed_folders")


@contextmanager
def get_connection():
    """
    Context manager for SQLite connections.

    Configuration:
      - WAL journal mode  → better concurrent read performance
      - Foreign keys ON   → enforce referential integrity
      - Row factory       → access columns by name (conn.row_factory)
      - Auto-commit on success, auto-rollback on exception

    Usage:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM files").fetchall()
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row        # Access cols by name: row["name"]
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-20000")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_info() -> dict:
    """
    Returns database metadata for the /db/status endpoint.

    Returns dict with:
      connected     — bool
      path          — absolute path to the .db file
      size_bytes    — file size on disk
      tables        — list of table names
      tables_ok     — True if all required tables exist
    """
    required = {
        "files", "indexed_folders", "files_fts",
        "file_chunks", "embeddings", "search_history", "settings",
    }

    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'shadow') "
                "ORDER BY name"
            ).fetchall()
            existing = {row["name"] for row in rows}

        size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

        return {
            "connected":   True,
            "path":        str(DB_PATH),
            "size_bytes":  size,
            "tables":      sorted(existing),
            "tables_ok":   required.issubset(existing),
        }

    except Exception as exc:
        log.error("DB info check failed: %s", exc)
        return {
            "connected":  False,
            "path":       str(DB_PATH),
            "size_bytes": 0,
            "tables":     [],
            "tables_ok":  False,
        }
