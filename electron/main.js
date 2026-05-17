const { app, BrowserWindow, dialog } = require('electron');
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
const R_VERSION = '4.6.0';
const R_INSTALLER = `R-${R_VERSION}-win.exe`;
const R_URL = `https://cloud.r-project.org/bin/windows/base/old/${R_VERSION}/${R_INSTALLER}`;
const BIOC_PACKAGES = ['DESeq2','edgeR','limma','clusterProfiler','fgsea','ggplot2','org.Hs.eg.db','enrichplot'];

// ====== R Detection ======

function findR() {
  const bases = [path.join(process.env['ProgramFiles'] || 'C:/Program Files', 'R'), 'C:/Program Files/R'];
  for (const base of bases) {
    if (!fs.existsSync(base)) continue;
    const dirs = fs.readdirSync(base).filter(d => d.startsWith('R-')).sort().reverse();
    for (const d of dirs) {
      const rscript = path.join(base, d, 'bin', 'Rscript.exe');
      if (fs.existsSync(rscript)) {
        return { home: path.join(base, d), rscript: rscript };
      }
    }
  }
  return null;
}

function rBiocReady() {
  const r = findR();
  if (!r) return false;
  try {
    const out = execSync(`"${r.rscript}" -e "cat(require('DESeq2')&&require('clusterProfiler')&&require('fgsea')&&require('ggplot2'))"`, { timeout: 15000, encoding: 'utf8' });
    return out.includes('TRUE');
  } catch (e) { return false; }
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
.btn{padding:10px 24px;font-size:14px;font-weight:600;border:none;border-radius:6px;cursor:pointer;margin-top:16px}
.btn-primary{background:#2563EB;color:#fff}
.btn-secondary{background:#fff;color:#6B7280;border:1px solid #E5E7EB;margin-left:8px}
</style></head><body>
<div class="top">BEing Bio Setup</div>
<div class="content" id="content">
  <h1>Setting Up R Engine</h1>
  <p class="desc">BEing Bio uses R with DESeq2, clusterProfiler, fgsea, and ggplot2<br>for publication-quality bioinformatics analysis.</p>
  <div class="progress"><div class="bar" id="bar"></div></div>
  <div class="status" id="status">Checking R installation...</div>
  <div id="btns"></div>
</div>
<script>
const { ipcRenderer } = require('electron');
const steps = ['Downloading R','Installing R','Installing Bioconductor packages','Done'];
let current = 0;
function update(msg, pct) {
  document.getElementById('status').textContent = msg;
  document.getElementById('bar').style.width = pct + '%';
}
// Start immediately
update('Setting up R engine...', 5);
ipcRenderer.send('r-setup-start');
ipcRenderer.on('r-progress', (e, data) => {
  update(data.msg, data.pct);
  if (data.done) {
    document.getElementById('btns').innerHTML = '<button class="btn btn-primary" onclick="window.close()">Launch BEing Bio</button>';
  }
});
</script></body></html>`;
}

// ====== R Setup Logic ======

async function setupR() {
  if (rBiocReady()) {
    console.log('[Main] R + Bioconductor ready');
    return true;
  }

  const r = findR();
  if (!r) {
    // Download and install R
    const downloadPath = path.join(app.getPath('temp'), R_INSTALLER);

    if (setupWindow && !setupWindow.isDestroyed()) {
      setupWindow.webContents.send('r-progress', { msg: 'Downloading R (87MB)...', pct: 10 });
    }

    await downloadFile(R_URL, downloadPath);
    console.log('[Main] R downloaded');

    if (setupWindow && !setupWindow.isDestroyed()) {
      setupWindow.webContents.send('r-progress', { msg: 'Installing R silently...', pct: 30 });
    }

    try {
      execSync(`"${downloadPath}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART`, { timeout: 120000 });
    } catch (e) { /* returns non-zero but usually succeeds */ }

    // Wait for R to appear
    for (let i = 0; i < 30; i++) {
      if (findR()) break;
      await sleep(2000);
    }
  }

  // Install Bioconductor packages
  const rAfter = findR();
  if (!rAfter) {
    console.log('[Main] R install failed');
    return false;
  }

  if (setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.webContents.send('r-progress', { msg: 'Installing Bioconductor packages (2-5 min)...', pct: 50 });
  }

  const biocScript = `
options(repos=c(CRAN="https://cloud.r-project.org"))
if(!require("BiocManager", quietly=TRUE)) install.packages("BiocManager", quiet=TRUE)
BiocManager::install(c("${BIOC_PACKAGES.join('","')}"), update=FALSE, ask=FALSE, quiet=TRUE)
cat("BIOC_DONE\\n")
`;

  return new Promise((resolve) => {
    const proc = spawn(rAfter.rscript, ['--no-save', '-e', biocScript], {
      env: { ...process.env, R_HOME: rAfter.home },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    proc.stdout.on('data', d => {
      const txt = d.toString();
      if (txt.includes('BIOC_DONE')) {
        console.log('[Main] Bioconductor installed');
        if (setupWindow && !setupWindow.isDestroyed()) {
          setupWindow.webContents.send('r-progress', { msg: 'Setup complete!', pct: 100, done: true });
        }
        resolve(true);
      }
    });
    proc.on('close', (code) => {
      resolve(code === 0);
    });
    setTimeout(() => resolve(false), 600000); // 10 min timeout
  });
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const proto = url.startsWith('https') ? https : http;
    proto.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return downloadFile(res.headers.location, dest).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', reject);
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ====== Python Runtime ======

function getProjectRoot() {
  return app.isPackaged ? path.dirname(app.getPath('exe')) : path.join(__dirname, '..');
}

function getRuntimePython() {
  const userData = app.getPath('userData');
  const runtimeDir = path.join(userData, 'runtime');
  const pythonExe = path.join(runtimeDir, 'python', 'python.exe');
  if (fs.existsSync(pythonExe)) return pythonExe;

  const zipPath = app.isPackaged
    ? path.join(process.resourcesPath, 'runtime.zip')
    : path.join(getProjectRoot(), 'runtime.zip');
  if (!fs.existsSync(zipPath)) return null;

  console.log('[Main] Extracting Python runtime...');
  try {
    fs.mkdirSync(userData, { recursive: true });
    new AdmZip(zipPath).extractAllTo(userData, true);
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
  const r = findR();
  const env = { ...process.env };
  delete env.ELECTRON_RUN_AS_NODE;
  if (r) env.R_HOME = r.home;

  const args = [...backend.args, '--port', String(BACKEND_PORT), '--data-dir', dataDir];
  console.log('[Main] Starting backend:', backend.cmd, args.join(' '));

  backendProcess = spawn(backend.cmd, args, {
    cwd: app.isPackaged ? path.dirname(app.getPath('exe')) : getProjectRoot(),
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

const { ipcMain } = require('electron');
ipcMain.on('r-setup-start', async () => {
  await setupR();
});

// ====== App Lifecycle ======

app.whenReady().then(async () => {
  // Start backend first (Python doesn't depend on R)
  startBackend();

  // Check R in background — show setup window if needed
  const rReady = rBiocReady();
  if (!rReady) {
    createRSetupWindow();
    // Start R setup in background, don't block
    setupR().then(ok => {
      console.log('[Main] R setup result:', ok);
      if (setupWindow && !setupWindow.isDestroyed()) {
        setupWindow.webContents.send('r-progress', { msg: ok ? 'R ready! Restart to use full analysis.' : 'R setup incomplete. Basic analysis only.', pct: ok ? 100 : 30, done: true });
      }
    });
  }

  try {
    await waitForBackend();
    console.log('[Main] Backend ready');
    createMainWindow();
  } catch (err) {
    dialog.showErrorBox('Startup Failed', err.message);
    app.quit();
  }
});

app.on('window-all-closed', () => { stopBackend(); app.quit(); });
app.on('before-quit', () => { stopBackend(); });
