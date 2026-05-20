# DeepFind — Setup Notes

> Developer reference for environment setup. Updated as each component is built.

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Node.js | 18+ | Electron + React + Vite |
| npm | 9+ | Package management |
| Python | 3.10+ | Search engine (Step 3+) |
| Git | Any | Version control |

---

## Step 2: Electron + React Setup (Current)

### Install Dependencies

```powershell
cd app
npm install
```

### Run Development App

```powershell
cd app
npm run dev
```

This command:
1. Starts the **Vite dev server** at `http://localhost:5173`
2. Waits for Vite to be ready
3. Launches the **Electron desktop window** loading the React app

### Individual Commands

```powershell
# Run only the Vite frontend (browser at localhost:5173)
npm run dev:frontend

# Run only the Electron window (requires Vite already running)
npm run dev:electron
```

---

## Project Structure (Step 2)

```
app/
├── package.json            ← npm scripts and dependencies
├── vite.config.js          ← Vite config (root: ./frontend)
├── electron/
│   ├── main.js             ← Electron main process
│   └── preload.js          ← Secure bridge to renderer
└── frontend/
    ├── index.html          ← Vite HTML entry
    └── src/
        ├── main.jsx        ← React entry point
        ├── App.jsx         ← Welcome screen component
        ├── components/
        │   └── SearchBar/  ← Placeholder search bar
        └── styles/
            ├── index.css   ← Global design system (CSS variables)
            └── App.css     ← App layout styles
```

---

## Step 3: Python Engine Setup (Current)

### First-Time Setup

```powershell
cd engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Backend

```powershell
cd engine
.venv\Scripts\activate
python main.py
```

Or run directly with uvicorn:

```powershell
cd engine
.venv\Scripts\activate
uvicorn api.server:app --host 127.0.0.1 --port 8765 --reload
```

### Quick Start (Windows script)

```powershell
# From project root:
.\scripts\run_engine.bat
```

### Test the Backend

Once running, visit in your browser or curl:

```
http://127.0.0.1:8765/health    <- Health check (JSON)
http://127.0.0.1:8765/docs      <- Swagger UI (interactive docs)
http://127.0.0.1:8765/redoc     <- ReDoc UI
```

Expected `/health` response:

```json
{
  "status": "ok",
  "service": "DeepFind Engine",
  "version": "0.1.0",
  "backend": "FastAPI",
  "timestamp": "2026-05-19T10:26:49.199490+00:00"
}
```

---

## Python Dependencies (Planned)

```
fastapi
uvicorn[standard]
pypdf
python-docx
sentence-transformers      # V2 only
faiss-cpu                  # V2 only
watchdog                   # V3 only
pytesseract                # V4 only
```

---

## Local Data Storage

The app stores all data locally:

```
Windows: %APPDATA%\DeepFind\
  ├── deepfind.db            ← SQLite database (Step 5+)
  └── faiss.index            ← FAISS vector index (V2, Step 15+)
```

---

## Development Status

| Step | Description | Status |
|------|-------------|--------|
| Step 0 | Understand project | ✅ Done |
| Step 1 | Project structure | ✅ Done |
| Step 2 | Electron + React desktop app | ✅ Done |
| Step 3 | Python FastAPI backend | ✅ Done |
| Step 4 | Connect frontend to backend | ⏳ Pending |
| Step 5 | SQLite database schema | ⏳ Pending |
| Steps 6–20 | See agent.md for full plan | ⏳ Pending |
