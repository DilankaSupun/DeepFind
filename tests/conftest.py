"""
DeepFind — pytest conftest.py
=============================

Provides fixtures for isolated test database access.

IMPORTANT: No fixture in this file touches the production database at:
    engine/database/deepfind.db

All unit/integration test fixtures operate on a temporary in-memory or
temporary file SQLite database that is discarded after each test session.

Markers:
    live_db  — test requires a real, populated deepfind.db (excluded from default run)
    slow     — test is performance-sensitive and takes >1s (excluded from default run)

Usage:
    # Run isolated tests only (safe, fast):
    cd engine && python -m pytest -m "not live_db and not slow"

    # Run everything including live-DB tests:
    cd engine && python -m pytest

    # Run only live regression:
    cd engine && python -m pytest -m live_db
"""

import os
import sys
import sqlite3
import tempfile
import pytest

# ── Engine path bootstrap ──────────────────────────────────────────────────────
# tests/ lives one level above engine/ in the repo root.
# Add engine/ to sys.path so test files can import engine modules directly.
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "engine"))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def tmp_db_path(tmp_path_factory):
    """
    Create a temporary SQLite database for the test session.

    Uses the real schema.sql so the database structure is identical
    to production, but contains NO user data.

    Scope: session — one DB per pytest run (not per test), which is
    sufficient since unit tests never write persistent data.
    """
    schema_path = os.path.join(ENGINE_DIR, "database", "schema.sql")
    tmp_dir = tmp_path_factory.mktemp("deepfind_test_db")
    db_file = tmp_dir / "test_deepfind.db"

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    with open(schema_path, encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.close()
    return str(db_file)


@pytest.fixture(scope="session")
def tmp_db_conn(tmp_db_path):
    """
    Return a configured SQLite connection to the temporary test database.

    Scope: session — connection is shared per pytest run.
    Tests should NOT commit destructive changes; use transactions + rollback.
    """
    conn = sqlite3.connect(tmp_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    yield conn
    conn.close()
