// Quality Control Page
function renderQualityControl() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('qc.desc')}</div>
    <div class="card">
      <div class="card-header"><h3>${t('qc.title')}</h3></div>
      <p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:12px">${t('qc.desc2')}</p>
      <button class="btn btn-primary" id="btnRunQC" onclick="runQC()">${t('qc.run_btn')}</button>
      <button class="btn btn-secondary" style="margin-left:8px" onclick="window.location.hash = 'data-import'">${t('qc.back')}</button>
    </div>
    <div id="qcResult" style="display:none"></div>
    <div id="qcActions" style="display:none;margin-top:16px">
      <div class="card">
        <div class="card-header"><h3>${t('data.next_steps')}</h3></div>
        <div style="display:flex;gap:10px">
          <button class="btn btn-primary" onclick="window.location.hash = 'differential'">${t('qc.proceed_diff')}</button>
          <button class="btn btn-secondary" onclick="window.location.hash = 'data-import'">${t('qc.reimport')}</button>
        </div>
      </div>
    </div>
  `;
}

async function runQC() {
  const t = (k) => I18N.t(k);
  const btn = document.getElementById('btnRunQC');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('qc.running');
  const resultEl = document.getElementById('qcResult');
  resultEl.style.display = 'block';
  resultEl.innerHTML = '<div class="card"><h3>' + t('qc.running') + '</h3><div class="progress-bar"><div class="fill" style="width:0%"></div></div><p style="font-size:13px;color:var(--ab-text-secondary);margin-top:8px" id="qcStep">Starting...</p></div>';
  try {
    const steps = [t('qc.check_names'),t('qc.check_missing'),t('qc.check_dupes'),t('qc.check_numeric'),t('qc.check_outliers'),t('qc.check_log2'),t('qc.check_group')];
    const fill = document.querySelector('#qcResult .fill');
    const stepEl = document.getElementById('qcStep');
    for (let i = 0; i < steps.length; i++) {
      stepEl.textContent = t('qc.checking') + ': ' + steps[i];
      fill.style.width = ((i+1)/steps.length*100)+'%';
      await sleep(300);
    }
    const data = await API.qcRun(window._loadedData?.project_id || 'current');
    renderQCResult(data);
    document.getElementById('qcActions').style.display = 'block';
  } catch (e) { resultEl.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
  finally { btn.disabled = false; btn.textContent = t('qc.run_btn'); }
}

function renderQCResult(data) {
  const t = (k) => I18N.t(k);
  const el = document.getElementById('qcResult');
  const checks = data.checks || [];
  let checksHTML = '';
  checks.forEach(c => {
    const icon = c.status === 'pass' ? 'v' : c.status === 'warn' ? '!' : 'x';
    checksHTML += '<tr><td>' + icon + '</td><td>' + c.name + '</td><td>' + c.message + '</td><td>' + (c.detail||'-') + '</td></tr>';
  });
  el.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>${t('qc.results')}</h3><span class="badge ${(data.passed||0)===checks.length?'badge-success':'badge-warning'}">${data.passed||0}/${checks.length} ${t('qc.passed')}</span></div>
      <table class="data-table"><thead><tr><th></th><th>Check</th><th>Result</th><th>Detail</th></tr></thead><tbody>${checksHTML}</tbody></table>
      ${data.warnings?.length ? '<div class="alert alert-warning" style="margin-top:12px">' + data.warnings.join('<br>') + '</div>' : ''}
      ${data.passed === checks.length ? '<div class="alert alert-success" style="margin-top:12px">' + t('qc.all_passed') + '</div>' : ''}
    </div>
  `;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
