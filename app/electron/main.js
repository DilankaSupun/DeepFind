/**
 * DeepFind — Electron Main Process
 *
 * Responsibilities (current step):
 *   - Create the desktop window
 *   - Load the React UI (Vite dev server in dev, built files in production)
 *   - Register IPC handlers (folder picker, future: open file, etc.)
 *   - Handle window lifecycle
 *
 * Future steps will add:
 *   - Starting/stopping the Python FastAPI backend
 *   - Open file / open file location actions
 */

const { app, BrowserWindow, shell, globalShortcut } = require('electron');
const path = require('path');
const { registerIpcHandlers } = require('./ipc-handlers');

// Detect development mode: app.isPackaged is false when running with `electron .`
const isDev = !app.isPackaged;

// Vite dev server URL
const VITE_DEV_URL = 'http://localhost:5173';

// Keep a global reference to prevent the window from being garbage collected
let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    title: 'DeepFind',

    // Dark background matches the app theme - prevents white flash on load
    backgroundColor: '#0A0B0F',

    // Hide menu bar (File, Edit, View...) for a cleaner desktop app feel
    autoHideMenuBar: true,

    // Start hidden to avoid showing a white frame before the UI loads
    show: false,

    webPreferences: {
      // Preload script runs in a privileged context before page scripts
      preload: path.join(__dirname, 'preload.js'),

      // Security: disable Node.js in renderer process
      nodeIntegration: false,

      // Security: isolate preload context from renderer
      contextIsolation: true,
    },
  });

  // Show window only when content is fully ready (no white flash)
  // DevTools are NOT auto-opened - use Ctrl+Shift+I inside the Electron window
  mainWindow.once('ready-to-show', function() {
    mainWindow.show();
  });

  // Register all IPC handlers (folder picker, etc.)
  registerIpcHandlers(mainWindow);

  // Load the app
  if (isDev) {
    // Development: load from Vite dev server (hot reload enabled)
    mainWindow.loadURL(VITE_DEV_URL);
  } else {
    // Production: load the built React app
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Handle load failure in dev - Vite may not be fully ready yet on first attempt
  // Retry after 1 second to allow Vite time to start serving
  mainWindow.webContents.on('did-fail-load', function(_event, errorCode, errorDesc) {
    if (isDev) {
      console.log('[DeepFind] Load failed (' + errorCode + ': ' + errorDesc + ') - retrying in 1s...');
      setTimeout(function() {
        if (mainWindow) {
          mainWindow.loadURL(VITE_DEV_URL);
        }
      }, 1000);
    }
  });

  // Open any external links in the system browser, not inside Electron
  mainWindow.webContents.setWindowOpenHandler(function({ url }) {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', function() {
    mainWindow = null;
  });
}

// App lifecycle

app.whenReady().then(function() {
  createWindow();

  // Register Ctrl+Shift+I to open/toggle DevTools on demand (dev mode only)
  if (isDev) {
    globalShortcut.register('CommandOrControl+Shift+I', function() {
      if (mainWindow) {
        mainWindow.webContents.toggleDevTools();
      }
    });
  }

  // macOS: re-create window when dock icon is clicked and no windows are open
  app.on('activate', function() {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Unregister shortcuts cleanly on quit
app.on('will-quit', function() {
  globalShortcut.unregisterAll();
});

// Windows/Linux: quit when all windows are closed
app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
