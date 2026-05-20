# tests/

This folder will contain all test files for DeepFind.

## Planned Test Areas

| Test Area | What to Test |
|-----------|-------------|
| `test_scanner.py` | Recursive scan, skip rules, metadata accuracy |
| `test_extractors.py` | PDF, DOCX, TXT, code file text extraction |
| `test_database.py` | Schema creation, CRUD operations, FTS5 indexing |
| `test_search.py` | Filename search, FTS5 search, tag search |
| `test_ranking.py` | Hybrid scoring formula, result ordering |
| `test_indexer.py` | Staged indexing, change detection, error handling |
| `test_api.py` | FastAPI endpoint responses and error handling |
| `test_semantic.py` | Embedding generation, FAISS search (V2) |

## Test Fixtures

```
tests/
├── fixtures/
│   ├── sample_files/      ← Small test files for extraction testing
│   └── test_db/           ← Temporary test databases
└── *.py                   ← Test modules
```

> Tests will be written alongside each feature as it is implemented.
