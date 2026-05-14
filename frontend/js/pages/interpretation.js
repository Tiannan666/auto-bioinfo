// Interpretation Page
function renderInterpretation() {
  const t = (k) => I18N.t(k);
  const foci = ['auto','inflammation','oxidative_stress','metabolic_reprogramming','macrophage_polarization','bone_remodeling','tumor_immunity','mitochondrial','cell_death','immune_regulation','cell_proliferation','cell_migration','lipid_metabolism','glycolysis','oxphos'];
  return `
    <div class="page-desc">${t('interp.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:12px;color:var(--ab-primary)">Interpretation Settings</h3>
        <div class="form-group"><label class="form-label">${t('interp.focus')}</label>
          <select class="form-select" id="interpFocus">${foci.map(f => '<option value="' + f + '"' + (f==='auto'?' selected':'') + '>' + (f==='auto'?t('interp.auto'):t('focus.'+f)) + '</option>').join('')}</select></div>
        <div class="form-group"><label class="form-label">${t('interp.lang')}</label>
          <select class="form-select" id="interpLang"><option value="zh">Chinese</option><option value="en">English</option><option value="both">Bilingual</option></select></div>
        <button class="btn btn-primary" id="btnRunInterp" onclick="runInterpretation()" style="width:100%;margin-top:12px">${t('interp.generate')}</button>
      </div>
      <div class="split-main">
        <div id="interpResult"><div class="card"><p style="color:var(--ab-text-secondary);font-size:13px;text-align:center;padding:40px 0">${t('interp.placeholder')}</p></div></div>
      </div>
    </div>`;
}

async function runInterpretation() {
  const t = (k) => I18N.t(k);
  if (!requireApiKey()) return;
  const params = {
    focus: document.getElementById('interpFocus').value, language: document.getElementById('interpLang').value,
    project_id: window._loadedData?.project_id || 'current',
  };
  const btn = document.getElementById('btnRunInterp'); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Generating...';
  const el = document.getElementById('interpResult'); el.innerHTML = '<div class="card" style="text-align:center"><div class="spinner"></div><p style="margin-top:8px;color:var(--ab-text-secondary)">' + t('interp.generating') + '</p></div>';
  try {
    const data = await API.interpretation(params);
    el.innerHTML = ['summary','results','figure_legend','discussion','verification','key_findings']
      .filter(k => data[k])
      .map(k => '<div class="card" style="margin-bottom:12px"><div class="card-header"><h3>' + t('interp.'+k) + '</h3></div><div style="font-size:13px;line-height:1.8;white-space:pre-wrap">' + data[k] + '</div></div>').join('');
    window._interpResult = data;
  } catch(e) { el.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
  finally { btn.disabled = false; btn.textContent = t('interp.generate'); }
}
