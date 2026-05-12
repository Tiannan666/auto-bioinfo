// API Layer — Unified backend communication
const API = {
  base: '',

  async get(url) {
    const r = await fetch(this.base + url);
    if (!r.ok) throw new Error(`API ${r.status}: ${url}`);
    return r.json();
  },

  async post(url, data) {
    const r = await fetch(this.base + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error(`API ${r.status}: ${url}`);
    return r.json();
  },

  // Config
  configStatus: () => API.get('/api/config/status'),
  configSave: (key) => API.post('/api/config', { deepseek_api_key: key }),

  // Health
  health: () => API.get('/api/health'),

  // Data v2
  dataDetect: (path) => API.post('/api/v2/data/detect', { path }),
  dataLoad: (path) => API.post('/api/v2/data/load', { path }),

  // QC v2
  qcRun: (projectId) => API.post('/api/v2/qc/run', { project_id: projectId }),

  // Analysis v2
  diffAnalysis: (params) => API.post('/api/v2/analysis/differential', params),
  enrichment: (params) => API.post('/api/v2/analysis/enrichment', params),
  gsea: (params) => API.post('/api/v2/analysis/gsea', params),

  // Plots v2
  plotsGenerate: (params) => API.post('/api/v2/plots/generate', params),
  plotsExport: (params) => API.post('/api/v2/plots/export', params),

  // Intelligence v2
  interpretation: (params) => API.post('/api/v2/interpretation/generate', params),
  storyline: (params) => API.post('/api/v2/storyline/generate', params),

  // Report v2
  reportExport: (params) => API.post('/api/v2/report/export', params),

  // Projects v2
  projectsList: () => API.get('/api/v2/projects/list'),
  taskStatus: (taskId) => API.get('/api/v2/tasks/status?task_id=' + taskId),
};

// Settings
async function checkConfig() {
  try {
    const d = await API.configStatus();
    const el = document.getElementById('keyStatus');
    if (d.has_key) {
      el.innerHTML = '<span style="color:var(--ab-success)">●</span> API Ready';
    } else {
      el.innerHTML = '<span style="color:var(--ab-warning)">●</span> No API Key';
      openSettings();
    }
  } catch (e) { /* ignore */ }
}

function openSettings() {
  document.getElementById('settingsModal').classList.add('open');
  document.getElementById('apiKey').focus();
  document.getElementById('saveStatus').style.display = 'none';
  // Set language selector to current
  document.getElementById('langSelect').value = I18N.lang;
}

function switchLanguage(lang) {
  I18N.setLang(lang);
}

function closeSettings() {
  document.getElementById('settingsModal').classList.remove('open');
}

async function saveSettings() {
  const key = document.getElementById('apiKey').value.trim();
  if (!key) return;
  const st = document.getElementById('saveStatus');
  st.style.display = 'block'; st.textContent = 'Saving...'; st.style.color = 'var(--ab-text-secondary)';
  try {
    await API.configSave(key);
    st.textContent = 'Saved!'; st.style.color = 'var(--ab-success)';
    document.getElementById('keyStatus').innerHTML = '<span style="color:var(--ab-success)">●</span> API Ready';
    setTimeout(closeSettings, 800);
  } catch (e) {
    st.textContent = 'Failed: ' + e.message; st.style.color = 'var(--ab-error)';
  }
}
