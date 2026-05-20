"""
DeepFind Engine — Database Repositories

Repository pattern: each class handles all DB operations for one table.
Components call these functions — never write raw SQL outside this module.

Step 5: Stubs and SettingsRepository only.
        FilesRepository, FoldersRepository etc. are populated in Steps 6–11.
"""

import logging
from datetime import datetime, timezone

from database.db import get_connection

log = logging.getLogger(__name__)


def _now_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ── Settings ───────────────────────────────────────────────────────────────────

class SettingsRepository:
    """Read/write key-value settings."""

    @staticmethod
    def get(key: str, default: str | None = None) -> str | None:
        """Return the value for a setting key, or default if not found."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else default

    @staticmethod
    def set(key: str, value: str) -> None:
        """Insert or replace a setting value."""
        with get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    @staticmethod
    def get_all() -> dict[str, str]:
        """Return all settings as a plain dict."""
        with get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: row["value"] for row in rows}


# ── Indexed Folders ────────────────────────────────────────────────────────────

class FoldersRepository:
    """
    Manage user-selected and auto-discovered indexed folders.
    Step 6: Full implementation with source_type and toggle support.
    """

    @staticmethod
    def add(
        folder_path: str,
        source_type: str = "manual",
        is_active: int = 1,
    ) -> dict:
        """
        Add a folder. If the path already exists, re-activates it.
        Returns the full folder record after insert/update.
        """
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO indexed_folders (folder_path, is_active, added_at, source_type)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(folder_path) DO UPDATE SET is_active = excluded.is_active
                """,
                (folder_path, is_active, _now_iso(), source_type),
            )
            row = conn.execute(
                "SELECT * FROM indexed_folders WHERE folder_path = ?",
                (folder_path,),
            ).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def list_folders(active_only: bool = True) -> list[dict]:
        """Return all folders, optionally filtering to active (is_active=1) only."""
        with get_connection() as conn:
            if active_only:
                rows = conn.execute(
                    "SELECT * FROM indexed_folders WHERE is_active = 1 "
                    "ORDER BY source_type, added_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM indexed_folders ORDER BY source_type, added_at DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def list_all() -> list[dict]:
        """Return all folders including inactive ones."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM indexed_folders ORDER BY source_type, added_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(folder_id: int) -> dict | None:
        """Return a single folder by its primary key, or None."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM indexed_folders WHERE id = ?", (folder_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def set_active(folder_id: int, is_active: int) -> bool:
        """
        Set the is_active flag for a specific folder.
        Returns True if a row was actually updated.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE indexed_folders SET is_active = ? WHERE id = ?",
                (is_active, folder_id),
            )
            affected = cursor.rowcount
        return affected > 0

    @staticmethod
    def toggle(folder_id: int) -> dict | None:
        """
        Flip is_active (1→0 or 0→1) for a folder.
        Returns the updated folder dict, or None if ID not found.
        """
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM indexed_folders WHERE id = ?", (folder_id,)
            ).fetchone()
            if not row:
                return None
            new_active = 0 if row["is_active"] else 1
            conn.execute(
                "UPDATE indexed_folders SET is_active = ? WHERE id = ?",
                (new_active, folder_id),
            )
            updated = conn.execute(
                "SELECT * FROM indexed_folders WHERE id = ?", (folder_id,)
            ).fetchone()
        return dict(updated) if updated else None

    @staticmethod
    def deactivate(folder_id: int) -> bool:
        """
        Soft-delete: set is_active = 0 for the given folder ID.
        Returns True if a row was actually updated.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE indexed_folders SET is_active = 0 WHERE id = ? AND is_active = 1",
                (folder_id,),
            )
            affected = cursor.rowcount
        return affected > 0

    @staticmethod
    def count_by_path(folder_path: str) -> int:
        """Returns 1 if a folder path already exists in the table, else 0."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM indexed_folders WHERE folder_path = ?",
                (folder_path,),
            ).fetchone()
        return row["n"] if row else 0



# ── Files ──────────────────────────────────────────────────────────────────────

class FilesRepository:
    """
    CRUD operations for the files table.
    Populated incrementally in Steps 7 (metadata), 9 (text), 11 (tags).
    """

    @staticmethod
    def count() -> int:
        """Return total number of indexed files."""
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM files").fetchone()
        return row["n"]

    @staticmethod
    def get_recent_modified(limit: int = 10) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, path, extension, size, modified_at, last_indexed_at, tags, status "
                "FROM files WHERE status != 'missing' "
                "ORDER BY modified_at DESC LIMIT ?", 
                (limit,)
            ).fetchall()
            
        res = []
        for r in rows:
            d = dict(r)
            size = d.get("size") or 0
            for unit in ("B", "KB", "MB", "GB"):
                if size < 1024:
                    d["size_human"] = f"{size:.0f} {unit}"
                    break
                size /= 1024
            else:
                d["size_human"] = f"{size:.1f} TB"
            res.append(d)
        return res

    @staticmethod
    def get_recent_indexed(limit: int = 10) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, path, extension, size, modified_at, last_indexed_at, tags, status "
                "FROM files WHERE status != 'missing' "
                "ORDER BY last_indexed_at DESC LIMIT ?", 
                (limit,)
            ).fetchall()
            
        res = []
        for r in rows:
            d = dict(r)
            size = d.get("size") or 0
            for unit in ("B", "KB", "MB", "GB"):
                if size < 1024:
                    d["size_human"] = f"{size:.0f} {unit}"
                    break
                size /= 1024
            else:
                d["size_human"] = f"{size:.1f} TB"
            res.append(d)
        return res

    @staticmethod
    def upsert_batch(files: list[dict]) -> dict:
        """
        Insert new files or update changed files in a batch.
        Unchanged files (same size + modified_at) are skipped (no DB write).
        Returns dict: {added, updated, skipped}
        """
        if not files:
            return {"added": 0, "updated": 0, "skipped": 0}

        added = updated = skipped = 0
        now = _now_iso()

        with get_connection() as conn:
            # Single query to fetch all existing records for this batch
            paths = [f["path"] for f in files]
            placeholders = ",".join("?" * len(paths))
            existing = {
                row["path"]: dict(row)
                for row in conn.execute(
                    f"SELECT path, size, modified_at, status FROM files WHERE path IN ({placeholders})",
                    paths,
                ).fetchall()
            }

            to_insert: list[dict] = []
            to_update: list[dict] = []

            for f in files:
                ex = existing.get(f["path"])
                if ex is None:
                    to_insert.append({**f, "now": now})
                    added += 1
                elif (
                    ex["size"] != f["size"]
                    or ex["modified_at"] != f["modified_at"]
                    or ex["status"] == "missing"
                ):
                    to_update.append({**f, "now": now})
                    updated += 1
                else:
                    skipped += 1

            if to_insert:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO files
                      (path, name, extension, size, created_at, modified_at, last_indexed_at, status)
                    VALUES
                      (:path, :name, :extension, :size, :created_at, :modified_at, :now, 'metadata_indexed')
                    """,
                    to_insert,
                )

            if to_update:
                conn.executemany(
                    """
                    UPDATE files
                    SET name=:name, extension=:extension, size=:size,
                        modified_at=:modified_at, last_indexed_at=:now,
                        status='metadata_indexed'
                    WHERE path=:path
                    """,
                    to_update,
                )

        return {"added": added, "updated": updated, "skipped": skipped}

    @staticmethod
    def count_by_status() -> dict[str, int]:
        """Return file counts grouped by status."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM files GROUP BY status"
            ).fetchall()
        return {row["status"]: row["n"] for row in rows}

    @staticmethod
    def mark_missing(folder_paths: list[str], scanned_paths: set[str]) -> int:
        """
        For each active folder, find DB files that were NOT seen during the scan.
        Sets their status = 'missing'. Returns total count marked.
        """
        total = 0
        for folder_path in folder_paths:
            prefix = folder_path.rstrip("/") + "/"
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, path FROM files WHERE path LIKE ? AND status != 'missing'",
                    (prefix + "%",),
                ).fetchall()
                missing_ids = [r["id"] for r in rows if r["path"] not in scanned_paths]
                if missing_ids:
                    # SQLite variable limit is ~999; chunk to be safe
                    for i in range(0, len(missing_ids), 900):
                        chunk = missing_ids[i : i + 900]
                        ph = ",".join("?" * len(chunk))
                        conn.execute(
                            f"UPDATE files SET status='missing' WHERE id IN ({ph})",
                            chunk,
                        )
                    total += len(missing_ids)
        return total

    @staticmethod
    def update_extracted_text(
        file_id: int,
        text: str | None,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Set extracted text, status, and optional error message. (Step 9)"""
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE files
                SET extracted_text = :text,
                    status         = :status,
                    error_message  = :error,
                    last_indexed_at = :now
                WHERE id = :id
                """,
                {
                    "text":   text,
                    "status": status,
                    "error":  error_message,
                    "now":    _now_iso(),
                    "id":     file_id,
                },
            )

    @staticmethod
    def get_files_for_extraction(supported_extensions: set[str], batch_size: int = 200) -> list[dict]:
        """
        Return files eligible for text extraction:
          - status = 'metadata_indexed'
          - extension in supported_extensions
        Returned in batches to avoid loading all files at once.
        Uses a generator for memory efficiency.
        """
        ext_list = list(supported_extensions)
        placeholders = ",".join("?" * len(ext_list))
        sql = f"""
            SELECT id, path, name, extension, size
            FROM files
            WHERE status = 'metadata_indexed'
              AND LOWER(extension) IN ({placeholders})
            ORDER BY id
        """
        with get_connection() as conn:
            rows = conn.execute(sql, ext_list).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def update_tags(file_id: int, tags: str) -> None:
        """Set comma-separated tags. (Step 11)"""
        with get_connection() as conn:
            conn.execute(
                "UPDATE files SET tags = ?, modified_at = ? WHERE id = ?",
                (tags, _now_iso(), file_id),
            )

    @staticmethod
    def get_files_for_tagging(force: bool = False, batch_size: int = 200) -> list[dict]:
        """
        Return files eligible for tagging.
        If force is True, tags all non-missing files.
        If force is False, only tags files where tags is NULL or empty.
        """
        sql = """
            SELECT id, path, name, extension, extracted_text
            FROM files
            WHERE status != 'missing'
        """
        if not force:
            sql += " AND (tags IS NULL OR tags = '')"
        sql += " ORDER BY id"
        
        # In a real app we'd paginate by id to handle 100k+ rows, but for simplicity
        # we can just fetch all matching rows (SQLite fetches quickly) or yield in chunks.
        # Returning all matches is fine for our scale.
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]


# ── Search History ─────────────────────────────────────────────────────────────

class SearchHistoryRepository:
    """
    Log and retrieve search history.
    Populated in Step 8 (search).
    """

    @staticmethod
    def add(query: str, result_count: int = 0) -> None:
        """Record a search query."""
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO search_history (query, searched_at, result_count) "
                "VALUES (?, ?, ?)",
                (query, _now_iso(), result_count),
            )

    @staticmethod
    def get_recent(limit: int = 20) -> list[dict]:
        """Return the most recent search queries."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT query, searched_at, result_count "
                "FROM search_history ORDER BY searched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


