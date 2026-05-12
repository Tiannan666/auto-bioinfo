// scRNA-seq Placeholder Page
function renderScrna() {
  const t = (k) => I18N.t(k);
  const features = [
    '10x Genomics data import', 'Quality control & filtering', 'Normalization & HVG selection',
    'Dimensionality reduction (PCA/UMAP)', 'Cell clustering (Leiden/Louvain)', 'Cell type annotation',
    'Marker gene analysis', 'DotPlot & FeaturePlot', 'ViolinPlot & StackedViolin',
    'Cell proportion analysis', 'Gene set scoring (AUCell/ssGSEA)', 'Pseudotime trajectory analysis',
    'Cell-cell communication (CellChat)', 'Sub-clustering & re-analysis', 'Differential expression by cluster',
    'Multi-sample integration (Harmony/CCA)',
  ];
  return '<div class="coming-soon"><div class="icon">---</div><h3>' + t('scrna.title') + '</h3><p>' + t('scrna.desc') + '</p>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px;text-align:left;max-width:500px">' +
    features.map(f => '<div style="font-size:12px;color:var(--ab-text-secondary);padding:4px 8px;background:var(--ab-light-bg);border-radius:4px">... ' + f + '</div>').join('') + '</div></div>';
}
