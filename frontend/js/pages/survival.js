// Survival Analysis Page
function renderSurvival() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('survival.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">${t('survival.params')}</h3>
        <div class="form-group"><label class="form-label">${t('survival.gene')}</label>
          <input type="text" class="form-input" id="survGene" placeholder="e.g. TP53, BRCA1, CD8A"></div>
        <div class="form-group"><label class="form-label">${t('survival.cutoff')}</label>
          <select class="form-select" id="survCutoff"><option value="median">Median</option></select></div>
        <p style="font-size:11px;color:var(--ab-text-secondary);margin:8px 0;line-height:1.5">${t('survival.info')}</p>
        <button class="btn btn-primary" id="btnRunSurv" onclick="runSurvival()" style="width:100%;margin-top:16px">${t('survival.run')}</button>
      </div>
      <div class="split-main">
        <div id="survResult" class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('survival.placeholder')}</p></div>
      </div>
    </div>
  `;
}

async function runSurvival() {
  const t = (k) => I18N.t(k);
  const gene = document.getElementById('survGene').value.trim();
  if (!gene) { alert(t('survival.gene_required')); return; }
  const btn = document.getElementById('btnRunSurv');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('qc.running');
  const el = document.getElementById('survResult');
  el.innerHTML = '<div class="spinner"></div> ' + t('qc.running');
  try {
    const data = await API.survival({
      gene: gene,
      cutoff: document.getElementById('survCutoff').value,
      project_id: window._loadedData?.project_id || 'current',
    });
    if (data.error) {
      el.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
    } else {
      renderSurvivalResult(data);
    }
  } catch(e) {
    el.innerHTML = '<div class="alert alert-error">' + e.message + '</div>';
  } finally {
    btn.disabled = false; btn.textContent = t('survival.run');
  }
}

function renderSurvivalResult(data) {
  const t = (k) => I18N.t(k);
  const el = document.getElementById('survResult');
  const sig = data.logrank_pval < 0.05;

  let html = '<div class="card-header"><h3>' + data.gene + ' — Survival Analysis</h3>' +
    '<span class="badge ' + (sig ? 'badge-success' : 'badge-warning') + '">' + (sig ? 'Significant' : 'Not significant') + '</span></div>';

  // KM plot
  if (data.plot_base64) {
    html += '<div style="text-align:center;margin:16px 0"><img src="data:image/png;base64,' + data.plot_base64 + '" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1)"></div>';
  }

  // Stats table
  html += '<table class="data-table" style="margin-top:12px"><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>';
  html += '<tr><td>Hazard Ratio (HR)</td><td><strong>' + data.hr.toFixed(3) + '</strong> (' + data.hr_ci[0].toFixed(3) + ' - ' + data.hr_ci[1].toFixed(3) + ')</td></tr>';
  html += '<tr><td>Log-rank P-value</td><td><strong style="color:' + (sig ? 'var(--ab-success)' : 'var(--ab-warning)') + '">' + data.logrank_pval.toExponential(3) + '</strong></td></tr>';
  html += '<tr><td>Cox P-value</td><td>' + data.cox_pval.toExponential(3) + '</td></tr>';
  html += '<tr><td>High expression group</td><td>n=' + data.n_high + '</td></tr>';
  html += '<tr><td>Low expression group</td><td>n=' + data.n_low + '</td></tr>';
  if (data.median_high) html += '<tr><td>Median survival (High)</td><td>' + data.median_high.toFixed(1) + '</td></tr>';
  if (data.median_low) html += '<tr><td>Median survival (Low)</td><td>' + data.median_low.toFixed(1) + '</td></tr>';
  html += '</tbody></table>';

  el.innerHTML = html;
}
