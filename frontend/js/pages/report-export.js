// Report Export Page
function renderReportExport() {
  const t = (k) => I18N.t(k);
  return `
    <div class="page-desc">${t('report.desc')}</div>
    <div class="grid-2">
      <div class="card"><div class="card-header"><h3>${t('report.word')}</h3></div><p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:12px">${t('report.word_desc')}</p><button class="btn btn-primary" onclick="exportReport('word')">${t('report.export_btn')} Word (.docx)</button></div>
      <div class="card"><div class="card-header"><h3>${t('report.excel')}</h3></div><p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:12px">${t('report.excel_desc')}</p><button class="btn btn-primary" onclick="exportReport('excel')">${t('report.export_btn')} Excel (.xlsx)</button></div>
      <div class="card"><div class="card-header"><h3>${t('report.ppt')}</h3></div><p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:12px">${t('report.ppt_desc')}</p><button class="btn btn-primary" onclick="exportReport('ppt')">${t('report.export_btn')} PPT (.pptx)</button></div>
      <div class="card"><div class="card-header"><h3>${t('report.all')}</h3></div><p style="font-size:13px;color:var(--ab-text-secondary);margin-bottom:12px">${t('report.all_desc')}</p><button class="btn btn-primary" onclick="exportReport('all')">${t('report.export_btn')} All</button></div>
    </div>
    <div id="exportResult" style="margin-top:16px"></div>`;
}

async function exportReport(type) {
  const t = (k) => I18N.t(k);
  const params = { type, include_interpretation:true, include_storyline:true, include_figures:true, project_id: window._loadedData?.project_id||'current' };
  const el = document.getElementById('exportResult'); el.innerHTML = '<div class="card" style="text-align:center"><div class="spinner"></div><p style="margin-top:8px;color:var(--ab-text-secondary)">Generating report...</p></div>';
  try {
    const data = await API.reportExport(params);
    el.innerHTML = data.files?.length ? '<div class="card"><div class="card-header"><h3>' + t('report.complete') + '</h3></div><ul style="font-size:13px;line-height:2;padding-left:18px">' + data.files.map(f => '<li>' + f.name + ' <span class="badge badge-success">' + (f.size||'') + '</span> -> ' + f.path + '</li>').join('') + '</ul><p style="font-size:12px;color:var(--ab-text-secondary);margin-top:8px">Files saved to: ' + (data.output_dir||'output/') + '</p></div>' : '<div class="alert alert-warning">Export completed but no files were generated.</div>';
  } catch(e) { el.innerHTML = '<div class="alert alert-error">' + t('data.detection_failed') + ': ' + e.message + '</div>'; }
}
