const { app, BrowserWindow, dialog } = require('electron');
const { spawn, execSync } = require('child_process');
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

// R runtime is now expected at runtime/R/ — no auto-download

// ====== Path Helpers ======

function getProjectRoot() {
  return app.isPackaged ? path.dirname(app.getPath('exe')) : path.join(__dirname, '..');
}

function getRuntimeBase() {
  return path.join(getProjectRoot(), 'runtime');
}

function getDataDir() {
  return path.join(getProjectRoot(), 'data');
}

// ====== R Detection ======

function findR() {
  const rBase = path.join(getRuntimeBase(), 'R');
  if (!fs.existsSync(rBase)) return null;

  const direct = path.join(rBase, 'bin', 'Rscript.exe');
  if (fs.existsSync(direct)) return { home: rBase, rscript: direct };

  try {
    const dirs = fs.readdirSync(rBase).filter(d => d.startsWith('R-')).sort().reverse();
    for (const d of dirs) {
      const rscript = path.join(rBase, d, 'bin', 'Rscript.exe');
      if (fs.existsSync(rscript)) return { home: path.join(rBase, d), rscript };
    }
  } catch (e) {}
  return null;
}

function rReady() {
  return !!findR();
}

// ====== R Missing Dialog ======

async function waitForR() {
  // Loop until R is found or user chooses to exit
  while (!rReady()) {
    const rPath = path.join(getRuntimeBase(), 'R');
    const { response } = await dialog.showMessageBox({
      type: 'warning',
      title: 'R 环境缺失',
      message: '未检测到 R 运行环境',
      detail: `请将 R 运行时解压到以下目录，然后点击「重试」：\n\n${rPath}\n\n` +
              `目录中需要包含：\n` +
              `  bin/Rscript.exe\n` +
              `  library/  (含 DESeq2、clusterProfiler 等 Bioconductor 包)\n\n` +
              `R 运行时可从 GitHub Releases 下载，或从其他机器复制。`,
      buttons: ['退出应用', '重试'],
      defaultId: 1,
      cancelId: 0,
    });
    if (response !== 1) return false;
  }
  return true;
}





// ====== Python Runtime ======

function getRuntimePython() {
  const runtimeDir = getRuntimeBase();
  const pythonExe = path.join(runtimeDir, 'python', 'python.exe');
  if (fs.existsSync(pythonExe)) return pythonExe;

  const zipPath = app.isPackaged
    ? path.join(process.resourcesPath, 'runtime.zip')
    : path.join(getProjectRoot(), 'runtime.zip');
  if (!fs.existsSync(zipPath)) return null;

  console.log('[Main] Extracting Python runtime...');
  try {
    const parentDir = getProjectRoot();
    fs.mkdirSync(parentDir, { recursive: true });
    new AdmZip(zipPath).extractAllTo(parentDir, true);
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
  const dataDir = getDataDir();
  fs.mkdirSync(dataDir, { recursive: true });

  const r = findR();
  const env = { ...process.env };
  delete env.ELECTRON_RUN_AS_NODE;
  if (r) env.R_HOME = r.home;

  const args = [...backend.args, '--port', String(BACKEND_PORT), '--data-dir', dataDir];
  console.log('[Main] Starting backend:', backend.cmd, args.join(' '));

  backendProcess = spawn(backend.cmd, args, {
    cwd: getProjectRoot(),
    stdio: ['ignore', 'pipe', 'pipe'],
    env: env,
  });
  backendProcess.stdout.on('data', d => console.log('[Backend]', d.toString().trim()));
  backendProcess.stderr.on('data', d => console.log('[Backend]', d.toString().trim()));
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
    function retry() { if (--retries <= 0) { reject(new Error('Backend failed')); return; } setTimeout(check, RETRY_INTERVAL); }
    check();
  });
}

function stopBackend() {
  if (backendProcess) {
    spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t']);
    backendProcess = null;
  }
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280, height: 840, minWidth: 900, minHeight: 600,
    title: 'BEing Bio', autoHideMenuBar: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true, preload: path.join(__dirname, 'preload.js') },
    show: false,
  });
  mainWindow.webContents.session.clearCache();
  mainWindow.loadURL(BACKEND_URL);
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ====== App Lifecycle ======

app.whenReady().then(async () => {
  startBackend();
  try { await waitForBackend(); console.log('[Main] Backend ready'); }
  catch (err) { dialog.showErrorBox('Startup Failed', err.message); app.quit(); return; }

  // Check R runtime — if missing, show dialog until placed or user exits
  console.log('[Main] Checking R runtime...');
  const rOk = await waitForR();
  if (!rOk) { app.quit(); return; }

  createMainWindow();
});

app.on('window-all-closed', () => { stopBackend(); app.quit(); });
app.on('before-quit', () => { stopBackend(); });
