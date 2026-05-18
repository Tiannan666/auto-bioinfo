// Immune Infiltration Analysis Page
function renderImmune() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('immune.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">${t('immune.method')}</h3>
        <div class="form-group"><label class="form-label">${t('immune.method')}</label>
          <select class="form-select" id="immuneMethod"><option value="ssgsea">ssGSEA</option></select></div>
        <p style="font-size:11px;color:var(--ab-text-secondary);margin:8px 0;line-height:1.5">${t('immune.info')}</p>
        <button class="btn btn-primary" id="btnRunImmune" onclick="runImmune()" style="width:100%;margin-top:16px">${t('immune.run')}</button>
      </div>
      <div class="split-main">
        <div id="immuneResult" class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('immune.placeholder')}</p></div>
      </div>
    </div>
  `;
}

async function runImmune() {
  const t = (k) => I18N.t(k);
  const btn = document.getElementById('btnRunImmune');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('qc.running');
  const el = document.getElementById('immuneResult');
  el.innerHTML = '<div class="spinner"></div> ' + t('qc.running');
  try {
    const data = await API.immune({
      method: document.getElementById('immuneMethod').value,
      project_id: window._loadedData?.project_id || 'current',
    });
    if (data.error) {
      el.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
    } else {
      renderImmuneResult(data);
      window._immuneResult = data;
    }
  } catch(e) {
    el.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>';
  } finally {
    btn.disabled = false; btn.textContent = t('immune.run');
  }
}

function renderImmuneResult(data) {
  const t = (k) => I18N.t(k);
  const el = document.getElementById('immuneResult');
  const cellTypes = data.cell_types || [];
  const samples = data.samples || [];
  const scores = data.scores_normalized || {};

  if (!cellTypes.length || !samples.length) {
    el.innerHTML = '<div class="alert alert-warning">No results. Ensure expression data contains immune-related genes.</div>';
    return;
  }

  // Summary header
  let html = '<div class="card-header"><h3>' + t('immune.cell_types') + '</h3>' +
    '<span class="badge badge-info">' + cellTypes.length + ' cell types &times; ' + samples.length + ' samples</span></div>';

  // Heatmap-style table
  html += '<div style="overflow-x:auto;margin-top:12px"><table class="data-table" style="font-size:11px">';
  html += '<thead><tr><th style="min-width:140px">' + t('immune.cell_types') + '</th>';
  for (const s of samples) {
    html += '<th style="text-align:center;min-width:60px">' + truncate(s, 12) + '</th>';
  }
  html += '</tr></thead><tbody>';

  for (const ct of cellTypes) {
    html += '<tr><td><strong>' + ct + '</strong></td>';
    for (const s of samples) {
      const val = (scores[ct] && scores[ct][s] !== undefined) ? scores[ct][s] : 0;
      const color = scoreColor(val);
      html += '<td style="text-align:center;background:' + color + ';color:' + (val > 0.6 ? '#fff' : '#1E3A8A') + '">' + val.toFixed(2) + '</td>';
    }
    html += '</tr>';
  }
  html += '</tbody></table></div>';

  // Top cell types per sample
  html += '<div style="margin-top:16px"><h4 style="font-size:13px;color:var(--ab-primary);margin-bottom:8px">' + t('immune.score') + ' (Top 5 per sample)</h4>';
  html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px">';
  for (const s of samples.slice(0, 8)) {
    const sampleScores = cellTypes.map(ct => ({ ct, val: (scores[ct] && scores[ct][s]) || 0 }))
      .sort((a, b) => b.val - a.val).slice(0, 5);
    html += '<div class="card" style="padding:8px"><strong style="font-size:11px">' + truncate(s, 16) + '</strong>';
    for (const item of sampleScores) {
      const pct = Math.round(item.val * 100);
      html += '<div style="display:flex;align-items:center;margin-top:4px;font-size:10px">' +
        '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + item.ct + '</span>' +
        '<div style="width:50px;height:6px;background:#E5E7EB;border-radius:3px;margin:0 4px"><div style="width:' + pct + '%;height:100%;background:#2563EB;border-radius:3px"></div></div>' +
        '<span>' + pct + '%</span></div>';
    }
    html += '</div>';
  }
  html += '</div></div>';

  el.innerHTML = html;
}

function scoreColor(val) {
  if (val < 0.2) return '#EFF6FF';
  if (val < 0.4) return '#BFDBFE';
  if (val < 0.6) return '#60A5FA';
  if (val < 0.8) return '#2563EB';
  return '#1E3A8A';
}

function truncate(s, n) {
  return s.length > n ? s.substring(0, n) + '...' : s;
}