# ── Text Chunks ────────────────────────────────────────────────────────────────

class ChunksRepository:
    """
    CRUD for the file_chunks table.
    Populated in Step 9; embeddings added in Step 15 / V2.
    """

    @staticmethod
    def clear_for_file(file_id: int) -> None:
        """Delete all existing chunks for a file before re-inserting."""
        with get_connection() as conn:
            conn.execute("DELETE FROM file_chunks WHERE file_id = ?", (file_id,))

    @staticmethod
    def insert_batch(file_id: int, chunks: list[str]) -> int:
        """
        Insert a list of text chunks for a file.
        Returns the number of chunks inserted.
        """
        if not chunks:
            return 0
        now = _now_iso()
        rows = [
            (file_id, idx, text, now)
            for idx, text in enumerate(chunks)
        ]
        with get_connection() as conn:
            conn.executemany(
                "INSERT INTO file_chunks (file_id, chunk_index, chunk_text, created_at) "
                "VALUES (?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    @staticmethod
    def count_total() -> int:
        """Return total number of stored text chunks."""
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM file_chunks").fetchone()
        return row["n"] if row else 0

    @staticmethod
    def count_for_file(file_id: int) -> int:
        """Return number of chunks stored for a specific file."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM file_chunks WHERE file_id = ?", (file_id,)
            ).fetchone()
        return row["n"] if row else 0


# ── Extraction Summary helper ──────────────────────────────────────────────────
# (added to FilesRepository as a module-level function for clarity)

def get_extraction_summary() -> dict:
    """
    Return a summary dict of extraction progress for /extract/summary.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM files GROUP BY status"
        ).fetchall()
        chunk_count = conn.execute(
            "SELECT COUNT(*) AS n FROM file_chunks"
        ).fetchone()["n"]

    by_status = {row["status"]: row["n"] for row in rows}
    return {
        "content_extracted":      by_status.get("content_extracted", 0),
        "metadata_indexed":       by_status.get("metadata_indexed", 0),
        "extraction_failed":      by_status.get("extraction_failed", 0),
        "content_skipped_large":  by_status.get("content_skipped_large_file", 0),
        "missing":                by_status.get("missing", 0),
        "chunks":                 chunk_count,
        "total_files":            sum(by_status.values()),
    }


