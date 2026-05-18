const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const http = require('http');
const https = require('https');
const fs = require('fs');
const AdmZip = require('adm-zip');

let mainWindow = null;
let setupWindow = null;
let backendProcess = null;

const BACKEND_PORT = 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const MAX_RETRIES = 60;
const RETRY_INTERVAL = 1500;

const R_RUNTIME_FILE = 'r-runtime.tar.gz';
const R_RUNTIME_URLS = [
  'https://github.com/GodVfollower/auto-bioinfo/releases/download/v1.1.0/r-runtime.tar.gz',
];

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

// ====== R Setup UI ======

function createRSetupWindow() {
  setupWindow = new BrowserWindow({
    width: 600, height: 500, resizable: false,
    title: 'BEing Bio Setup',
    frame: false,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  });

  const html = getSetupHTML();
  setupWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  setupWindow.on('closed', () => { setupWindow = null; });
}

function getSetupHTML() {
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F8FAFC;display:flex;flex-direction:column;height:100vh}
.top{height:40px;background:#1E3A8A;display:flex;align-items:center;padding:0 16px;color:#fff;font-weight:600;font-size:13px}
.content{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
h1{font-size:20px;color:#1E3A8A;margin-bottom:8px}
.desc{font-size:13px;color:#6B7280;text-align:center;margin-bottom:16px;line-height:1.6}
.progress{width:320px;height:8px;background:#E5E7EB;border-radius:4px;overflow:hidden;margin:16px 0}
.progress .bar{height:100%;background:#2563EB;width:0%;transition:width .3s}
.status{font-size:12px;color:#6B7280;margin-top:8px}
.speed{font-size:11px;color:#9CA3AF;margin-top:4px}
.btn{padding:10px 24px;font-size:14px;font-weight:600;border:none;border-radius:6px;cursor:pointer;margin-top:16px}
.btn-primary{background:#2563EB;color:#fff}
.btn-retry{background:#DC2626;color:#fff;display:none}
</style></head><body>
<div class="top">BEing Bio Setup</div>
<div class="content" id="content">
  <h1>Setting Up R Engine</h1>
  <p class="desc">BEing Bio uses R with DESeq2, clusterProfiler, fgsea, and ggplot2<br>for publication-quality bioinformatics analysis.</p>
  <div class="progress"><div class="bar" id="bar"></div></div>
  <div class="status" id="status">Initializing...</div>
  <div class="speed" id="speed"></div>
  <div id="btns">
    <button class="btn btn-retry" id="retryBtn" onclick="retry()">Retry</button>
  </div>
</div>
<script>
const { ipcRenderer } = require('electron');
function update(msg, pct, spd) {
  document.getElementById('status').textContent = msg;
  document.getElementById('bar').style.width = pct + '%';
  document.getElementById('speed').textContent = spd || '';
}
function showRetry() {
  document.getElementById('retryBtn').style.display = 'inline-block';
}
function retry() {
  document.getElementById('retryBtn').style.display = 'none';
  ipcRenderer.send('r-setup-retry');
}
ipcRenderer.on('r-progress', (e, data) => {
  update(data.msg, data.pct, data.speed || '');
  if (data.done) {
    document.getElementById('btns').innerHTML = '<button class="btn btn-primary" onclick="window.close()">Launch BEing Bio</button>';
  }
  if (data.failed) {
    showRetry();
  }
});
update('Setting up R engine...', 5);
ipcRenderer.send('r-setup-start');
</script></body></html>`;
}

function sendProgress(msg, pct, extra = {}) {
  if (setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.webContents.send('r-progress', { msg, pct, ...extra });
  }
}

// ====== Download with Resume ======

function downloadWithResume(urls, dest, onProgress) {
  const urlList = Array.isArray(urls) ? [...urls] : [urls];
  return new Promise((resolve) => {
    let idx = 0;
    let totalSize = 0;
    let startByte = 0;

    try { startByte = fs.statSync(dest).size; } catch (e) {}

    function tryNext() {
      if (idx >= urlList.length) return resolve(false);
      const url = urlList[idx++];
      console.log('[Main] Downloading:', url, startByte > 0 ? `(resume from ${startByte})` : '');

      const headers = {};
      if (startByte > 0) headers['Range'] = `bytes=${startByte}-`;

      const proto = url.startsWith('https') ? https : http;
      const req = proto.get(url, { headers }, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          let location = res.headers.location;
          if (location.startsWith('/')) {
            const parsed = new URL(url);
            location = `${parsed.protocol}//${parsed.host}${location}`;
          }
          urlList.splice(idx - 1, 0, location);
          return tryNext();
        }

        if (res.statusCode === 416) {
          resolve(true);
          return;
        }

        if (res.statusCode !== 200 && res.statusCode !== 206) {
          console.log('[Main] HTTP', res.statusCode, '- trying next mirror');
          res.resume();
          return tryNext();
        }

        const contentLength = parseInt(res.headers['content-length'] || '0', 10);
        if (res.statusCode === 200) {
          totalSize = contentLength;
          startByte = 0;
        } else {
          totalSize = startByte + contentLength;
        }

        const flags = res.statusCode === 206 ? 'a' : 'w';
        const file = fs.createWriteStream(dest, { flags });
        let received = startByte;
        let lastTime = Date.now();
        let lastReceived = received;
        let staleTimer = null;

        function resetStaleTimer() {
          if (staleTimer) clearTimeout(staleTimer);
          staleTimer = setTimeout(() => {
            console.log('[Main] Download stalled, trying next mirror');
            req.destroy();
            file.close();
            startByte = received;
            tryNext();
          }, 60000);
        }

        resetStaleTimer();

        res.on('data', (chunk) => {
          received += chunk.length;
          resetStaleTimer();

          const now = Date.now();
          if (now - lastTime > 500) {
            const speed = ((received - lastReceived) / (now - lastTime) * 1000) / (1024 * 1024);
            const pct = totalSize > 0 ? Math.round((received / totalSize) * 100) : 0;
            if (onProgress) onProgress(pct, `${speed.toFixed(1)} MB/s`);
            lastTime = now;
            lastReceived = received;
          }
        });

        res.pipe(file);
        file.on('finish', () => {
          if (staleTimer) clearTimeout(staleTimer);
          file.close();
          resolve(true);
        });
        file.on('error', (e) => {
          if (staleTimer) clearTimeout(staleTimer);
          console.error('[Main] Write error:', e.message);
          file.close();
          startByte = received;
          tryNext();
        });
      });

      req.on('error', (e) => {
        console.error('[Main] Download error:', e.message);
        startByte = startByte;
        tryNext();
      });
    }
    tryNext();
  });
}

// ====== Large ZIP Extraction ======

function extractArchive(archivePath, destDir) {
  return new Promise((resolve) => {
    console.log('[Main] Extracting with system tar...');
    const proc = spawn('tar', ['-xzf', archivePath, '-C', destDir]);
    proc.stderr.on('data', d => console.error('[tar]', d.toString().trim()));
    proc.on('close', code => {
      resolve(code === 0);
    });
    proc.on('error', () => {
      resolve(false);
    });
  });
}

// ====== R Setup Logic ======

async function setupR() {
  if (rReady()) {
    console.log('[Main] R engine already installed');
    return true;
  }

  const rBase = path.join(getRuntimeBase(), 'R');
  const downloadPath = path.join(app.getPath('temp'), R_RUNTIME_FILE);

  sendProgress('Downloading R analysis engine...', 10);

  const ok = await downloadWithResume(R_RUNTIME_URLS, downloadPath, (pct, speed) => {
    const mappedPct = 10 + Math.round(pct * 0.6);
    sendProgress(`Downloading R engine... ${pct}%`, mappedPct, { speed });
  });

  if (!ok) {
    console.error('[Main] R download failed');
    sendProgress('Download failed. Please check your network.', 10, { failed: true });
    return false;
  }

  console.log('[Main] R runtime downloaded');
  sendProgress('Extracting R engine (please wait)...', 75);

  fs.mkdirSync(rBase, { recursive: true });
  const extracted = await extractArchive(downloadPath, rBase);

  if (!extracted) {
    console.error('[Main] R extraction failed');
    sendProgress('Extraction failed.', 75, { failed: true });
    return false;
  }

  try { fs.unlinkSync(downloadPath); } catch (e) {}

  if (!findR()) {
    console.error('[Main] R not found after extraction');
    sendProgress('Setup failed - R engine not found after extraction.', 80, { failed: true });
    return false;
  }

  console.log('[Main] R engine ready');
  sendProgress('Setup complete!', 100, { done: true });
  return true;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

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

// ====== IPC ======

ipcMain.on('r-setup-start', () => {
  // Setup is already triggered from app.whenReady, this is just a UI signal
});

ipcMain.on('r-setup-retry', async () => {
  const ok = await setupR();
  if (ok && setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.close();
    createMainWindow();
  }
});

// ====== App Lifecycle ======

app.whenReady().then(async () => {
  startBackend();
  try { await waitForBackend(); console.log('[Main] Backend ready'); }
  catch (err) { dialog.showErrorBox('Startup Failed', err.message); app.quit(); return; }

  if (!rReady()) {
    createRSetupWindow();
    const ok = await setupR();
    if (!ok) {
      // Don't quit - let user retry via the setup window button
      return;
    }
    if (setupWindow && !setupWindow.isDestroyed()) setupWindow.close();
  }

  createMainWindow();
});

app.on('window-all-closed', () => { stopBackend(); app.quit(); });
app.on('before-quit', () => { stopBackend(); });
