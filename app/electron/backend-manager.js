const { app } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');
const crypto = require('crypto');
const net = require('net');

class BackendManager {
  constructor() {
    this.backendProcess = null;
    this.port = null;
    this.controlToken = crypto.randomBytes(32).toString('hex');
    this.instanceId = crypto.randomBytes(16).toString('hex');
    this.dataDir = path.join(app.getPath('userData'), 'data');
    this.logDir = path.join(app.getPath('userData'), 'logs');
    this.isPackaged = app.isPackaged;
  }

  locate() {
    if (!this.isPackaged) {
      return null;
    }
    // PyInstaller onedir outputs a directory containing the executable.
    const exePath = path.join(process.resourcesPath, 'engine', 'deepfind-engine', 'deepfind-engine.exe');
    if (fs.existsSync(exePath)) {
      return exePath;
    }
    // Fallback if structured differently
    const altExePath = path.join(process.resourcesPath, 'engine', 'deepfind-engine.exe');
    if (fs.existsSync(altExePath)) {
      return altExePath;
    }
    
    console.error(`[BackendManager] Could not find backend executable.`);
    return null;
  }

  async findFreePort(startPort = 8765, endPort = 8799) {
    for (let port = startPort; port <= endPort; port++) {
      if (await this.isPortFree(port)) {
        return port;
      }
    }
    throw new Error('No free ports found in the specified range');
  }

  isPortFree(port) {
    return new Promise((resolve) => {
      const server = net.createServer();
      server.listen(port, '127.0.0.1', () => {
        server.once('close', () => resolve(true));
        server.close();
      });
      server.on('error', () => resolve(false));
    });
  }

  async launch() {
    if (this.backendProcess) {
      console.log('[BackendManager] Backend is already running.');
      return this.backendProcess;
    }

    const exePath = this.locate();
    if (!exePath) {
      console.log('[BackendManager] Running in dev mode, assuming backend is started manually.');
      // Wait, in dev mode we might have to use 8765, so let's default to that.
      this.port = 8765;
      return null;
    }

    try {
      this.port = await this.findFreePort();
      console.log(`[BackendManager] Found free port: ${this.port}`);
    } catch (e) {
      console.error('[BackendManager] Failed to find free port', e);
      throw e;
    }

    // Ensure logs directory exists
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }

    const logFile = path.join(this.logDir, 'electron-backend-launcher.log');
    const out = fs.openSync(logFile, 'a');
    const err = fs.openSync(logFile, 'a');

    console.log(`[BackendManager] Launching packaged backend from ${exePath}`);
    console.log(`[BackendManager] User Data Dir: ${app.getPath('userData')}`);

    this.backendProcess = spawn(exePath, [], {
      env: {
        ...process.env,
        DEEPFIND_USER_DATA_DIR: app.getPath('userData'),
        DEEPFIND_PORT: this.port.toString(),
        DEEPFIND_CONTROL_TOKEN: this.controlToken,
        DEEPFIND_INSTANCE_ID: this.instanceId,
      },
      detached: false,
      windowsHide: true,
      shell: false,
      cwd: path.dirname(exePath),
      stdio: ['ignore', out, err]
    });

    this.backendProcess.on('exit', (code, signal) => {
      console.log(`[BackendManager] Backend process exited with code ${code} and signal ${signal}`);
      this.backendProcess = null;
    });

    return this.backendProcess;
  }

  waitReady(timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const intervalMs = 500;

      const checkHealth = () => {
        // If we spawned a process but it died before becoming healthy, reject fast
        if (this.isPackaged && !this.backendProcess) {
           return reject(new Error('Backend process exited before becoming ready.'));
        }

        const req = http.get(`http://127.0.0.1:${this.port}/health`, (res) => {
          if (res.statusCode === 200) {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
              try {
                const json = JSON.parse(data);
                // In dev mode we might not have passed DEEPFIND_INSTANCE_ID so it falls back to 'dev-instance'
                if (!this.isPackaged || json.instance_id === this.instanceId) {
                  resolve(true);
                } else {
                  console.error(`[BackendManager] Instance ID mismatch! Expected ${this.instanceId}, got ${json.instance_id}`);
                  retry();
                }
              } catch (e) {
                retry();
              }
            });
          } else {
            retry();
          }
        });

        req.on('error', () => retry());
        req.end();
      };

      const retry = () => {
        if (Date.now() - startTime > timeoutMs) {
          reject(new Error('Backend startup timeout'));
        } else {
          setTimeout(checkHealth, intervalMs);
        }
      };

      checkHealth();
    });
  }

  terminate() {
    if (!this.backendProcess) return;

    console.log('[BackendManager] Terminating backend process gracefully...');

    // Try graceful shutdown via HTTP
    const req = http.request({
      hostname: '127.0.0.1',
      port: this.port,
      path: '/system/shutdown',
      method: 'POST',
      headers: {
        'X-DeepFind-Control-Token': this.controlToken
      }
    }, () => {
      console.log('[BackendManager] Graceful shutdown requested via HTTP.');
    });

    req.on('error', (err) => {
      console.log('[BackendManager] Failed to reach /system/shutdown endpoint, backend may already be dead:', err.message);
    });
    
    req.end();

    // Fallback force kill after 15 seconds if process doesn't exit
    const killTimer = setTimeout(() => {
      if (this.backendProcess) {
        console.log('[BackendManager] Backend did not exit gracefully within 15 seconds, forcing kill.');
        this.backendProcess.kill('SIGKILL');
        this.backendProcess = null;
      }
    }, 15000);
    
    // Clear the timer if it exits gracefully
    if (this.backendProcess) {
        this.backendProcess.once('exit', () => clearTimeout(killTimer));
    }
  }

  getLogPath() {
    return path.join(this.logDir, 'engine.log');
  }
}

module.exports = new BackendManager();
