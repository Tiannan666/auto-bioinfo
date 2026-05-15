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
}
