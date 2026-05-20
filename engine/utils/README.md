# engine/utils/

This module will contain **shared utility functions** used across the engine.

## Planned Files

- `logger.py` — Structured logging setup for the Python engine
- `file_utils.py` — File size formatting, extension normalization, hash calculation
- `text_utils.py` — Text cleaning, truncation, keyword extraction helpers
- `config.py` — Load and manage app configuration (DB path, limits, settings)
- `constants.py` — Default limits, supported file extensions, skip directories

## Key Constants (Planned)

```python
MAX_FILE_SIZE_BYTES     = 25 * 1024 * 1024   # 25 MB
MAX_EMBED_CHARS         = 20_000
MAX_CHUNKS_PER_FILE     = 20
CHUNK_SIZE_WORDS        = 400
EMBED_BATCH_SIZE        = 32
SUPPORTED_TEXT_EXTENSIONS = ['.txt', '.md', '.csv', ...]
SKIP_DIRECTORIES        = ['node_modules', '.git', '__pycache__', ...]
```

> ⏳ Not implemented yet — will be built incrementally as needed.
