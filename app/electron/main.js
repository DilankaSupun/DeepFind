/**
 * DeepFind — Electron Main Process
 *
 * Responsibilities (current step):
 *   - Create the desktop window
 *   - Load the React UI (Vite dev server in dev, built files in production)
 *   - Register IPC handlers (folder picker, open file, show in folder)
 *   - Handle window lifecycle
 *
 * Step 21 will add (Python backend bundling):
 *   - BackendManager: locates, launches, and terminates the packaged Python .exe
 *   - Interface contract (to be implemented in app/electron/backend-manager.js):
 *
 *     BackendManager.locate()     → string | null
 *       Finds the bundled engine executable path relative to app.getAppPath().
 *       In dev: returns null (user runs engine manually).
 *       In prod: returns path to resources/engine/deepfind-engine.exe
 *
 *     BackendManager.launch(dataDir)  → ChildProcess
 *       Spawns the engine executable with DEEPFIND_DATA_DIR env var set to
 *       Electron's app.getPath('userData') + '/data'.
 *       Captures stdout/stderr to logs/engine.log.
 *
 *     BackendManager.waitReady(timeoutMs)  → Promise<boolean>
 *       Polls GET http://127.0.0.1:8765/health until 200 or timeout.
 *       Shows a loading screen in Electron while waiting.
 *
 *     BackendManager.ensureSingle()  → boolean
 *       Returns true if the backend port is already listening (prevents
 *       double-launch when user opens a second app window).
 *
 *     BackendManager.terminate()  → void
 *       Sends SIGTERM to the engine process on app 'before-quit' event.
 *       Waits up to 3 seconds before force-killing.
 *
 *     BackendManager.getLogPath()  → string
 *       Returns the absolute path to the engine log file for display
 *       in error dialogs or a "View Logs" button.
 */

const { app, BrowserWindow, shell, globalShortcut } = require('electron');
const path = require('path');
const { registerIpcHandlers } = require('./ipc-handlers');
const backendManager = require('./backend-manager');

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

      // Pass the dynamic backend port to the preload script
      additionalArguments: [`--backend-port=${require('./backend-manager').port || 8765}`],
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

// Single instance lock
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // Someone tried to run a second instance, we should focus our window.
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async function() {
    createWindow();

    if (app.isPackaged) {
      console.log('[DeepFind] Launching Backend...');
      
      const startBackend = async () => {
        if (mainWindow) {
          mainWindow.webContents.send('engine:status', { state: 'starting', message: 'Starting DeepFind engine...' });
        }
        
        backendManager.launch();
        try {
          await backendManager.waitReady(30000);
          console.log('[DeepFind] Backend is ready!');
          if (mainWindow) {
            mainWindow.webContents.send('engine:status', { state: 'ready', message: 'Engine ready' });
          }
        } catch (err) {
          console.error('[DeepFind] Backend failed to start:', err);
          if (mainWindow) {
            mainWindow.webContents.send('engine:status', { 
              state: 'error', 
              message: 'Engine failed to start', 
              error: err.message 
            });
          }
        }
      };

      // Start backend once window finishes loading to ensure IPC is ready
      mainWindow.webContents.once('did-finish-load', () => {
        startBackend();
      });
      
      // Also register IPC handlers for retrying / opening logs
      const { ipcMain, shell } = require('electron');
      ipcMain.handle('engine:retry', () => {
        startBackend();
      });
      ipcMain.handle('engine:open-logs', () => {
        shell.openPath(backendManager.getLogPath());
      });
    }

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
}

// Unregister shortcuts cleanly on quit
app.on('will-quit', function() {
  globalShortcut.unregisterAll();
  backendManager.terminate();
});

// Windows/Linux: quit when all windows are closed
app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
