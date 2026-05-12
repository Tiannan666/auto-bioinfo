// Visualization Page
function renderVisualization() {
  const t = (k) => I18N.t(k);
  const plots = [
    {id:'volcano',name:t('viz.volcano'),icon:'V'},{id:'heatmap',name:t('viz.heatmap'),icon:'H'},
    {id:'pca',name:t('viz.pca'),icon:'P'},{id:'correlation',name:t('viz.correlation'),icon:'C'},
    {id:'go_bubble',name:t('viz.go_bubble'),icon:'B'},{id:'go_bar',name:t('viz.go_bar'),icon:'B'},
    {id:'kegg_bubble',name:t('viz.kegg_bubble'),icon:'B'},{id:'kegg_bar',name:t('viz.kegg_bar'),icon:'B'},
    {id:'gsea_curve',name:t('viz.gsea_curve'),icon:'G'},{id:'top_genes',name:t('viz.top_genes'),icon:'T'},
    {id:'boxplot',name:t('viz.boxplot'),icon:'B'},{id:'violin',name:t('viz.violin'),icon:'V'},{id:'deg_stats',name:t('viz.deg_stats'),icon:'D'},
  ];
  return `
    <div class="page-desc">${t('viz.desc')}</div>
    <div class="split-layout">
      <div class="split-sidebar">
        <h3 style="font-size:14px;margin-bottom:8px;color:var(--ab-primary)">${t('viz.plot_type')}</h3>
        <div style="max-height:300px;overflow-y:auto;margin-bottom:12px">
          ${plots.map(p => '<label style="display:block;padding:4px 0;font-size:13px;cursor:pointer"><input type="radio" name="plotType" value="' + p.id + '" ' + (p.id==='volcano'?'checked':'') + ' onchange="updatePlotParams(\'' + p.id + '\')"> ' + p.icon + ' ' + p.name + '</label>').join('')}
        </div>
        <hr style="border-color:var(--ab-border);margin:8px 0">
        <div id="plotParams">
          <h3 style="font-size:14px;margin-bottom:8px;color:var(--ab-primary)">${t('enrich.params')}</h3>
          <div class="form-group"><label class="form-label">${t('viz.title')}</label><input type="text" class="form-input" id="plotTitle"></div>
          <div class="form-group"><label class="form-label">${t('viz.xlabel')}</label><input type="text" class="form-input" id="plotXlabel"></div>
          <div class="form-group"><label class="form-label">${t('viz.ylabel')}</label><input type="text" class="form-input" id="plotYlabel"></div>
          <div class="form-group"><label class="form-label">${t('viz.font_size')}</label><input type="number" class="form-input" id="plotFontSize" value="12" min="6" max="24"></div>
          <div class="grid-2"><div class="form-group"><label class="form-label">${t('viz.width')}</label><input type="number" class="form-input" id="plotWidth" value="8" step="0.5"></div>
          <div class="form-group"><label class="form-label">${t('viz.height')}</label><input type="number" class="form-input" id="plotHeight" value="6" step="0.5"></div></div>
          <div class="form-group"><label class="form-label">DPI</label><select class="form-select" id="plotDPI"><option value="150">150</option><option value="300" selected>300</option><option value="600">600</option></select></div>
          <div class="form-group"><label class="form-label">${t('viz.up_color')}</label><input type="color" class="form-input" id="plotUpColor" value="#DC2626"></div>
          <div class="form-group"><label class="form-label">${t('viz.down_color')}</label><input type="color" class="form-input" id="plotDnColor" value="#2563EB"></div>
          <details style="margin-top:8px"><summary style="font-size:13px;font-weight:600;cursor:pointer;color:var(--ab-text-secondary)">${t('viz.more_options')}</summary>
            <div style="margin-top:8px">
              <label style="font-size:12px;display:block;margin:4px 0"><input type="checkbox" id="plotShowLabels"> ${t('viz.show_labels')}</label>
              <label style="font-size:12px;display:block;margin:4px 0"><input type="checkbox" id="plotShowLegend" checked> ${t('viz.show_legend')}</label>
              <label style="font-size:12px;display:block;margin:4px 0"><input type="checkbox" id="plotLogFCline"> ${t('viz.show_logfc')}</label>
            </div></details>
          <label class="form-label" style="margin-top:8px">${t('viz.top_n')}</label><input type="number" class="form-input" id="plotTopN" value="20" min="1" max="100">
        </div>
        <button class="btn btn-primary" onclick="generatePlot()" style="width:100%;margin-top:12px">${t('viz.generate')}</button>
        <div style="margin-top:8px;display:flex;gap:4px;flex-wrap:wrap">
          <button class="btn btn-sm btn-secondary" onclick="exportPlot('png')">PNG</button><button class="btn btn-sm btn-secondary" onclick="exportPlot('pdf')">PDF</button>
          <button class="btn btn-sm btn-secondary" onclick="exportPlot('svg')">SVG</button><button class="btn btn-sm btn-secondary" onclick="exportPlot('tiff')">TIFF</button>
        </div>
      </div>
      <div class="split-main">
        <div id="plotResult" class="card" style="min-height:400px;display:flex;align-items:center;justify-content:center">
          <p style="color:var(--ab-text-secondary);font-size:13px">${t('viz.placeholder')}</p></div>
      </div>
    </div>`;
}

function updatePlotParams(id) {}
async function generatePlot() {
  const t = (k) => I18N.t(k);
  const plotType = document.querySelector('input[name="plotType"]:checked')?.value||'volcano';
  const params = {
    plot_type:plotType, title: document.getElementById('plotTitle').value||undefined,
    xlabel: document.getElementById('plotXlabel').value||undefined, ylabel: document.getElementById('plotYlabel').value||undefined,
    font_size: parseInt(document.getElementById('plotFontSize').value),
    width: parseFloat(document.getElementById('plotWidth').value), height: parseFloat(document.getElementById('plotHeight').value),
    dpi: parseInt(document.getElementById('plotDPI').value),
    up_color: document.getElementById('plotUpColor').value, down_color: document.getElementById('plotDnColor').value,
    show_labels: document.getElementById('plotShowLabels').checked, show_legend: document.getElementById('plotShowLegend').checked,
    show_logfc_line: document.getElementById('plotLogFCline').checked, top_n: parseInt(document.getElementById('plotTopN').value),
    project_id: window._loadedData?.project_id||'current',
  };
  const el = document.getElementById('plotResult');
  el.innerHTML = '<div style="text-align:center"><div class="spinner"></div><p style="margin-top:8px;color:var(--ab-text-secondary)">' + t('viz.generating') + '</p></div>';
  try {
    const data = await API.plotsGenerate(params);
    el.innerHTML = data.images?.length ? data.images.map(img => '<img src="/' + img + '" style="max-width:100%;border:1px solid var(--ab-border);border-radius:var(--ab-radius)" onerror="this.outerHTML=\'<div class=alert-alert-warning>Image not found: ' + img + '</div>\'">').join('') : '<div class="alert alert-warning">Plot generated but no image returned.</div>';
    window._lastPlot = data;
  } catch(e) { el.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
}
async function exportPlot(format) {
  if (!window._lastPlot) return alert('Generate a plot first.');
  try { await API.plotsExport({...window._lastPlot, format}); alert('Export as ' + format.toUpperCase() + ' requested.'); }
  catch(e) { alert('Export failed: ' + e.message); }
}
