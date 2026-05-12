const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

let mainWindow = null;
let backendProcess = null;

const BACKEND_PORT = 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const MAX_RETRIES = 30;
const RETRY_INTERVAL = 1000;

function getProjectRoot() {
  if (app.isPackaged) {
    return path.dirname(app.getPath('exe'));
  }
  return path.join(__dirname, '..');
}

function getBackendCommand() {
  let pythonExe, backendScript;

  if (app.isPackaged) {
    pythonExe = path.join(process.resourcesPath, 'runtime', 'python', 'python.exe');
    backendScript = path.join(process.resourcesPath, 'backend_server.py');
  } else {
    const root = getProjectRoot();
    pythonExe = path.join(root, 'runtime', 'python', 'python.exe');
    backendScript = path.join(root, 'backend_server.py');
    // Fallback to system python for dev
    if (!fs.existsSync(pythonExe)) {
      pythonExe = 'python';
    }
  }

  console.log(`[Main] Python: ${pythonExe}`);
  console.log(`[Main] Script: ${backendScript}`);
  return { cmd: pythonExe, args: [backendScript], isExe: true };
}

function startBackend() {
  const backend = getBackendCommand();
  const root = getProjectRoot();
  const dataDir = app.getPath('userData');

  const args = [...backend.args, '--port', String(BACKEND_PORT), '--data-dir', dataDir];

  console.log(`[Main] Starting backend: ${backend.cmd} ${args.join(' ')}`);

  const spawnOpts = {
    cwd: root,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env },
  };
  delete spawnOpts.env.ELECTRON_RUN_AS_NODE;

  backendProcess = spawn(backend.cmd, args, spawnOpts);

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error(`[Main] Failed to start backend: ${err.message}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Main] Backend exited with code ${code}`);
    backendProcess = null;
  });
}

function waitForBackend(retries = MAX_RETRIES) {
  return new Promise((resolve, reject) => {
    function check() {
      const req = http.get(`${BACKEND_URL}/api/health`, (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          retry();
        }
      });
      req.on('error', () => retry());
      req.setTimeout(2000, () => { req.destroy(); retry(); });
    }
    function retry() {
      retries--;
      if (retries <= 0) { reject(new Error('Backend failed to start')); return; }
      setTimeout(check, RETRY_INTERVAL);
    }
    check();
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('[Main] Stopping backend...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t']);
    } else {
      backendProcess.kill('SIGTERM');
    }
    backendProcess = null;
  }
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 900,
    minHeight: 600,
    title: 'BioInfo Platform',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  });

  mainWindow.loadURL(BACKEND_URL);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (setupWindow && !setupWindow.isDestroyed()) {
      setupWindow.close();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ========== App Lifecycle ==========

app.whenReady().then(async () => {
  startBackend();

  try {
    await waitForBackend();
    console.log('[Main] Backend ready');
    createMainWindow();
  } catch (err) {
    console.error(`[Main] ${err.message}`);
    dialog.showErrorBox(
      'Startup Failed',
      'Could not connect to the analysis engine.\n\nError: ' + err.message
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  stopBackend();
  app.quit();
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createMainWindow();
  }
});
