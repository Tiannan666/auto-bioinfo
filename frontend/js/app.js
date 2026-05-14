// SPA Router + App Initialization

// Fallback I18N if i18n.js fails to load (prevents cascading ReferenceErrors)
if (typeof I18N === 'undefined') {
  var I18N = { t: function(k) { return k; }, lang: 'en', applyAll: function(){}, setLang: function(l){
    this._lang = l; localStorage.setItem('bioinfo_lang', l); applyI18nAll();
    var hash = window.location.hash || '#dashboard';
    if (typeof App !== 'undefined') App.navigate(hash.replace('#', ''));
  }};
}

// Self-contained i18n apply function (does not depend on i18n.js being loaded)
function applyI18nAll() {
  if (typeof I18N !== 'undefined' && typeof I18N.applyAll === 'function') I18N.applyAll();
}

// Show visible error if JS fails catastrophically
var _jsLoaded = false;
window.onerror = function(msg, src, line, col, err) {
  var el = document.getElementById('contentArea');
  if (el && !_jsLoaded) {
    el.innerHTML = '<div style="padding:40px;text-align:center;color:#DC2626;font-family:sans-serif"><h3>JavaScript Error</h3><p>' + String(msg).replace(/</g,'&lt;') + '</p><p style="font-size:12px;color:#6B7280">File: ' + (src||'?').split('/').pop() + ' line ' + line + '</p><p style="font-size:12px;margin-top:16px">Try restarting the app. If this persists, check that the installation is complete.</p></div>';
  }
  return true;
};
window.addEventListener('unhandledrejection', function(e) {
  console.error('[Unhandled Rejection]', e.reason);
  var el = document.getElementById('contentArea');
  if (el && !_jsLoaded) {
    el.innerHTML = '<div style="padding:40px;text-align:center;color:#DC2626"><h3>Startup Error</h3><p>' + String(e.reason).replace(/</g,'&lt;') + '</p></div>';
  }
});

const App = {
  currentPage: null,

  pages: {},

  register(name, renderFn) {
    this.pages[name] = renderFn;
  },

  navigate(name, data) {
    if (this.currentPage === name && !data) return;
    this.currentPage = name;
    var title = (typeof I18N !== 'undefined' && I18N.t('nav.' + name) !== 'nav.' + name) ? I18N.t('nav.' + name) : getPageTitle(name);
    document.getElementById('pageTitle').textContent = title;

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
  if (typeof applyI18nAll === 'function') applyI18nAll();

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
  // Sync topbar language dropdown
  var tb = document.getElementById('topbarLang');
  if (tb && typeof I18N !== 'undefined') tb.value = I18N.lang;
  _jsLoaded = true;
});

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
