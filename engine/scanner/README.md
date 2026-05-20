# engine/scanner/

This module will contain the **file system scanner**.

## Planned Files (Step 6)

- `scanner.py` — Recursive folder scanner that reads file metadata
- `file_filter.py` — Rules for skipping system folders, hidden files, binary files
- `change_detector.py` — Compare current vs. indexed state (mtime, size, hash)

## Scanner Rules

- Scan only selected folders (never the full system by default)
- Skip hidden files and system directories
- Skip files > 25 MB for content extraction (still index metadata)
- Record: path, name, extension, size, created_at, modified_at
- Do not read file content during metadata scan
- Handle permission errors gracefully — log and continue

> ⏳ Not implemented yet — awaiting Step 6.
