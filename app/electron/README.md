# app/electron/

This folder will contain the **Electron main process** code.

## Planned Files (Step 2)

- `main.js` — Electron entry point, window creation, app lifecycle
- `preload.js` — Secure bridge between Electron and React renderer
- `ipc-handlers.js` — IPC handlers for folder picker, open file, open location
- `backend-manager.js` — Start/stop Python FastAPI backend process

## Responsibilities

- Create and manage the desktop app window
- Start the Python backend when the app launches
- Stop the Python backend when the app closes
- Provide native folder picker dialog
- Open files using the system default application
- Reveal files in Windows Explorer

> ⏳ Not implemented yet — awaiting Step 2.
