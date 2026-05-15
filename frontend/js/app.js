// Minimal SPA router - no state, no App object, just hash-based rendering
var _pages = {};
var _firstRender = true;

function page(name, fn) { _pages[name] = fn; }

function show(name) {
  var el = document.getElementById('contentArea');
  var fn = _pages[name];
  if (el && fn) { el.innerHTML = fn(); }
  document.getElementById('pageTitle').textContent = (typeof I18N !== 'undefined' && I18N.t('nav.' + name)) || name;
  // Highlight sidebar
  var links = document.querySelectorAll('.sidebar-nav a');
  for (var i = 0; i < links.length; i++) { links[i].classList.remove('active'); }
  var link = document.querySelector('[data-page="' + name + '"]');
  if (link) link.classList.add('active');
}

function route() {
  var hash = (window.location.hash || '#dashboard').replace('#', '');
  if (!hash) hash = 'dashboard';
  show(hash);
  if (_firstRender && typeof checkConfig === 'function') { checkConfig(); _firstRender = false; }
}

// Error handlers
window.onerror = function(msg, src, line) {
  var el = document.getElementById('contentArea');
  if (el) el.innerHTML = '<div style="padding:40px;text-align:center;color:#DC2626"><h3>Error</h3><p>' + String(msg).slice(0, 200) + '</p><p style="font-size:12px">' + (src||'').split('/').pop() + ':' + line + '</p></div>';
  return true;
};

// Register all pages, set up routing, start
document.addEventListener('DOMContentLoaded', function() {
  // Register pages (defined in page JS files loaded before this script)
  page('dashboard', renderDashboard);
  page('data-import', renderDataImport);
  page('quality-control', renderQualityControl);
  page('differential', renderDifferential);
  page('enrichment', renderEnrichment);
  page('visualization', renderVisualization);
  page('interpretation', renderInterpretation);
  page('storyline', renderStoryline);
  page('report-export', renderReportExport);
  page('scrna', renderScrna);

  // Sidebar click handlers
  var links = document.querySelectorAll('.sidebar-nav a[data-page]');
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener('click', function(e) {
      e.preventDefault();
      window.location.hash = this.dataset.page;
    });
  }

  // I18n if available
  if (typeof I18N !== 'undefined' && typeof I18N.applyAll === 'function') {
    I18N.applyAll();
  }

  // Route on hash change + initial load
  window.addEventListener('hashchange', route);
  route();
});
