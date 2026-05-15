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
      <div id="dropZone" style="margin-top:16px;border:2px dashed var(--ab-border);border-radius:8px;padding:32px;text-align:center;transition:all .2s;background:var(--ab-light-bg)">
        <div style="font-size:32px;margin-bottom:8px">&#128194;</div>
        <p style="font-size:14px;color:var(--ab-text-secondary);margin:0">Drag & drop your data file here</p>
        <p style="font-size:12px;color:var(--ab-text-secondary);margin:4px 0 0 0">CSV, TSV, TXT, Excel, SOFT, MINiML, or GZ</p>
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

function init_data_import() {
  var dropZone = document.getElementById('dropZone');
  if (!dropZone) return;

  dropZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.style.borderColor = 'var(--ab-btn)';
    this.style.background = '#DBEAFE';
  });

  dropZone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.style.borderColor = 'var(--ab-border)';
    this.style.background = 'var(--ab-light-bg)';
  });

  dropZone.addEventListener('drop', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.style.borderColor = 'var(--ab-border)';
    this.style.background = 'var(--ab-light-bg)';

    var files = e.dataTransfer.files;
    if (files && files.length > 0) {
      var path = files[0].path || files[0].name;
      document.getElementById('dataPath').value = path;
      // Show feedback
      var p = this.querySelector('p');
      if (p) p.textContent = 'File: ' + (files[0].name || path.split('/').pop().split('\\').pop());
      // Auto-detect
      setTimeout(function() { detectData(); }, 300);
    }
  });
}

async function detectData() {
  const t = (k) => I18N.t(k);
  var path = document.getElementById('dataPath').value.trim();
  if (!path) return alert('Please enter a file path or GEO ID.');
  var resultEl = document.getElementById('detectResult');
  resultEl.style.display = 'block';
  resultEl.innerHTML = '<div class="card"><div class="spinner"></div> ' + t('data.detecting') + '</div>';
  try {
    var data = await API.dataDetect(path);
    if (data.error) { resultEl.innerHTML = '<div class="alert alert-error">' + data.error + '</div>'; return; }
    renderDetectionResult(data);
    document.getElementById('detectActions').style.display = 'block';
  } catch (e) {
    resultEl.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>';
  }
}

function renderDetectionResult(data) {
  var t = (k) => I18N.t(k);
  var issues = data.issues || [];
  var issueHTML = issues.length ? issues.map(function(i) { return '<li style="color:' + (i.level==='error'?'var(--ab-error)':'var(--ab-warning)') + '">' + (i.level==='error'?'!':'!') + ' ' + i.message + '</li>'; }).join('')
    : '<li style="color:var(--ab-success)">' + t('data.no_issues') + '</li>';
  var el = document.getElementById('detectResult');
  el.innerHTML = '<div class="card">' +
    '<div class="card-header"><h3>' + t('data.detection_result') + '</h3><span class="badge ' + (issues.some(function(i){return i.level==='error'})?'badge-warning':'badge-success') + '">' + (data.data_type||'Unknown') + '</span></div>' +
    '<div class="stat-cards">' +
      '<div class="stat-card"><div class="stat-value">' + (data.n_samples||'-') + '</div><div class="stat-label">' + t('data.samples') + '</div></div>' +
      '<div class="stat-card"><div class="stat-value">' + (data.n_genes||'-') + '</div><div class="stat-label">' + t('data.genes') + '</div></div>' +
      '<div class="stat-card"><div class="stat-value">' + (data.n_groups||'-') + '</div><div class="stat-label">' + t('data.groups') + '</div></div>' +
      '<div class="stat-card"><div class="stat-value">' + (data.file_type||'-') + '</div><div class="stat-label">' + t('data.file_type') + '</div></div>' +
    '</div>' +
    (data.groups ? '<p style="font-size:13px;margin-bottom:8px"><strong>Groups:</strong> ' + data.groups.join(', ') + '</p>' : '') +
    '<div style="margin-top:8px"><strong>Issues:</strong><ul style="font-size:13px;padding-left:18px;margin-top:4px">' + issueHTML + '</ul></div>' +
    '</div>';
  window._detectedData = data;
}

async function loadAndProceed() {
  var path = document.getElementById('dataPath').value.trim();
  if (!window._detectedData) return;
  try {
    var data = await API.dataLoad(path);
    window._loadedData = data;
    var projects = JSON.parse(localStorage.getItem('bioinfo_projects') || '[]');
    projects.push({ path: path, timestamp: new Date().toISOString(), dataType: window._detectedData.data_type });
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
  var p = document.querySelector('#dropZone p');
  if (p) p.textContent = 'Drag & drop your data file here';
}
