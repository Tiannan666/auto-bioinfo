// Storyline Recommendations Page
function renderStoryline() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('storyline.desc')}</div>
    <div class="card">
      <div class="card-header"><h3>${t('storyline.title')}</h3></div>
      <p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:12px">${t('storyline.desc2')}</p>
      <div class="grid-2" style="margin-bottom:12px">
        <div class="form-group"><label class="form-label">${t('storyline.count')}</label>
          <select class="form-select" id="storyCount"><option value="3">3</option><option value="4">4</option><option value="5" selected>5</option></select></div>
        <div class="form-group"><label class="form-label">${t('interp.lang')}</label>
          <select class="form-select" id="storyLang"><option value="zh">Chinese</option><option value="en">English</option><option value="both" selected>Bilingual</option></select></div>
      </div>
      <button class="btn btn-primary" id="btnRunStory" onclick="runStoryline()">${t('storyline.generate')}</button>
    </div>
    <div id="storyResult"></div>`;
}

async function runStoryline() {
  const t = (k) => I18N.t(k);
  if (!requireApiKey()) return;
  const params = { count: parseInt(document.getElementById('storyCount').value), language: document.getElementById('storyLang').value, project_id: window._loadedData?.project_id || 'current' };
  const btn = document.getElementById('btnRunStory'); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Generating...';
  const el = document.getElementById('storyResult'); el.innerHTML = '<div class="card" style="text-align:center;margin-top:12px"><div class="spinner"></div><p style="margin-top:8px;color:var(--ab-text-secondary)">Analyzing pathways and building mechanistic hypotheses with DeepSeek AI...</p></div>';
  try {
    const data = await API.storyline(params);
    const storylines = data.storylines || [];
    el.innerHTML = storylines.map((s,i) => `
      <div class="card" style="margin-top:12px;border-left:4px solid var(--ab-primary)">
        <div class="card-header"><h3><span style="color:var(--ab-primary)">${t('storyline.direction')} ${i+1}:</span> ${s.title||s.hypothesis||'Mechanism Hypothesis '+(i+1)}</h3><span class="badge badge-info">${t('storyline.score')}: ${s.confidence||'--'}</span></div>
        <div class="grid-2" style="gap:12px">
          <div><strong style="font-size:13px">${t('storyline.hypothesis')}</strong><p style="font-size:13px;color:var(--ab-text-secondary);margin-top:4px;line-height:1.7">${s.hypothesis||'-'}</p>
          <strong style="font-size:13px;margin-top:8px;display:block">${t('storyline.key_genes')}</strong><p style="font-size:13px;color:var(--ab-text-secondary)">${(s.key_genes||[]).join(', ')||'-'}</p>
          <strong style="font-size:13px;margin-top:8px;display:block">${t('storyline.key_pathways')}</strong><p style="font-size:13px;color:var(--ab-text-secondary)">${(s.key_pathways||[]).join(', ')||'-'}</p></div>
          <div><strong style="font-size:13px">${t('storyline.validation')}</strong><p style="font-size:13px;color:var(--ab-text-secondary);margin-top:4px;line-height:1.7">${s.validation||'-'}</p>
          <strong style="font-size:13px;margin-top:8px;display:block">${t('storyline.figures')}</strong><p style="font-size:13px;color:var(--ab-text-secondary);line-height:1.7">${s.suggested_figures||'-'}</p>
          <strong style="font-size:13px;margin-top:8px;display:block">${t('storyline.title_field')}</strong><p style="font-size:13px;color:var(--ab-text-secondary);font-style:italic">${s.paper_title||'-'}</p></div>
        </div>
        ${s.mechanism?'<div style="margin-top:12px;background:var(--ab-light-bg);padding:12px;border-radius:var(--ab-radius);font-size:13px;line-height:1.8;color:var(--ab-text)">'+s.mechanism+'</div>':''}
      </div>`).join('');
    window._storyResult = data;
  } catch(e) { el.innerHTML = '<div class="alert alert-error" style="margin-top:12px">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
  finally { btn.disabled = false; btn.textContent = t('storyline.generate'); }
}
