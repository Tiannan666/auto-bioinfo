// Dashboard Page
function renderDashboard() {
  const t = (k) => I18N.t(k);
  const steps = ['data_import','quality_control','differential','enrichment','visualization','interpretation','storyline','report_export'];
  const stepPages = ['data-import','quality-control','differential','enrichment','visualization','interpretation','storyline','report-export'];
  return `
    <div class="page-desc">${t('dashboard.welcome')}</div>
    <div class="card">
      <div class="card-header"><h3>${t('dashboard.workflow')}</h3></div>
      <div class="steps" id="workflowSteps">
        ${steps.map((s,i) => `
          <div class="step" onclick="window.location.hash = '${stepPages[i]}'" style="cursor:pointer">
            <span class="step-num">${i+1}</span>${t('step.'+s)}
          </div>
        `).join('')}
      </div>
    </div>
    <div class="stat-cards">
      <div class="stat-card"><div class="stat-value" id="statProjects">0</div><div class="stat-label">${t('dashboard.recent_projects')}</div></div>
      <div class="stat-card"><div class="stat-value" id="statStatus">-</div><div class="stat-label">${t('dashboard.data_status')}</div></div>
      <div class="stat-card"><div class="stat-value" id="statProgress">-</div><div class="stat-label">${t('dashboard.analysis_progress')}</div></div>
      <div class="stat-card"><div class="stat-value" id="statReports">0</div><div class="stat-label">${t('dashboard.exported_reports')}</div></div>
    </div>
    <div class="card">
      <div class="card-header"><h3>${t('dashboard.r_engine', 'R 引擎状态')}</h3></div>
      <div class="r-status" id="rStatusArea" style="padding:12px 0;font-size:14px;display:flex;align-items:center;gap:10px">
        <span id="rStatusIcon">⏳</span>
        <span id="rStatusText">${t('dashboard.checking_r', '检测 R 环境中...')}</span>
      </div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header"><h3>${t('dashboard.quick_start')}</h3></div>
        <p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:14px">${t('dashboard.quick_start_desc')}</p>
        <button class="btn btn-primary" onclick="window.location.hash = 'data-import'">${t('dashboard.start_analysis')}</button>
      </div>
      <div class="card">
        <div class="card-header"><h3>${t('dashboard.supported_types')}</h3></div>
        <ul style="font-size:13px;color:var(--ab-text-secondary);padding-left:18px;line-height:2">
          <li>${t('dashboard.type_bulk')}</li>
          <li>${t('dashboard.type_meta')}</li>
          <li>${t('dashboard.type_diff')}</li>
          <li>${t('dashboard.type_go')}</li>
          <li>${t('dashboard.type_geo')}</li>
          <li><em>${t('dashboard.type_scrna')}</em></li>
        </ul>
      </div>
    </div>
  `;
}

function init_dashboard() {
  try {
    const projects = JSON.parse(localStorage.getItem('bioinfo_projects') || '[]');
    document.getElementById('statProjects').textContent = projects.length;
    document.getElementById('statReports').textContent = projects.filter(p => p.reports || 0).length;
  } catch(e) {}

  // Check R engine status
  API.rStatus().then(r => {
    const icon = document.getElementById('rStatusIcon');
    const text = document.getElementById('rStatusText');
    if (r.available) {
      icon.textContent = '✅';
      const rPath = document.getElementById('rStatusArea');
      text.textContent = 'R 引擎就绪 — 差异分析、富集分析、GSEA、生存分析、WGCNA 等功能可用';
      text.style.color = 'var(--ab-success, #16A34A)';
    } else {
      icon.textContent = '❌';
      text.textContent = 'R 引擎未就绪 — 差异分析、富集分析等依赖 R 的功能不可用。请将 R 运行时放置在 runtime/R/ 目录下。';
      text.style.color = 'var(--ab-warning, #D97706)';
    }
  }).catch(() => {
    const icon = document.getElementById('rStatusIcon');
    const text = document.getElementById('rStatusText');
    if (icon) icon.textContent = '⚠️';
    if (text) text.textContent = '无法检测 R 引擎状态';
  });
}
