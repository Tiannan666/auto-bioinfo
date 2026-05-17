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
  if (app.isPackaged) return path.dirname(app.getPath('exe'));
  return path.join(__dirname, '..');
}

function getRuntimePython() {
  const userData = app.getPath('userData');
  const extractDir = userData;
  const runtimeDir = path.join(extractDir, 'runtime');
  const pythonExe = path.join(runtimeDir, 'python', 'python.exe');

  if (fs.existsSync(pythonExe)) return pythonExe;

  const zipPath = app.isPackaged
    ? path.join(process.resourcesPath, 'runtime.zip')
    : path.join(getProjectRoot(), 'runtime.zip');

  if (!fs.existsSync(zipPath)) return null;

  console.log('[Main] Extracting runtime...');
  try {
    fs.mkdirSync(extractDir, { recursive: true });
    new AdmZip(zipPath).extractAllTo(extractDir, true);
    console.log('[Main] Runtime extracted');
  } catch (e) { console.error('[Main]', e.message); return null; }

  return fs.existsSync(pythonExe) ? pythonExe : null;
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
    if (!fs.existsSync(pythonExe)) pythonExe = 'python';
  }
  if (!pythonExe) throw new Error('Python runtime not available.');
  return { cmd: pythonExe, args: [backendScript] };
}

function startBackend() {
  const backend = getBackendCommand();
  const dataDir = app.getPath('userData');
  const args = [...backend.args, '--port', String(BACKEND_PORT), '--data-dir', dataDir];
  const env = { ...process.env };
  delete env.ELECTRON_RUN_AS_NODE;

  console.log('[Main] Starting backend:', backend.cmd, args.join(' '));
  backendProcess = spawn(backend.cmd, args, {
    cwd: app.isPackaged ? path.dirname(app.getPath('exe')) : getProjectRoot(),
    stdio: ['ignore', 'pipe', 'pipe'],
    env: env,
  });
  backendProcess.stdout.on('data', d => console.log('[Backend]', d.toString().trim()));
  backendProcess.stderr.on('data', d => console.log('[Backend]', d.toString().trim()));
  backendProcess.on('close', code => { console.log('[Main] Backend exited:', code); backendProcess = null; });
}

function waitForBackend(retries = MAX_RETRIES) {
  return new Promise((resolve, reject) => {
    function check() {
      const req = http.get(`${BACKEND_URL}/api/health`, res => {
        if (res.statusCode === 200) resolve(true); else retry();
      });
      req.on('error', () => retry());
      req.setTimeout(2000, () => { req.destroy(); retry(); });
    }
    function retry() {
      if (--retries <= 0) { reject(new Error('Backend failed to start')); return; }
      setTimeout(check, RETRY_INTERVAL);
    }
    check();
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('[Main] Stopping backend...');
    if (process.platform === 'win32') spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t']);
    else backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280, height: 840, minWidth: 900, minHeight: 600,
    title: 'BEing Bio',
    autoHideMenuBar: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true, preload: path.join(__dirname, 'preload.js') },
    show: false,
  });
  mainWindow.webContents.session.clearCache();
  mainWindow.loadURL(BACKEND_URL);
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ========== App Lifecycle ==========

app.whenReady().then(async () => {
  startBackend();
  try {
    await waitForBackend();
    console.log('[Main] Backend ready');
    createMainWindow();
  } catch (err) {
    console.error('[Main]', err.message);
    dialog.showErrorBox('Startup Failed',
      'The analysis engine could not start.\n\n' +
      '1. Close all BEing Bio windows and try again.\n' +
      '2. Restart your computer.\n\n' + err.message);
    app.quit();
  }
});

app.on('window-all-closed', () => { stopBackend(); app.quit(); });
app.on('before-quit', () => { stopBackend(); });
app.on('activate', () => { if (mainWindow === null) createMainWindow(); });
