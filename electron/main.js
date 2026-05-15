const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const http = require('http');
const https = require('https');
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

// ========== R Detection & Setup ==========

function findRscript() {
  // Check common R installation paths
  const paths = [
    path.join(process.env['ProgramFiles'] || 'C:/Program Files', 'R'),
    'C:/Program Files/R',
    path.join(app.getPath('userData'), 'runtime', 'R'),
  ];
  for (const base of paths) {
    if (!fs.existsSync(base)) continue;
    // Find all R versions and return the latest
    const dirs = fs.readdirSync(base).filter(d => d.startsWith('R-')).sort().reverse();
    for (const d of dirs) {
      const rscript = path.join(base, d, 'bin', 'Rscript.exe');
      if (fs.existsSync(rscript)) {
        // Set R_HOME for the backend
        process.env.R_HOME = path.join(base, d);
        return rscript;
      }
    }
  }
  return null;
}

async function ensureR() {
  // Returns true if R with Bioconductor is available
  const rscript = findRscript();
  if (!rscript) {
    return await promptInstallR();
  }
  if (!fs.existsSync(rscript)) return await promptInstallR();

  const markerFile = path.join(path.dirname(path.dirname(rscript)), '.being_bio_packages_installed');
  if (!fs.existsSync(markerFile)) {
    return await installBioconductor(rscript, markerFile);
  }
  console.log('[Main] R ready:', rscript);
  return true;
}

async function promptInstallR() {
  return new Promise((resolve) => {
    const win = new BrowserWindow({
      width: 560, height: 420, resizable: false,
      title: 'BEing Bio - R Setup',
      frame: false,
      webPreferences: { nodeIntegration: true, contextIsolation: false },
    });
    win.loadURL(`data:text/html,${encodeURIComponent(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{font-family:-apple-system,sans-serif;background:#F8FAFC;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;padding:20px;text-align:center}
h1{color:#1E3A8A;font-size:20px;margin-bottom:8px}
p{color:#6B7280;font-size:13px;margin-bottom:20px;line-height:1.6}
.btn{display:block;width:280px;padding:12px 20px;margin:8px auto;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
.btn-primary{background:#2563EB;color:#fff}
.btn-primary:hover{background:#1D4ED8}
.btn-secondary{background:#fff;color:#6B7280;border:1px solid #E5E7EB}
.btn-secondary:hover{background:#F8FAFC}
.status{font-size:12px;color:#16A34A;margin-top:12px;display:none}
</style></head><body>
<h1>R Engine Required</h1>
<p>BEing Bio uses R for DESeq2, clusterProfiler, fgsea, and ggplot2.<br>
These are the gold-standard tools for publication-quality analysis.</p>
<p style="font-size:12px;color:#9CA3AF">Without R: basic analysis only (t-test, hypergeometric).<br>
With R: full DESeq2/edgeR/limma, clusterProfiler GO/KEGG, fgsea, ggplot2.</p>
<div id="btns">
<button class="btn btn-primary" id="installBtn">Download & Install R</button>
<button class="btn btn-secondary" id="skipBtn">Skip (basic analysis only)</button>
</div>
<div class="status" id="status"></div>
<script>
const { shell } = require('electron');
document.getElementById('installBtn').onclick = function() {
  document.getElementById('status').style.display='block';
  document.getElementById('status').textContent='Opening R download page...';
  shell.openExternal('https://cloud.r-project.org/bin/windows/base/');
  document.getElementById('installBtn').textContent='Re-check R Installation';
  document.getElementById('installBtn').onclick = function() {
    document.getElementById('status').textContent='Checking...';
    const { execSync } = require('child_process');
    try {
      const r = execSync('Rscript.exe -e "cat(\\"OK\\")"', {timeout:5000}).toString();
      if (r.includes('OK')) { window.close(); return true; }
    } catch(e) {}
    document.getElementById('status').textContent='R not detected. Please install R first (check Downloads folder).';
  };
};
document.getElementById('skipBtn').onclick = function() { window.close(); };
</script></body></html>`)}`);
    win.on('closed', () => resolve(false));
    // Don't block main window
  });
}

async function installBioconductor(rscript, markerFile) {
  console.log('[Main] Installing Bioconductor packages...');
  return new Promise((resolve) => {
    const proc = spawn(rscript, ['--no-save', '-e',
      'options(repos=c(CRAN="https://cloud.r-project.org")); ' +
      'if(!require("BiocManager",quietly=TRUE)) install.packages("BiocManager",quiet=TRUE); ' +
      'BiocManager::install(c("DESeq2","edgeR","limma","clusterProfiler","fgsea","ggplot2","org.Hs.eg.db","enrichplot"),update=FALSE,ask=FALSE,quiet=TRUE); ' +
      'writeLines("OK", "' + markerFile.replace(/\\/g, '/') + '")'
    ], { stdio: 'ignore' });
    proc.on('close', (code) => {
      console.log('[Main] Bioconductor install done, code:', code);
      resolve(code === 0);
    });
    // Bioconductor install can take a while. Don't block the app.
    // Analysis will work once packages are installed.
    setTimeout(() => resolve(false), 60000); // 60s timeout, will use fallback
  });
}

// ========== App Lifecycle ==========

app.whenReady().then(async () => {
  startBackend();
  ensureR(); // Start R setup in parallel, don't block startup

  try {
    await waitForBackend();
    console.log('[Main] Backend ready');
    createMainWindow();
  } catch (err) {
    console.error('[Main]', err.message);
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
