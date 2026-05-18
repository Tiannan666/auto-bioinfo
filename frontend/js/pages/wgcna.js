// WGCNA Co-expression Network Page
function renderWgcna() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('wgcna.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">${t('wgcna.params')}</h3>
        <div class="form-group"><label class="form-label">${t('wgcna.n_genes')}</label>
          <input type="number" class="form-input" id="wgcnaNGenes" value="5000" min="500" max="20000"></div>
        <div class="form-group"><label class="form-label">${t('wgcna.min_module')}</label>
          <input type="number" class="form-input" id="wgcnaMinModule" value="30" min="10" max="200"></div>
        <p style="font-size:11px;color:var(--ab-text-secondary);margin:8px 0;line-height:1.5">${t('wgcna.info')}</p>
        <button class="btn btn-primary" id="btnRunWgcna" onclick="runWgcna()" style="width:100%;margin-top:16px">${t('wgcna.run')}</button>
      </div>
      <div class="split-main">
        <div id="wgcnaResult" class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('wgcna.placeholder')}</p></div>
      </div>
    </div>
  `;
}

async function runWgcna() {
  const t = (k) => I18N.t(k);
  const btn = document.getElementById('btnRunWgcna');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('wgcna.running');
  const el = document.getElementById('wgcnaResult');
  el.innerHTML = '<div class="spinner"></div> ' + t('wgcna.running');
  try {
    const data = await API.wgcna({
      n_top_genes: parseInt(document.getElementById('wgcnaNGenes').value),
      min_module_size: parseInt(document.getElementById('wgcnaMinModule').value),
      project_id: window._loadedData?.project_id || 'current',
    });
    if (data.error) {
      el.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
    } else {
      renderWgcnaResult(data);
      window._wgcnaResult = data;
    }
  } catch(e) {
    el.innerHTML = '<div class="alert alert-error">' + e.message + '</div>';
  } finally {
    btn.disabled = false; btn.textContent = t('wgcna.run');
  }
}

function renderWgcnaResult(data) {
  const t = (k) => I18N.t(k);
  const el = document.getElementById('wgcnaResult');
  const modules = data.modules || {};
  const hubGenes = data.hub_genes || {};

  let html = '<div class="card-header"><h3>' + t('wgcna.result_title') + '</h3>' +
    '<span class="badge badge-info">' + data.n_modules + ' modules | ' + data.n_genes + ' genes | power=' + data.soft_power + '</span></div>';

  // Module summary
  html += '<div style="margin-top:12px"><h4 style="font-size:13px;margin-bottom:8px">' + t('wgcna.modules') + '</h4>';
  html += '<div style="display:flex;flex-wrap:wrap;gap:6px">';
  const sortedModules = Object.entries(modules).sort((a, b) => b[1] - a[1]);
  for (const [mod, count] of sortedModules) {
    const color = mod === 'grey' ? '#9CA3AF' : mod;
    html += '<div style="padding:4px 10px;border-radius:12px;font-size:11px;background:' + color + ';color:' + (isLightColor(color) ? '#000' : '#fff') + '">' + mod + ' (' + count + ')</div>';
  }
  html += '</div></div>';

  // Hub genes per module
  html += '<div style="margin-top:16px"><h4 style="font-size:13px;margin-bottom:8px">' + t('wgcna.hub_genes') + '</h4>';
  html += '<table class="data-table" style="font-size:11px"><thead><tr><th>Module</th><th>Hub Genes (top 5 by kME)</th></tr></thead><tbody>';
  for (const [mod, genes] of Object.entries(hubGenes)) {
    if (mod === 'grey') continue;
    const geneStr = genes.map(g => '<strong>' + g.gene + '</strong> (' + g.kME.toFixed(2) + ')').join(', ');
    html += '<tr><td style="background:' + mod + ';color:' + (isLightColor(mod) ? '#000' : '#fff') + ';font-weight:600">' + mod + '</td><td>' + geneStr + '</td></tr>';
  }
  html += '</tbody></table></div>';

  el.innerHTML = html;
}

function isLightColor(color) {
  if (!color || color === 'grey' || color === 'gray') return false;
  const colors = { yellow: true, lightyellow: true, white: true, ivory: true, floralwhite: true, lighgreen: true, lightcyan: true, honeydew: true };
  return !!colors[color.toLowerCase()];
}
