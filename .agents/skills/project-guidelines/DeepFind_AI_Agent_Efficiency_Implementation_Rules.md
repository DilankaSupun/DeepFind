# DeepFind AI Agent Implementation Rules

## Purpose of This Document

This document is a strict instruction guide for the AI coding agent that will implement the **DeepFind** desktop application.

The AI agent's job is **only to write code according to the instructions**.

The agent must not independently redesign the architecture, choose heavier models, add unnecessary features, or make performance-related decisions that conflict with this document.

DeepFind must be built as a:

> **Lightweight, local-first, resource-friendly desktop AI file search application.**

---

# 1. Core Agent Rule

The AI agent must follow this rule throughout the project:

> **Only implement the current requested step. Do not build the whole application at once.**

After each step, the agent must:

1. Explain what files were created or changed.
2. Explain how to run the current step.
3. Explain how to test the current step.
4. Stop and wait for the next instruction.

The agent must not continue to future steps unless the user asks.

---

# 2. Project Goal

DeepFind is a desktop file search application that helps users find local files by:

- Filename
- File path
- File extension
- Metadata
- Extracted text content
- Auto-generated tags
- Natural language meaning
- Semantic similarity
- Similar files

The app should feel fast like a local file search tool while also supporting AI-powered semantic search.

---

# 3. Hard Requirements

The agent must follow these requirements.

## 3.1 Local-First Requirement

All processing must happen on the user's machine.

The app must not:

- Upload files to any server
- Send file content to cloud APIs
- Use online AI APIs
- Use remote vector databases
- Store user file content outside the local machine

## 3.2 Desktop App Requirement

DeepFind must be built as a desktop app.

It must not be built as a normal public website.

The final app should run as an installable desktop application.

## 3.3 Lightweight Requirement

The app must be resource-friendly.

The agent must avoid:

- Large local LLMs
- Heavy background processes
- Unnecessary file scanning
- Loading all extracted text into memory
- Processing very large files by default
- Running OCR by default
- Generating embeddings during live search

## 3.4 Indexed Search Requirement

The app must not scan files when the user searches.

Search must happen only through pre-built indexes:

- SQLite metadata index
- SQLite FTS5 full-text index
- FAISS semantic vector index

---

# 4. Approved Architecture

The agent must follow this architecture.

```text
Electron Desktop Shell
        ↓
React Frontend
        ↓
Local API Bridge
        ↓
Python Search Engine
        ↓
Hybrid Search Layer
   ┌───────────────┬───────────────┬───────────────┐
   │ Filename      │ Full-text     │ Semantic      │
   │ Search        │ Search        │ Search        │
   └───────────────┴───────────────┴───────────────┘
        ↓
Ranking Engine
        ↓
Results with Explanation
        ↓
SQLite + FTS5 + FAISS
        ↓
Local Files
```

---

# 5. Approved Tech Stack

The agent must use the following stack unless the user explicitly changes it.

## Desktop Shell

```text
Electron
```

## Frontend

```text
React
```

## Local Backend / Search Engine

```text
Python
FastAPI
```

## Database

```text
SQLite
SQLite FTS5
```

## Semantic Search

```text
FAISS
sentence-transformers/all-MiniLM-L6-v2
```

## File Watching

```text
watchdog
```

## Text Extraction

```text
pypdf
python-docx
plain text readers
code file readers
```

## OCR Later

```text
Tesseract
```

OCR must not be implemented in early versions unless explicitly requested.

---

# 6. Technologies the Agent Must Not Use

The agent must not use these unless the user explicitly allows them later:

```text
Cloud AI APIs
OpenAI API
Gemini API
Claude API
Online vector databases
Remote databases
Large local LLMs
Llama models
GPT-style local chat models
Image generation models
Cloud storage
Automatic online sync
```

The first versions must remain lightweight and fully local.

---

# 7. Version-Based Implementation Plan

The agent must build the app version by version.

Do not implement future version features early.

---

## Version 1: Core Local File Search

### Goal

Build a working desktop app that can index selected folders and search files by filename, metadata, extracted text, and basic tags.

### Version 1 Features

- Electron desktop shell
- React UI
- Python FastAPI local backend
- SQLite database
- Folder selection
- File metadata indexing
- Filename search
- File path search
- File extension search
- Text extraction for supported files
- SQLite FTS5 content search
- Basic auto-tagging
- Search result list
- Open file
- Open file location
- Indexing progress
- Basic settings

