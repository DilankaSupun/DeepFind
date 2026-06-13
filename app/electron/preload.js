/**
 * DeepFind — Electron Preload Script
 *
 * Runs in a privileged context BEFORE the React app loads.
 * Creates a safe, minimal API bridge via contextBridge.
 *
 * Security rules:
 *   - contextIsolation: true  → preload runs in its own isolated context
 *   - nodeIntegration: false  → React renderer has NO direct Node.js access
 *   - Only APIs listed below are accessible to React via window.deepfind
 *
 * Step 6: Added selectFolder() for native OS folder picker.
 * Future steps will add:
 *   - openFile(path)         → shell.openPath
 *   - openInExplorer(path)   → shell.showItemInFolder
 *   - onIndexingProgress(cb) → ipcRenderer.on(...)
 */

const { contextBridge, ipcRenderer } = require('electron');

console.log("DeepFind preload loaded");

const portArg = process.argv.find(arg => arg.startsWith('--backend-port='));
const port = portArg ? portArg.split('=')[1] : '8765';

contextBridge.exposeInMainWorld('deepfind', {
  // ── App metadata ─────────────────────────────────────────────────────────
  isDesktop: true,
  version:  '0.1.0',
  platform: process.platform,   // 'win32' | 'darwin' | 'linux'
  baseUrl: `http://127.0.0.1:${port}`,

  // ── Native folder picker ─────────────────────────────────────────────────
  // Opens the OS folder dialog. Returns the selected path string, or null.
  selectFolder: () => ipcRenderer.invoke('dialog:selectFolder'),

  // ── Native file actions (Step 13) ────────────────────────────────────────
  openFile:     (filePath) => ipcRenderer.invoke('open-file', filePath),
  showInFolder: (filePath) => ipcRenderer.invoke('show-in-folder', filePath),

  // ── Engine Lifecycle ─────────────────────────────────────────────────────
  onEngineStatus: (callback) => ipcRenderer.on('engine:status', (_e, data) => callback(data)),
  retryEngine:    () => ipcRenderer.invoke('engine:retry'),
  openEngineLogs: () => ipcRenderer.invoke('engine:open-logs'),

  // ── Future APIs (added in later steps) ───────────────────────────────────
  // onIndexProgress: (callback) => ipcRenderer.on('index:progress', (_e, data) => callback(data)),
});
