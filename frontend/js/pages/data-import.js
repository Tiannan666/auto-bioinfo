// Data Import Page
function renderDataImport() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('data.desc')}</div>
    <div class="card">
      <div class="card-header"><h3>${t('data.source')}</h3></div>
      <div class="form-group">
        <label class="form-label">${t('data.path_label')}</label>
        <div style="display:flex;gap:8px">
          <input type="text" class="form-input" id="dataPath" placeholder="${t('data.path_placeholder')}" style="flex:1">
          <button class="btn btn-primary" onclick="detectData()">${t('data.detect_btn')}</button>
        </div>
        <div class="form-hint">${t('data.hint')}</div>
      </div>
    </div>
    <div id="detectResult" style="display:none"></div>
    <div id="detectActions" style="display:none;margin-top:16px">
      <div class="card">
        <div class="card-header"><h3>${t('data.next_steps')}</h3></div>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <button class="btn btn-primary" onclick="loadAndProceed()">${t('data.load_continue')}</button>
          <button class="btn btn-secondary" onclick="App.navigate('quality-control')">${t('data.skip_qc')}</button>
          <button class="btn btn-outline" onclick="resetImport()">${t('data.reset')}</button>
        </div>
      </div>
    </div>
  `;
}

async function detectData() {
  const t = (k) => I18N.t(k);
  const path = document.getElementById('dataPath').value.trim();
  if (!path) return alert('Please enter a file path or GEO ID.');
  const resultEl = document.getElementById('detectResult');
  resultEl.style.display = 'block';
  resultEl.innerHTML = '<div class="card"><div class="spinner"></div> ' + t('data.detecting') + '</div>';
  try {
    const data = await API.dataDetect(path);
    if (data.error) { resultEl.innerHTML = '<div class="alert alert-error">' + data.error + '</div>'; return; }
    renderDetectionResult(data);
    document.getElementById('detectActions').style.display = 'block';
  } catch (e) {
    resultEl.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>';
  }
}

function renderDetectionResult(data) {
  const t = (k) => I18N.t(k);
  const issues = data.issues || [];
  const issueHTML = issues.length ? issues.map(i => '<li style="color:' + (i.level==='error'?'var(--ab-error)':'var(--ab-warning)') + '">' + (i.level==='error'?'x':'!') + ' ' + i.message + '</li>').join('')
    : '<li style="color:var(--ab-success)">v ' + t('data.no_issues') + '</li>';
  const el = document.getElementById('detectResult');
  el.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>${t('data.detection_result')}</h3><span class="badge ${issues.some(i=>i.level==='error')?'badge-warning':'badge-success'}">${data.data_type||'Unknown'}</span></div>
      <div class="stat-cards">
        <div class="stat-card"><div class="stat-value">${data.n_samples||'-'}</div><div class="stat-label">${t('data.samples')}</div></div>
        <div class="stat-card"><div class="stat-value">${data.n_genes||'-'}</div><div class="stat-label">${t('data.genes')}</div></div>
        <div class="stat-card"><div class="stat-value">${data.n_groups||'-'}</div><div class="stat-label">${t('data.groups')}</div></div>
        <div class="stat-card"><div class="stat-value">${data.file_type||'-'}</div><div class="stat-label">${t('data.file_type')}</div></div>
      </div>
      ${data.groups ? '<p style="font-size:13px;margin-bottom:8px"><strong>Groups:</strong> ' + data.groups.join(', ') + '</p>' : ''}
      <div style="margin-top:8px"><strong>Issues:</strong><ul style="font-size:13px;padding-left:18px;margin-top:4px">${issueHTML}</ul></div>
    </div>
  `;
  window._detectedData = data;
}

async function loadAndProceed() {
  if (!window._detectedData) return;
  const path = document.getElementById('dataPath').value.trim();
  try {
    const data = await API.dataLoad(path);
    window._loadedData = data;
    const projects = JSON.parse(localStorage.getItem('bioinfo_projects') || '[]');
    projects.push({ path, timestamp: new Date().toISOString(), dataType: window._detectedData.data_type });
    localStorage.setItem('bioinfo_projects', JSON.stringify(projects));
    App.navigate('quality-control');
  } catch (e) { alert('Load failed: ' + e.message); }
}

function resetImport() {
  document.getElementById('dataPath').value = '';
  document.getElementById('detectResult').style.display = 'none';
  document.getElementById('detectActions').style.display = 'none';
  window._detectedData = null;
  window._loadedData = null;
}