### Version 1 Must Not Include

- Semantic search
- FAISS
- Embeddings
- OCR
- Image meaning search
- Similar file detection
- Model fine-tuning
- Large AI models

---

## Version 2: Lightweight Semantic AI Search

### Goal

Add semantic search using a lightweight embedding model and FAISS.

### Version 2 Features

- `sentence-transformers/all-MiniLM-L6-v2`
- Chunk-level embeddings
- FAISS vector index
- Semantic search
- Hybrid ranking
- Result explanation
- Similar file detection

### Version 2 Must Not Include

- Model training from scratch
- Large LLMs
- Cloud APIs
- OCR by default
- Heavy summarization models

---

## Version 3: Background Updates and Efficiency Improvements

### Goal

Improve real-world usability and indexing efficiency.

### Version 3 Features

- File watcher using `watchdog`
- Background re-indexing
- Changed file detection
- Deleted file handling
- Renamed file handling
- Re-index button
- Clear index option
- Performance logging

---

## Version 4: OCR and Advanced File Understanding

### Goal

Add OCR only after the core app and semantic search are stable.

### Version 4 Features

- Tesseract OCR
- Screenshot text search
- Scanned document text extraction
- OCR settings
- OCR disabled by default
- File size limit for OCR

### Version 4 Must Not Include

- Heavy image models
- Image generation
- Real-time OCR for all images

---

# 8. AI/ML Rules

The AI/ML system must be lightweight.

## 8.1 No Training First

The agent must not train a model from scratch.

The first semantic search implementation must use a pre-trained lightweight embedding model.

Approved model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Reason:

- Lightweight
- CPU-friendly
- Good for semantic search
- Suitable for local applications
- Produces small 384-dimensional embeddings

---

## 8.2 AI Is Only a Semantic Layer

AI must not replace the whole search system.

DeepFind must use hybrid search:

```text
Filename search
+ Full-text search
+ Tag search
+ Metadata filtering
+ Semantic search
```

Semantic search is only one part of the ranking system.

---

## 8.3 Chunk-Level Embeddings

The agent must not embed very large files as one huge text block.

Use chunking.

Recommended chunk rules:

```text
Chunk size: 300-500 words
Max chunks per file in early versions: 20
Max text length per file for embeddings: 20,000 characters
```

Each chunk should map back to its original file.

---

## 8.4 Embedding Generation Rules

Embeddings must be generated only during indexing or background processing.

The app must not generate file embeddings during live search.

During live search, the app may generate only the query embedding.

---

## 8.5 Embedding Cache

The agent must cache embeddings.

If a file has not changed, do not regenerate embeddings.

Use file change detection:

```text
file path
file size
modified timestamp
optional content hash
```

---

## 8.6 Optional Future Fine-Tuning

Fine-tuning is not part of early versions.

If added later, it must be optional and local.

Possible future feedback data:

```text
search query
clicked file
ignored results
timestamp
```

This data must stay local.

---

## 8.7 ONNX Optimization Later

The agent must not start with ONNX unless requested.

Future optimization path:

```text
Convert MiniLM to ONNX
Apply INT8 quantization
Use ONNX Runtime for CPU inference
```

This is a later optimization step, not an MVP requirement.

---

# 9. Memory Efficiency Rules

The app must avoid unnecessary memory usage.

## 9.1 Do Not Load Everything Into Memory

The agent must not load all file records, all extracted text, or all chunks into memory at once.

Use pagination and limits.

Example:

```text
Return top 20 or top 50 search results
Load file details only when user opens a result
Load extracted text preview only when needed
```

---

## 9.2 Keep FAISS Efficient

FAISS index can be loaded into memory, but metadata and text must remain in SQLite.

FAISS should store vectors only.

SQLite should store:

- File metadata
- Tags
- Extracted text
- Chunk text previews
- Mapping between file IDs and vector IDs

---

## 9.3 Limit Text Stored for Embeddings

Do not embed unlimited text.

Recommended limits:

```text
Max text characters per file for embedding: 20,000
Max chunks per file: 20
Max chunk size: 300-500 words
```

Full extracted text can be stored in SQLite if reasonable, but previews should be used in UI.

---

