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
            
        # Step 19.5: Path normalization migration
        # We need to normalize all paths in the DB to avoid case-sensitivity duplicates
        # Since it might violate UNIQUE constraint if duplicates already exist, we do it safely:
        from scanner.path_utils import normalize_path
        
        # 1. scan_scope table
        scope_rows = conn.execute("SELECT id, path FROM scan_scope").fetchall()
        for r in scope_rows:
            norm = normalize_path(r["path"])
            if norm != r["path"]:
                try:
                    conn.execute("UPDATE scan_scope SET path = ? WHERE id = ?", (norm, r["id"]))
                except sqlite3.IntegrityError:
                    # Duplicate exists, delete the unnormalized one
                    conn.execute("DELETE FROM scan_scope WHERE id = ?", (r["id"],))

        # 2. indexed_folders
        folder_rows = conn.execute("SELECT id, folder_path FROM indexed_folders").fetchall()
        for r in folder_rows:
            norm = normalize_path(r["folder_path"])
            if norm != r["folder_path"]:
                try:
                    conn.execute("UPDATE indexed_folders SET folder_path = ? WHERE id = ?", (norm, r["id"]))
                except sqlite3.IntegrityError:
                    conn.execute("DELETE FROM indexed_folders WHERE id = ?", (r["id"],))

        # 3. files table
        # Only normalize files if they have uppercase characters or backslashes
        file_rows = conn.execute("SELECT id, path FROM files WHERE path GLOB '*[A-Z\\\\]*'").fetchall()
        for r in file_rows:
            norm = normalize_path(r["path"])
            try:
                conn.execute("UPDATE files SET path = ? WHERE id = ?", (norm, r["id"]))
            except sqlite3.IntegrityError:
                # If the normalized path already exists, delete this duplicate row
                conn.execute("DELETE FROM files WHERE id = ?", (r["id"],))
            log.info("Migration applied: path normalization")

        # Step 20: Clean up FTS pollution
        # Rebuild files_fts so it only contains rows with actual extracted_text
        # We check if there are any polluted rows first to avoid rebuilding every startup
        polluted = conn.execute(
            "SELECT COUNT(*) as c FROM files_fts WHERE extracted_text IS NULL OR extracted_text = ''"
        ).fetchone()
        
        if polluted and polluted["c"] > 0:
            log.info(f"FTS migration: Found {polluted['c']} polluted rows. Rebuilding files_fts...")
            # Drop old triggers before deleting from files_fts, otherwise delete triggers might fire incorrectly
            conn.execute("DROP TRIGGER IF EXISTS files_ai")
            conn.execute("DROP TRIGGER IF EXISTS files_ad")
            conn.execute("DROP TRIGGER IF EXISTS files_au")
            
            # Drop the virtual table completely to fix any "database disk image is malformed" FTS5 corruption
            conn.execute("DROP TABLE IF EXISTS files_fts")
            
            # Recreate the FTS table
            conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                    name,
                    path,
                    extracted_text,
                    tags,
                    content     = 'files',
                    content_rowid = 'id',
                    tokenize    = 'porter ascii'
                );
            """)
            
            conn.execute("""
                INSERT INTO files_fts(rowid, name, path, extracted_text, tags)
                SELECT id, name, path, extracted_text, tags
                FROM files
                WHERE status != 'missing'
                  AND extracted_text IS NOT NULL 
                  AND extracted_text != ''
            """)
            
            # Recreate triggers with the new WHEN conditions
            conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS files_ai
                AFTER INSERT ON files 
                WHEN new.extracted_text IS NOT NULL AND new.extracted_text != ''
                BEGIN
                    INSERT INTO files_fts(rowid, name, path, extracted_text, tags)
                    VALUES (new.id, new.name, new.path, new.extracted_text, new.tags);
                END;

                CREATE TRIGGER IF NOT EXISTS files_ad
                AFTER DELETE ON files 
                WHEN old.extracted_text IS NOT NULL AND old.extracted_text != ''
                BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, path, extracted_text, tags)
                    VALUES ('delete', old.id, old.name, old.path, old.extracted_text, old.tags);
                END;

                CREATE TRIGGER IF NOT EXISTS files_au
                AFTER UPDATE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, path, extracted_text, tags)
                    SELECT 'delete', old.id, old.name, old.path, old.extracted_text, old.tags
                    WHERE old.extracted_text IS NOT NULL AND old.extracted_text != '';
                    
                    INSERT INTO files_fts(rowid, name, path, extracted_text, tags)
                    SELECT new.id, new.name, new.path, new.extracted_text, new.tags
                    WHERE new.extracted_text IS NOT NULL AND new.extracted_text != '';
                END;
            """)
            log.info("FTS migration complete.")

        # Step 19: ensure scan_scope table exists on existing databases
        # schema.sql already has IF NOT EXISTS, but older DBs that started
        # before this step need the table created via the migration path.
        existing_tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "scan_scope" not in existing_tables:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scan_scope (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    path        TEXT    UNIQUE NOT NULL,
                    scan_mode   TEXT    NOT NULL,
                    source_type TEXT    DEFAULT 'user',
                    is_enabled  INTEGER DEFAULT 1,
                    added_at    TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_scan_scope_scan_mode
                    ON scan_scope(scan_mode);
                CREATE INDEX IF NOT EXISTS idx_scan_scope_is_enabled
                    ON scan_scope(is_enabled);
            """)
            log.info("Migration applied: created scan_scope table")



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
        "scan_scope",
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
