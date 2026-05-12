// Differential Analysis Page
function renderDifferential() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('diff.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">${t('diff.params')}</h3>
        <div class="form-group"><label class="form-label">${t('diff.group1')}</label><input type="text" class="form-input" id="diffGroup1" placeholder="e.g. Treatment"></div>
        <div class="form-group"><label class="form-label">${t('diff.group2')}</label><input type="text" class="form-input" id="diffGroup2" placeholder="e.g. Control"></div>
        <div class="form-group"><label class="form-label">${t('diff.logfc')}</label><input type="number" class="form-input" id="diffLogFC" value="1.0" step="0.1" min="0"></div>
        <div class="form-group"><label class="form-label">${t('diff.pval')}</label><input type="number" class="form-input" id="diffPval" value="0.05" step="0.01" min="0" max="1"></div>
        <div class="form-group"><label class="form-label">${t('diff.fdr')}</label><input type="number" class="form-input" id="diffFDR" value="0.05" step="0.01" min="0" max="1"></div>
        <details style="margin-top:12px"><summary style="font-size:13px;font-weight:600;cursor:pointer;color:var(--ab-text-secondary)">${t('diff.advanced')}</summary>
          <div style="margin-top:8px">
            <div class="form-group"><label class="form-label"><input type="checkbox" id="diffLog2" checked> ${t('diff.log2')}</label></div>
            <div class="form-group"><label class="form-label"><input type="checkbox" id="diffFilterLow" checked> ${t('diff.filter_low')}</label></div>
            <div class="form-group"><label class="form-label">${t('diff.method')}</label>
              <select class="form-select" id="diffMethod"><option value="ttest">t-test (Welch)</option><option value="wilcoxon">Wilcoxon rank-sum</option><option value="limma">limma-like (moderated t)</option></select></div>
          </div>
        </details>
        <button class="btn btn-primary" id="btnRunDiff" onclick="runDifferential()" style="width:100%;margin-top:16px">${t('diff.run')}</button>
      </div>
      <div class="split-main">
        <div id="diffResult" class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('diff.placeholder')}</p></div>
        <div id="diffTables" style="display:none"></div>
        <div id="diffActions" style="display:none;margin-top:12px;display:flex;gap:8px">
          <button class="btn btn-primary" onclick="App.navigate('enrichment')">${t('diff.proceed_enrich')}</button>
          <button class="btn btn-secondary" onclick="App.navigate('visualization')">${t('diff.generate_fig')}</button>
          <button class="btn btn-outline" onclick="exportDiffCSV()">${t('diff.export_csv')}</button>
        </div>
      </div>
    </div>
  `;
}

async function runDifferential() {
  const t = (k) => I18N.t(k);
  const params = {
    group1: document.getElementById('diffGroup1').value.trim(), group2: document.getElementById('diffGroup2').value.trim(),
    logfc: parseFloat(document.getElementById('diffLogFC').value), pval: parseFloat(document.getElementById('diffPval').value),
    fdr: parseFloat(document.getElementById('diffFDR').value), log2: document.getElementById('diffLog2').checked,
    filter_low: document.getElementById('diffFilterLow').checked, method: document.getElementById('diffMethod').value,
    project_id: window._loadedData?.project_id || 'current',
  };
  if (!params.group1 || !params.group2) return alert('Please specify both comparison groups.');
  const btn = document.getElementById('btnRunDiff'); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('qc.running');
  const el = document.getElementById('diffResult'); el.innerHTML = '<div class="spinner"></div> ' + t('qc.running');
  try {
    const data = await API.diffAnalysis(params);
    renderDiffResult(data);
    document.getElementById('diffTables').style.display = 'block';
    document.getElementById('diffActions').style.display = 'flex';
    window._diffResult = data;
  } catch (e) { el.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
  finally { btn.disabled = false; btn.textContent = t('diff.run'); }
}

function renderDiffResult(data) {
  const t = (k) => I18N.t(k);
  document.getElementById('diffResult').innerHTML = `
    <div class="card-header"><h3>${t('diff.result_title')}</h3></div>
    <div class="stat-cards">
      <div class="stat-card"><div class="stat-value">${data.n_total||0}</div><div class="stat-label">${t('diff.total_genes')}</div></div>
      <div class="stat-card"><div class="stat-value" style="color:var(--ab-error)">${data.n_up||0}</div><div class="stat-label">${t('diff.up')}</div></div>
      <div class="stat-card"><div class="stat-value" style="color:var(--ab-btn)">${data.n_down||0}</div><div class="stat-label">${t('diff.down')}</div></div>
      <div class="stat-card"><div class="stat-value">${data.n_sig||0}</div><div class="stat-label">${t('diff.sig')}${data.fdr_threshold||0.05})</div></div>
    </div>`;
  const tb = document.getElementById('diffTables');
  tb.innerHTML = data.top_genes ? `
    <div class="card" style="margin-top:12px"><div class="card-header"><h3>${t('diff.top_genes')}</h3></div>
    <table class="data-table"><thead><tr><th>${t('diff.gene')}</th><th>log2FC</th><th>P-value</th><th>FDR</th><th>${t('diff.direction')}</th></tr></thead>
    <tbody>${data.top_genes.map(g => '<tr><td><strong>' + g.gene + '</strong></td><td>' + (g.logfc?.toFixed(3)||'-') + '</td><td>' + (g.pval?.toExponential(2)||'-') + '</td><td>' + (g.fdr?.toExponential(2)||'-') + '</td><td><span class="badge ' + (g.direction==='up'?'badge-error':'badge-info') + '">' + g.direction + '</span></td></tr>').join('')}</tbody></table></div>` : '';
}

function exportDiffCSV() {
  if (!window._diffResult) return;
  const rows = [['Gene','log2FC','P-value','FDR','Direction']];
  (window._diffResult.all_genes||[]).forEach(g => rows.push([g.gene,g.logfc,g.pval,g.fdr,g.direction]));
  downloadCSV('differential_genes.csv', rows);
}
function downloadCSV(filename, rows) {
  const csv = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob(['﻿'+csv],{type:'text/csv;charset=utf-8'});
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=filename; a.click();
}