## 9.4 Skip Large Files by Default

In early versions, skip content extraction for very large files.

Recommended defaults:

```text
Max file size for text extraction: 25 MB
Max file size for OCR: 10 MB
Max file size for semantic embedding: 25 MB
```

Still index filename and metadata for skipped files.

---

## 9.5 Batch Processing

Embedding generation must be batched.

Recommended batch size:

```text
16 or 32 chunks per batch
```

Do not process every chunk one by one if batching is available.

---

## 9.6 Background Processing

Heavy tasks must run in the background:

- Text extraction
- Tag generation
- Embedding generation
- OCR
- Similar file detection

The UI must remain responsive.

---

# 10. Software Efficiency Rules

## 10.1 Staged Indexing

The agent must implement indexing in stages.

```text
Stage 1: Metadata indexing
Stage 2: Text extraction
Stage 3: FTS5 indexing
Stage 4: Tag generation
Stage 5: Embedding generation
Stage 6: OCR later
```

The app should become usable after Stage 1.

Do not block the user until all AI processing is complete.

---

## 10.2 Search Must Be Instant from Indexes

When the user searches, the app must:

- Search SQLite metadata
- Search SQLite FTS5
- Search FAISS, if semantic search is enabled
- Merge and rank results

The app must not:

- Scan folders during search
- Extract text during search
- Generate file embeddings during search
- Run OCR during search

---

## 10.3 Incremental Indexing

When files change, only re-index changed files.

Do not re-index the entire folder unless requested.

Use:

```text
modified timestamp
file size
optional hash
```

---

## 10.4 Error-Safe Processing

The agent must handle errors safely.

If a file cannot be read, the app should:

- Skip the file content extraction
- Still index metadata if possible
- Store error status
- Continue processing other files

The app must not crash because of:

- Permission errors
- Corrupted PDFs
- Unsupported file types
- Deleted files
- Locked files
- Very large files

---

## 10.5 File Watcher Efficiency

When adding file watcher support:

- Debounce rapid changes
- Avoid duplicate indexing jobs
- Queue changed files
- Process changes gradually
- Do not continuously rescan entire folders

---

# 11. Search Ranking Rules

The agent must use hybrid ranking.

Initial ranking formula:

```text
Final Score =
filename_score * 0.30
+ tag_score * 0.20
+ content_score * 0.25
+ semantic_score * 0.20
+ recency_score * 0.05
```

For Version 1, semantic score can be zero.

For Version 2, semantic score comes from FAISS similarity.

Filename matches should remain important.

A file with a strong filename match should not be buried by semantic results.

---

# 12. Result Explanation Rules

Every result should include a simple explanation when possible.

Examples:

```text
Filename matched "payment"
Content contains "PayHere sandbox"
Tags include "gateway"
Semantic meaning is close to your search
Modified recently
```

The explanation must be generated from actual matching signals, not fake AI text.

---

# 13. Auto-Tagging Rules

Auto-tagging must start simple and lightweight.

Use signals from:

- File extension
- Folder name
- Filename
- Extracted text keywords
- Known keyword dictionaries

Do not use a large LLM for tagging.

Example categories:

```text
finance: invoice, payment, receipt, bank, salary, transaction
university: assignment, lecture, tutorial, practical, exam, coursework
project: github, database, frontend, backend, api, documentation
code: function, class, import, controller, model, config
design: figma, logo, ui, ux, wireframe, prototype
```

---

# 14. Text Extraction Rules

Supported in early versions:

```text
.txt
.md
.csv
.py
.js
.jsx
.ts
.tsx
.php
.java
.html
.css
.sql
.pdf
.docx
```

The agent must not attempt to extract text from all file types at once.

Unsupported file types should still have metadata indexed.

---

# 15. OCR Rules

OCR is a later feature.

When implemented:

- OCR must be disabled by default
- User must enable OCR in settings
- OCR must use file size limits
- OCR must run in the background
- OCR must not run during search
- OCR must store extracted text in the index

OCR should focus on:

```text
screenshots
scanned documents
images with text
```

---

# 16. Database Efficiency Rules

SQLite is the source of truth for metadata.

Recommended tables:

```text
files
indexed_folders
file_chunks
embeddings
search_history
settings
index_jobs
```

Use SQLite FTS5 for content search.

Do not create unnecessary duplicate tables.

