const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');
const AdmZip = require('adm-zip');

let mainWindow = null;
let backendProcess = null;

const BACKEND_PORT = 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const MAX_RETRIES = 60;
const RETRY_INTERVAL = 1500;

function getProjectRoot() {
  if (app.isPackaged) {
    return path.dirname(app.getPath('exe'));
  }
  return path.join(__dirname, '..');
}

function getRuntimePython() {
  // Extracts runtime.zip to userData on first run, returns path to python.exe
  const userData = app.getPath('userData');
  // Extract to userData (zip already contains 'runtime/' prefix internally)
  const extractDir = userData;
  const runtimeDir = path.join(extractDir, 'runtime');
  const pythonExe = path.join(runtimeDir, 'python', 'python.exe');

  if (fs.existsSync(pythonExe)) {
    console.log('[Main] Using existing runtime at', runtimeDir);
    return pythonExe;
  }

  // Extract runtime.zip
  const zipPath = app.isPackaged
    ? path.join(process.resourcesPath, 'runtime.zip')
    : path.join(getProjectRoot(), 'runtime.zip');

  if (!fs.existsSync(zipPath)) {
    console.error('[Main] runtime.zip not found at', zipPath);
    return null;
  }

  console.log('[Main] Extracting to', extractDir, '...');
  const startTime = Date.now();
  try {
    fs.mkdirSync(extractDir, { recursive: true });
    const zip = new AdmZip(zipPath);
    zip.extractAllTo(extractDir, true);
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log('[Main] Runtime extracted in', elapsed, 's');
  } catch (e) {
    console.error('[Main] Extraction failed:', e.message);
    return null;
  }

  if (fs.existsSync(pythonExe)) {
    return pythonExe;
  }
  console.error('[Main] python.exe not found at', pythonExe);
  return null;
}

function getBackendCommand() {
  let pythonExe, backendScript;

  if (app.isPackaged) {
    pythonExe = getRuntimePython();
    backendScript = path.join(process.resourcesPath, 'backend_server.py');
  } else {
    const root = getProjectRoot();
    pythonExe = path.join(root, 'runtime', 'python', 'python.exe');
    backendScript = path.join(root, 'backend_server.py');
    if (!fs.existsSync(pythonExe)) {
      pythonExe = 'python';
    }
  }

  if (!pythonExe) {
    throw new Error('Python runtime not available. Please reinstall the application.');
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
    title: 'BEing Bio',
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
      'The analysis engine could not start.\n\n' +
      'Possible fixes:\n' +
      '1. Close all BEing Bio windows and try again.\n' +
      '2. Restart your computer if the problem persists.\n' +
      '3. Check if another program is using port ' + BACKEND_PORT + '.\n\n' +
      'Error: ' + err.message
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
