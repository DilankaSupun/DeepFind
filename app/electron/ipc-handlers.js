/**
 * DeepFind — Electron IPC Handlers
 *
 * All ipcMain handlers live here. Registered in main.js on app startup.
 *
 * Step 6: Folder picker dialog.
 * Future steps will add:
 *   - openFile(path)        → shell.openPath
 *   - openInExplorer(path)  → shell.showItemInFolder
 *   - onIndexingProgress    → send progress events to renderer
 */

const { ipcMain, dialog } = require('electron');

/**
 * Register all IPC handlers.
 * Called once from main.js after the window is created.
 *
 * @param {import('electron').BrowserWindow} win - The main browser window
 */
function registerIpcHandlers(win) {
  // ── dialog:selectFolder ──────────────────────────────────────────────────────
  //
  // Opens a native OS folder picker dialog.
  // Returns the selected folder path string, or null if cancelled.
  //
  // Called from React via:  window.deepfind.selectFolder()
  //
  ipcMain.handle('dialog:selectFolder', async () => {
    const result = await dialog.showOpenDialog(win, {
      title: 'Select a folder to index',
      buttonLabel: 'Add Folder',
      properties: ['openDirectory', 'createDirectory'],
    });

    if (result.canceled || result.filePaths.length === 0) {
      return null; // User cancelled — React receives null
    }

    // Normalize to forward slashes for consistent cross-platform paths
    return result.filePaths[0].replace(/\\/g, '/');
  });

  const { shell } = require('electron');

  const fs = require('fs');

  // Prevent duplicate registration issues
  ipcMain.removeHandler('open-file');
  ipcMain.removeHandler('show-in-folder');

  ipcMain.handle('open-file', async (_event, filePath) => {
    try {
      if (!filePath || typeof filePath !== 'string') {
        return { success: false, error: 'Invalid file path' };
      }

      if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
        return { success: false, error: 'Only local files can be opened' };
      }

      if (!fs.existsSync(filePath)) {
        return { success: false, error: 'File not found' };
      }

      const result = await shell.openPath(filePath);

      if (result) {
        return { success: false, error: result };
      }

      return { success: true };
    } catch (error) {
      return { success: false, error: error.message || 'Failed to open file' };
    }
  });

  ipcMain.handle('show-in-folder', async (_event, filePath) => {
    try {
      if (!filePath || typeof filePath !== 'string') {
        return { success: false, error: 'Invalid file path' };
      }

      if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
        return { success: false, error: 'Only local files can be shown' };
      }

      if (!fs.existsSync(filePath)) {
        return { success: false, error: 'File not found' };
      }

      shell.showItemInFolder(filePath);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message || 'Failed to show file in folder' };
    }
  });
}

module.exports = { registerIpcHandlers };