Do not store large binary file contents in SQLite.

Store paths and extracted text only.

---

# 17. API Efficiency Rules

The frontend must not receive huge payloads.

API responses should be limited.

Search response should include:

```text
file id
file name
path
extension
size
modified date
tags
score
matched reasons
small preview
```

Do not return full extracted text in search results.

Full details should be loaded only when user opens a file detail panel.

---

# 18. UI Efficiency Rules

React UI must be lightweight.

Use:

- Pagination or virtualized lists for many results
- Debounced search input
- Loading states
- Empty states
- Progress indicators

Do not render thousands of results at once.

Recommended search behavior:

```text
Debounce input by 250-400 ms
Return top 20 or top 50 results
Load more only when requested
```

---

# 19. Desktop App Rules

Electron must handle desktop-specific tasks:

- Open app window
- Start Python backend
- Stop Python backend on app close
- Open native folder picker
- Open file
- Open file location

React must not directly access the file system.

---

# 20. Security and Privacy Rules

The agent must protect user privacy.

Rules:

- No cloud upload
- No remote APIs
- No telemetry by default
- No hidden background network calls
- Local database only
- Clear index option must be provided eventually
- User must control indexed folders

---

# 21. Step-by-Step Build Workflow

The user will instruct the agent step by step.

The agent must follow this workflow.

## Step 0: Understand Project

Read the project blueprint and this instruction file.

Do not code yet.

Confirm understanding.

---

## Step 1: Create Project Structure

Create folders and placeholder files only.

Do not implement features.

---

## Step 2: Setup Electron + React

Create a working desktop window with React.

Do not connect backend yet.

---

## Step 3: Setup Python FastAPI Backend

Create a local backend with health check endpoint.

Do not implement file scanning yet.

---

## Step 4: Connect Frontend to Backend

React should call backend health endpoint.

Do not implement indexing yet.

---

## Step 5: Setup SQLite Database

Create schema and database connection.

Do not scan files yet.

---

## Step 6: Build File Scanner

Scan selected folder and return metadata.

Do not extract content yet.

---

## Step 7: Store Metadata

Save scanned file metadata into SQLite.

---

## Step 8: Add Filename Search

Search file name, path, and extension using indexed metadata.

Do not scan during search.

---

## Step 9: Add Text Extraction

Extract text from supported text, code, PDF, and DOCX files.

---

## Step 10: Add SQLite FTS5 Search

Index extracted text and search file content.

---

## Step 11: Add Basic Auto-Tagging

Generate tags from filename, path, extension, and extracted keywords.

---

## Step 12: Build Search UI

Create search bar, filters, result cards, and basic result explanations.

---

## Step 13: Add Open File / Open Folder

Use Electron or backend-safe actions to open files and locations.

---

## Step 14: Add Indexing Progress

Show progress while indexing.

---

## Step 15: Add Semantic Search

Add MiniLM embeddings and FAISS.

---

## Step 16: Add Hybrid Ranking

Merge filename, tag, content, semantic, and recency scores.

---

## Step 17: Add Similar File Detection

Use embeddings to find similar files.

---

## Step 18: Add File Watcher

Use watchdog for changed files.

---

## Step 19: Add OCR Later

Only implement OCR after core app is stable.

---

## Step 20: Add Packaging

Package app as desktop installer.

---

# 22. Required Response Format After Each Agent Step

After completing each step, the agent must respond with:

```text
Completed Step:
Files Created/Updated:
What Was Implemented:
How to Run:
How to Test:
Limitations:
Next Recommended Step:
```

The agent must not proceed to the next step automatically.

---

# 23. Acceptance Criteria

The project is acceptable only if:

- It runs as a desktop app
- It indexes selected folders locally
- It searches from indexes, not live folder scans
- It supports filename search
- It supports content search
- It stores data locally in SQLite
- It uses FTS5 for full-text search
- It uses MiniLM + FAISS for semantic search in Version 2
- It does not use cloud APIs
- It does not use large LLMs
- It handles errors safely
- It remains responsive during indexing
- It includes clear documentation

---

# 24. Final Reminder to the Agent

The agent is not responsible for choosing a new architecture.

The agent is not responsible for deciding to add heavy features.

The agent is not responsible for changing the model plan.

The agent's job is:

> **Implement the requested step exactly, efficiently, and safely.**
