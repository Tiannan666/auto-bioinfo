// SPA Router + App Initialization

const App = {
  currentPage: 'dashboard',

  pages: {},

  register(name, renderFn) {
    this.pages[name] = renderFn;
  },

  navigate(name, data) {
    if (this.currentPage === name && !data) return;
    this.currentPage = name;
    document.getElementById('pageTitle').textContent = I18N.t('nav.' + name) || getPageTitle(name);

    // Update sidebar active
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
    const link = document.querySelector(`[data-page="${name}"]`);
    if (link) link.classList.add('active');

    // Render page
    const container = document.getElementById('contentArea');
    const renderFn = this.pages[name];
    if (renderFn) {
      container.innerHTML = renderFn(data);
      if (typeof window['init_' + name.replace(/-/g, '_')] === 'function') {
        window['init_' + name.replace(/-/g, '_')](data);
      }
    } else {
      container.innerHTML = '<div class="coming-soon"><div class="icon">-</div><h3>' + (I18N.t('nav.' + name) || name) + '</h3><p>This page is under development.</p></div>';
    }
  }
};

function getPageTitle(name) {
  const titles = {
    'dashboard': 'Dashboard', 'data-import': 'Data Import', 'quality-control': 'Quality Control',
    'differential': 'Differential Analysis', 'enrichment': 'Enrichment Analysis',
    'visualization': 'Visualization', 'interpretation': 'Interpretation',
    'storyline': 'Storyline Recommendations', 'report-export': 'Report Export', 'scrna': 'scRNA-seq Analysis',
  };
  return titles[name] || name;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  registerAllPages();
  applyI18nSidebar();

  document.querySelectorAll('.sidebar-nav a[data-page]').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.hash = a.dataset.page;
      App.navigate(a.dataset.page);
    });
  });

  function handleHash() {
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    App.navigate(hash);
  }
  window.addEventListener('hashchange', handleHash);
  handleHash();

  checkConfig();
});

function applyI18nSidebar() {
  const sections = document.querySelectorAll('.sidebar-nav .nav-section');
  if (sections.length >= 1) sections[0].textContent = I18N.t('nav.analysis_workflow');
  if (sections.length >= 2) sections[1].textContent = I18N.t('nav.intelligence');
  if (sections.length >= 3) sections[2].textContent = I18N.t('nav.output');

  document.querySelectorAll('.sidebar-nav a[data-page]').forEach(a => {
    const page = a.dataset.page;
    const iconEl = a.querySelector('.nav-icon');
    const badgeEl = a.querySelector('.badge');
    // Keep icon, update text
    const textNode = Array.from(a.childNodes).find(n => n.nodeType === 3 && n.textContent.trim());
    if (textNode) textNode.textContent = ' ' + (I18N.t('nav.' + page) || getPageTitle(page));
    if (badgeEl) badgeEl.textContent = I18N.t('nav.coming_soon');
  });
}

function registerAllPages() {
  App.register('dashboard', renderDashboard);
  App.register('data-import', renderDataImport);
  App.register('quality-control', renderQualityControl);
  App.register('differential', renderDifferential);
  App.register('enrichment', renderEnrichment);
  App.register('visualization', renderVisualization);
  App.register('interpretation', renderInterpretation);
  App.register('storyline', renderStoryline);
  App.register('report-export', renderReportExport);
  App.register('scrna', renderScrna);
}
