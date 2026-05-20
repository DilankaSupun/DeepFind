-- ============================================================
-- DeepFind Engine — SQLite Database Schema
-- ============================================================
-- Execution: run once at backend startup via db.init_db()
-- All tables use IF NOT EXISTS — safe to call repeatedly.
-- ============================================================


-- ── 1. files ──────────────────────────────────────────────
-- Stores metadata for every indexed file.
-- extracted_text and tags are populated in later stages.

CREATE TABLE IF NOT EXISTS files (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    path             TEXT    UNIQUE NOT NULL,   -- Absolute file path
    name             TEXT    NOT NULL,          -- Filename only (no directory)
    extension        TEXT,                      -- e.g. ".pdf", ".py"
    size             INTEGER,                   -- Bytes
    created_at       TEXT,                      -- ISO-8601 UTC
    modified_at      TEXT,                      -- ISO-8601 UTC
    last_indexed_at  TEXT,                      -- ISO-8601 UTC
    content_hash     TEXT,                      -- SHA-256 for change detection
    extracted_text   TEXT,                      -- Plain text content (Step 9)
    tags             TEXT,                      -- Comma-separated tags (Step 11)
    summary          TEXT,                      -- Short AI summary (future)
    status           TEXT    DEFAULT 'metadata_indexed',
                                               -- metadata_indexed | text_extracted
                                               -- tagged | embedded | error
    error_message    TEXT                       -- Set when status = 'error'
);

CREATE INDEX IF NOT EXISTS idx_files_extension   ON files(extension);
CREATE INDEX IF NOT EXISTS idx_files_status      ON files(status);
CREATE INDEX IF NOT EXISTS idx_files_modified_at ON files(modified_at);
CREATE INDEX IF NOT EXISTS idx_files_name        ON files(name);
CREATE INDEX IF NOT EXISTS idx_files_path        ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_last_indexed_at ON files(last_indexed_at);
CREATE INDEX IF NOT EXISTS idx_files_tags        ON files(tags);


-- ── 2. indexed_folders ────────────────────────────────────
-- Stores folders that the user has selected for indexing.

CREATE TABLE IF NOT EXISTS indexed_folders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path     TEXT    UNIQUE NOT NULL,
    is_active       INTEGER DEFAULT 1,        -- 1 = active, 0 = paused
    added_at        TEXT,                     -- ISO-8601 UTC
    last_scanned_at TEXT                      -- ISO-8601 UTC
);


-- ── 3. files_fts (FTS5 full-text search) ─────────────────
-- Virtual table for fast keyword search over file content.
-- Uses content= to reference the files table (no data duplication).
-- Synced automatically via the triggers below.

CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    name,
    path,
    extracted_text,
    tags,
    content     = 'files',    -- Source table
    content_rowid = 'id',     -- Row ID column in source table
    tokenize    = 'porter ascii'
);

-- Trigger: keep FTS in sync on INSERT
CREATE TRIGGER IF NOT EXISTS files_ai
AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, name, path, extracted_text, tags)
    VALUES (new.id, new.name, new.path, new.extracted_text, new.tags);
END;

-- Trigger: keep FTS in sync on DELETE
CREATE TRIGGER IF NOT EXISTS files_ad
AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, name, path, extracted_text, tags)
    VALUES ('delete', old.id, old.name, old.path, old.extracted_text, old.tags);
END;

-- Trigger: keep FTS in sync on UPDATE
CREATE TRIGGER IF NOT EXISTS files_au
AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, name, path, extracted_text, tags)
    VALUES ('delete', old.id, old.name, old.path, old.extracted_text, old.tags);
    INSERT INTO files_fts(rowid, name, path, extracted_text, tags)
    VALUES (new.id, new.name, new.path, new.extracted_text, new.tags);
END;


-- ── 4. file_chunks ────────────────────────────────────────
-- Stores text chunks for semantic embedding (V2 / Step 15).
-- Large documents are split into chunks before embedding.

CREATE TABLE IF NOT EXISTS file_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     INTEGER NOT NULL,
    chunk_index INTEGER,          -- Position within the file (0-based)
    chunk_text  TEXT,             -- The actual chunk text
    vector_id   INTEGER,          -- Corresponding FAISS vector index position
    created_at  TEXT,             -- ISO-8601 UTC
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_file_chunks_file_id ON file_chunks(file_id);


-- ── 5. embeddings ─────────────────────────────────────────
-- Maps file/chunk IDs to FAISS vector positions (V2 / Step 15).

CREATE TABLE IF NOT EXISTS embeddings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     INTEGER,
    chunk_id    INTEGER,          -- References file_chunks.id
    vector_id   INTEGER,          -- Position in FAISS index
    model_name  TEXT,             -- e.g. "all-MiniLM-L6-v2"
    created_at  TEXT,             -- ISO-8601 UTC
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);


-- ── 6. search_history ─────────────────────────────────────
-- Stores local search queries for history display (Step 12+).

CREATE TABLE IF NOT EXISTS search_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    query        TEXT    NOT NULL,
    searched_at  TEXT,            -- ISO-8601 UTC
    result_count INTEGER
);


-- ── 7. settings ───────────────────────────────────────────
-- Key-value store for all user-configurable preferences.

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- Default settings — INSERT OR IGNORE so re-running never overwrites user changes
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('app_version',              '0.1.0'),
    ('max_file_size_mb',         '25'),
    ('max_embed_chars',          '20000'),
    ('max_chunks_per_file',      '20'),
    ('chunk_size_words',         '400'),
    ('ocr_enabled',              'false'),
    ('semantic_search_enabled',  'false'),
    ('theme',                    'dark'),
    ('result_limit',             '50');
