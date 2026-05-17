// Enrichment Analysis Page
function renderEnrichment() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('enrich.desc')}</div>
    <div class="tabs" id="enrichTabs">
      <div class="tab active" onclick="switchEnrichTab('go')">GO Enrichment</div>
      <div class="tab" onclick="switchEnrichTab('kegg')">KEGG Pathway</div>
      <div class="tab" onclick="switchEnrichTab('gsea')">GSEA</div>
    </div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">${t('enrich.params')}</h3>
        <div class="form-group"><label class="form-label">${t('enrich.source')}</label>
          <select class="form-select" id="enrichSource"><option value="diff">${t('enrich.source_diff')}</option><option value="up">${t('enrich.source_up')}</option><option value="down">${t('enrich.source_down')}</option><option value="all">${t('enrich.source_all')}</option></select></div>
        <div class="form-group"><label class="form-label">${t('enrich.pval')}</label><input type="number" class="form-input" id="enrichPval" value="0.05" step="0.01" min="0" max="1"></div>
        <div class="form-group"><label class="form-label">Species</label>
          <select class="form-select" id="enrichSpecies"><option value="human">Human (Homo sapiens)</option><option value="mouse">Mouse (Mus musculus)</option><option value="rat">Rat (Rattus norvegicus)</option></select></div>
        <div class="form-group" id="goSection"><label class="form-label">${t('enrich.go_cat')}</label>
          <label style="font-size:12px;display:block;margin:4px 0"><input type="checkbox" checked id="goBP"> Biological Process (BP)</label>
          <label style="font-size:12px;display:block;margin:4px 0"><input type="checkbox" checked id="goCC"> Cellular Component (CC)</label>
          <label style="font-size:12px;display:block;margin:4px 0"><input type="checkbox" checked id="goMF"> Molecular Function (MF)</label></div>
        <div class="form-group" id="gseaSection" style="display:none"><label class="form-label">${t('enrich.gsea_geneset')}</label>
          <select class="form-select" id="gseaGeneset"><option value="go">GO Gene Sets</option><option value="kegg">KEGG Gene Sets</option><option value="hallmark">Hallmark Gene Sets</option></select></div>
        <button class="btn btn-primary" id="btnRunEnrich" onclick="runEnrichment()" style="width:100%;margin-top:16px">${t('enrich.run')}</button>
      </div>
      <div class="split-main">
        <div id="enrichResult" class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('enrich.placeholder')}</p></div>
        <div id="enrichPlot" style="display:none"></div>
      </div>
    </div>
  `;
}

let enrichTab = 'go';
function switchEnrichTab(tab) {
  enrichTab = tab;
  document.querySelectorAll('#enrichTabs .tab').forEach(t => t.classList.toggle('active', t === event.target));
  document.getElementById('goSection').style.display = tab === 'gsea' ? 'none' : 'block';
  document.getElementById('gseaSection').style.display = tab === 'gsea' ? 'block' : 'none';
}

async function runEnrichment() {
  const t = (k) => I18N.t(k);
  const params = {
    type: enrichTab, source: document.getElementById('enrichSource').value,
    pval_cutoff: parseFloat(document.getElementById('enrichPval').value),
    go_bp: document.getElementById('goBP')?.checked||false, go_cc: document.getElementById('goCC')?.checked||false, go_mf: document.getElementById('goMF')?.checked||false,
    gsea_geneset: enrichTab==='gsea'?document.getElementById('gseaGeneset').value:null,
    species: document.getElementById('enrichSpecies')?.value||'human',
    project_id: window._loadedData?.project_id||'current',
  };
  const btn = document.getElementById('btnRunEnrich'); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> ' + t('qc.running');
  const el = document.getElementById('enrichResult'); el.innerHTML = '<div class="spinner"></div> ' + t('qc.running');
  try {
    const endpoint = enrichTab==='gsea'?API.gsea:API.enrichment;
    const data = await endpoint(params);
    renderEnrichResult(data); window._enrichResult = data;
  } catch(e) { el.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
  finally { btn.disabled = false; btn.textContent = t('enrich.run'); }
}

function renderEnrichResult(data) {
  const t = (k) => I18N.t(k);
  const el = document.getElementById('enrichResult');
  const terms = data.terms || [];
  const cols = data.type==='gsea'?['Term','NES','ES','P-value','FDR','Leading Edge']:['Term','ID','Gene Count','P-value','FDR','Genes'];
  const rows = terms.slice(0,20).map(tm => '<tr>' + cols.map((c,i) => '<td>' + (i===0?'<strong>':'') + (tm[c.toLowerCase().replace(/[ -]/g,'_')]||'-') + (i===0?'</strong>':'') + '</td>').join('') + '</tr>').join('');
  el.innerHTML = '<div class="card-header"><h3>' + t('enrich.result_title') + '</h3><span class="badge badge-info">' + terms.length + ' ' + t('enrich.terms') + '</span></div>' +
    '<table class="data-table"><thead><tr>' + cols.map(c => '<th>' + c + '</th>').join('') + '</tr></thead><tbody>' + rows + '</tbody></table>' +
    (terms.length>20?'<p style="font-size:12px;color:var(--ab-text-secondary);margin-top:4px">Showing top 20 of ' + terms.length + ' terms</p>':'');
}
