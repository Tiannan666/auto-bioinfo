// LASSO Biomarker Selection Page
function renderLasso() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('lasso.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">${t('lasso.params')}</h3>
        <div class="form-group"><label class="form-label">${t('lasso.group1')}</label>
          <input type="text" class="form-input" id="lassoGroup1" placeholder="e.g. Tumor, Disease"></div>
        <div class="form-group"><label class="form-label">${t('lasso.group2')}</label>
          <input type="text" class="form-input" id="lassoGroup2" placeholder="e.g. Normal, Control"></div>
        <div class="form-group"><label class="form-label">${t('lasso.n_features')}</label>
          <input type="number" class="form-input" id="lassoNFeatures" value="50" min="5" max="200"></div>
        <p style="font-size:11px;color:var(--ab-text-secondary);margin:8px 0;line-height:1.5">${t('lasso.info')}</p>
        <button class="btn btn-primary" id="btnRunLasso" onclick="runLasso()" style="width:100%;margin-top:16px">${t('lasso.run')}</button>
      </div>
      <div class="split-main">
        <div id="lassoResult" class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('lasso.placeholder')}</p></div>
      </div>
    </div>
  `;
}

async function runLasso() {
  const t = (k) => I18N.t(k);
  const btn = document.getElementById('btnRunLasso');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('qc.running');
  const el = document.getElementById('lassoResult');
  el.innerHTML = '<div class="spinner"></div> ' + t('qc.running');
  try {
    const data = await API.lasso({
      group1: document.getElementById('lassoGroup1').value.trim(),
      group2: document.getElementById('lassoGroup2').value.trim(),
      n_features: parseInt(document.getElementById('lassoNFeatures').value),
      project_id: window._loadedData?.project_id || 'current',
    });
    if (data.error) {
      el.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
    } else {
      renderLassoResult(data);
      window._lassoResult = data;
    }
  } catch(e) {
    el.innerHTML = '<div class="alert alert-error">' + e.message + '</div>';
  } finally {
    btn.disabled = false; btn.textContent = t('lasso.run');
  }
}

function renderLassoResult(data) {
  const t = (k) => I18N.t(k);
  const el = document.getElementById('lassoResult');
  const biomarkers = data.biomarkers || [];

  let html = '<div class="card-header"><h3>' + t('lasso.result_title') + '</h3>' +
    '<span class="badge badge-info">' + data.n_selected + ' biomarkers selected</span></div>';

  // Performance metrics
  html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0">';
  html += '<div class="card" style="padding:12px;text-align:center"><div style="font-size:11px;color:var(--ab-text-secondary)">AUC</div><div style="font-size:22px;font-weight:700;color:var(--ab-primary)">' + data.cv_auc.toFixed(3) + '</div></div>';
  html += '<div class="card" style="padding:12px;text-align:center"><div style="font-size:11px;color:var(--ab-text-secondary)">Accuracy</div><div style="font-size:22px;font-weight:700;color:var(--ab-primary)">' + (data.cv_accuracy * 100).toFixed(1) + '%</div></div>';
  html += '<div class="card" style="padding:12px;text-align:center"><div style="font-size:11px;color:var(--ab-text-secondary)">Features</div><div style="font-size:22px;font-weight:700;color:var(--ab-primary)">' + data.n_selected + '</div></div>';
  html += '</div>';

  // Biomarker table
  html += '<table class="data-table" style="font-size:12px"><thead><tr><th>#</th><th>Gene</th><th>Coefficient</th><th>Direction</th><th>Importance</th></tr></thead><tbody>';
  const maxCoef = Math.max(...biomarkers.map(b => Math.abs(b.coefficient)));
  for (let i = 0; i < Math.min(biomarkers.length, 30); i++) {
    const b = biomarkers[i];
    const pct = Math.round((Math.abs(b.coefficient) / maxCoef) * 100);
    const color = b.direction === 'up' ? '#DC2626' : '#2563EB';
    html += '<tr><td>' + (i + 1) + '</td><td><strong>' + b.gene + '</strong></td>';
    html += '<td>' + b.coefficient.toFixed(4) + '</td>';
    html += '<td style="color:' + color + '">' + (b.direction === 'up' ? '↑ Up' : '↓ Down') + '</td>';
    html += '<td><div style="width:80px;height:6px;background:#E5E7EB;border-radius:3px;display:inline-block;vertical-align:middle"><div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:3px"></div></div></td></tr>';
  }
  html += '</tbody></table>';
  if (biomarkers.length > 30) html += '<p style="font-size:11px;color:var(--ab-text-secondary);margin-top:4px">Showing top 30 of ' + biomarkers.length + ' biomarkers</p>';

  el.innerHTML = html;
}