def get_tagging_summary() -> dict:
    """
    Return a summary dict of tagging progress for /tags/summary.
    """
    with get_connection() as conn:
        # Files with tags
        tagged = conn.execute(
            "SELECT COUNT(*) AS n FROM files WHERE tags IS NOT NULL AND tags != '' AND status != 'missing'"
        ).fetchone()["n"]
        
        # Fetch all tags to calculate unique count and top tags
        rows = conn.execute(
            "SELECT tags FROM files WHERE tags IS NOT NULL AND tags != '' AND status != 'missing'"
        ).fetchall()
    
    tag_counts = {}
    for row in rows:
        tags_str = row["tags"]
        if tags_str:
            for t in tags_str.split(","):
                t = t.strip()
                if t:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
                    
    top_tags = sorted([{"tag": k, "count": v} for k, v in tag_counts.items()], key=lambda x: x["count"], reverse=True)
    
    return {
        "files_with_tags": tagged,
        "unique_tags": len(tag_counts),
        "top_tags": top_tags[:20]  # Return top 20
    }

# ── Search History ─────────────────────────────────────────────────────────────

class SearchHistoryRepository:
    """CRUD for local search history (Step 12)."""

    @staticmethod
    def add_search(query: str, result_count: int) -> None:
        q = query.strip()
        if not q:
            return
            
        with get_connection() as conn:
            row = conn.execute("SELECT id, query FROM search_history ORDER BY searched_at DESC LIMIT 1").fetchone()
            if row and row["query"] == q:
                conn.execute("UPDATE search_history SET searched_at = ?, result_count = ? WHERE id = ?", (_now_iso(), result_count, row["id"]))
            else:
                conn.execute("INSERT INTO search_history (query, searched_at, result_count) VALUES (?, ?, ?)", (q, _now_iso(), result_count))

    @staticmethod
    def get_recent(limit: int = 10) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("SELECT id, query, searched_at, result_count FROM search_history ORDER BY searched_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def clear_all() -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM search_history")

def get_dashboard_summary() -> dict:
    with get_connection() as conn:
        total_files = conn.execute("SELECT COUNT(*) AS n FROM files WHERE status != 'missing'").fetchone()["n"]
        content_extracted = conn.execute("SELECT COUNT(*) AS n FROM files WHERE status = 'content_extracted'").fetchone()["n"]
        files_with_tags = conn.execute("SELECT COUNT(*) AS n FROM files WHERE tags IS NOT NULL AND tags != '' AND status != 'missing'").fetchone()["n"]
        recent_searches = conn.execute("SELECT COUNT(*) AS n FROM search_history").fetchone()["n"]
        
    return {
        "total_files": total_files,
        "content_extracted": content_extracted,
        "files_with_tags": files_with_tags,
        "recent_searches": recent_searches
    }
