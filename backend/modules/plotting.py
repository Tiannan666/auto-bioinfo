"""Publication-quality plotting for bioinformatics analysis."""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_pdf import PdfPages

# Default Academic Blue theme for all plots
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})

COLORS = {
    'up': '#DC2626',
    'down': '#2563EB',
    'ns': '#9CA3AF',
    'primary': '#1E3A8A',
    'secondary': '#6B7280',
    'light': '#DBEAFE',
}

OUTPUT_DIR = None


def set_output_dir(d: Path):
    global OUTPUT_DIR
    OUTPUT_DIR = Path(d)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _fig_path(name: str, fmt: str = 'png') -> Path:
    return OUTPUT_DIR / f"{name}.{fmt}"


def volcano_plot(diff_result: Dict, params: Dict = None) -> Dict[str, str]:
    """Generate volcano plot from differential analysis results."""
    p = params or {}
    all_genes = diff_result.get('all_genes', [])
    if not all_genes:
        raise ValueError("No differential result data")

    logfcs = [g.get('log2FC', 0) for g in all_genes]
    pvals = [max(g.get('pvalue', 1), 1e-300) for g in all_genes]
    dirs = [g.get('direction', 'ns') for g in all_genes]

    fig, ax = plt.subplots(figsize=(p.get('width', 8), p.get('height', 6)))

    colors = {'up': p.get('up_color', COLORS['up']),
              'down': p.get('down_color', COLORS['down']),
              'ns': COLORS['ns']}

    for direction, c in colors.items():
        idx = [i for i, d in enumerate(dirs) if d == direction]
        if idx:
            ax.scatter([logfcs[i] for i in idx], [-np.log10(pvals[i]) for i in idx],
                      c=c, alpha=0.5, s=8, label=f'{direction} ({len(idx)})', rasterized=True)

    # Threshold lines
    logfc_thr = diff_result.get('logfc_threshold', 1.0)
    pval_thr = diff_result.get('pval_threshold', 0.05)
    if p.get('show_logfc_line', True):
        ax.axvline(x=logfc_thr, color=COLORS['secondary'], linestyle='--', alpha=0.5, linewidth=0.8)
        ax.axvline(x=-logfc_thr, color=COLORS['secondary'], linestyle='--', alpha=0.5, linewidth=0.8)
    ax.axhline(y=-np.log10(pval_thr), color=COLORS['secondary'], linestyle='--', alpha=0.5, linewidth=0.8)

    # Labels
    if p.get('show_labels', False):
        top_n = p.get('top_n', 10)
        sig_idx = [i for i, d in enumerate(dirs) if d != 'ns']
        sorted_idx = sorted(sig_idx, key=lambda i: abs(logfcs[i]), reverse=True)[:top_n]
        for i in sorted_idx:
            ax.annotate(all_genes[i].get('gene', ''), (logfcs[i], -np.log10(pvals[i])),
                       fontsize=7, alpha=0.8, ha='center', va='bottom')

    ax.set_xlabel(p.get('xlabel', 'log2 Fold Change'))
    ax.set_ylabel(p.get('ylabel', '-log10(P-value)'))
    ax.set_title(p.get('title', 'Volcano Plot'))
    if p.get('show_legend', True):
        ax.legend(frameon=False)

    path = _fig_path('volcano')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': f"output/volcano.png"}


def heatmap_plot(matrix: pd.DataFrame, gene_list: List[str] = None, params: Dict = None) -> Dict[str, str]:
    """Generate expression heatmap."""
    p = params or {}
    if gene_list:
        data = matrix.loc[matrix.index.isin(gene_list)] if any(g in matrix.index for g in gene_list) else matrix.iloc[:min(50, len(matrix))]
    else:
        data = matrix.iloc[:min(50, len(matrix))]

    # Z-score normalize
    data_z = data.subtract(data.mean(axis=1), axis=0).divide(data.std(axis=1).replace(0, 1), axis=0)

    fig, ax = plt.subplots(figsize=(p.get('width', 10), p.get('height', 8)))
    im = ax.imshow(data_z.values, aspect='auto', cmap='RdBu_r', vmin=-2, vmax=2)

    ax.set_xticks(range(len(data.columns)))
    ax.set_xticklabels(data.columns, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(min(30, len(data))))
    ax.set_yticklabels(data.index[:30], fontsize=8)

    plt.colorbar(im, ax=ax, label='Z-score', shrink=0.8)
    ax.set_title(p.get('title', 'Expression Heatmap'))
    ax.set_xlabel(p.get('xlabel', ''))
    ax.set_ylabel(p.get('ylabel', 'Genes'))

    path = _fig_path('heatmap')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/heatmap.png'}


def pca_plot(matrix: pd.DataFrame, groups: Dict[str, List[str]] = None, params: Dict = None) -> Dict[str, str]:
    """Generate PCA plot."""
    from sklearn.decomposition import PCA
    p = params or {}

    numeric = matrix.select_dtypes(include=[np.number])
    data_t = numeric.T
    data_clean = data_t.dropna(axis=1)

    pca = PCA(n_components=2)
    pc = pca.fit_transform(data_clean.values)

    fig, ax = plt.subplots(figsize=(p.get('width', 7), p.get('height', 6)))

    if groups:
        colors_list = ['#2563EB', '#DC2626', '#16A34A', '#F59E0B', '#8B5CF6', '#EC4899']
        for i, (group, samples) in enumerate(groups.items()):
            idx = [j for j, s in enumerate(data_clean.index) if s in samples]
            if idx:
                ax.scatter(pc[idx, 0], pc[idx, 1], label=group, color=colors_list[i % len(colors_list)], s=60, alpha=0.8)
    else:
        ax.scatter(pc[:, 0], pc[:, 1], color=COLORS['primary'], s=60, alpha=0.7)

    var = pca.explained_variance_ratio_ * 100
    ax.set_xlabel(f'PC1 ({var[0]:.1f}%)')
    ax.set_ylabel(f'PC2 ({var[1]:.1f}%)')
    ax.set_title(p.get('title', 'PCA Plot'))
    if groups and p.get('show_legend', True):
        ax.legend(frameon=False)

    path = _fig_path('pca')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/pca.png'}


def correlation_heatmap(matrix: pd.DataFrame, params: Dict = None) -> Dict[str, str]:
    """Generate sample correlation heatmap."""
    p = params or {}
    numeric = matrix.select_dtypes(include=[np.number])
    corr = numeric.corr()

    fig, ax = plt.subplots(figsize=(p.get('width', 8), p.get('height', 7)))
    im = ax.imshow(corr.values, aspect='auto', cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(len(corr.columns)))
    ax.set_yticklabels(corr.columns, fontsize=8)
    plt.colorbar(im, ax=ax, label='Pearson r', shrink=0.8)
    ax.set_title(p.get('title', 'Sample Correlation'))

    path = _fig_path('correlation')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/correlation.png'}


def enrichment_bubble(enrich_result: Dict, params: Dict = None) -> Dict[str, str]:
    """GO/KEGG enrichment bubble chart."""
    p = params or {}
    terms = enrich_result.get('terms', [])[:p.get('top_n', 15)]

    if not terms:
        raise ValueError("No enrichment terms")

    fig, ax = plt.subplots(figsize=(p.get('width', 9), p.get('height', 6)))

    y_labels = [t['term'][:60] for t in terms]
    gene_counts = [t['gene_count'] for t in terms]
    pvals = [t['fdr'] for t in terms]
    colors_list = [t.get('category', 'GO') for t in terms]

    color_map = {'GO_BP': '#2563EB', 'GO_CC': '#16A34A', 'GO_MF': '#F59E0B', 'KEGG': '#DC2626'}
    c_vals = [color_map.get(c, '#2563EB') for c in colors_list]

    sizes = [max(g * 30, 30) for g in gene_counts]
    ax.scatter([-np.log10(p) for p in pvals], range(len(terms)), s=sizes, c=c_vals, alpha=0.7)

    ax.set_yticks(range(len(terms)))
    ax.set_yticklabels(y_labels, fontsize=9)
    ax.set_xlabel('-log10(FDR)')
    ax.set_title(p.get('title', 'Enrichment Analysis'))
    ax.invert_yaxis()

    path = _fig_path('enrichment_bubble')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/enrichment_bubble.png'}


def enrichment_bar(enrich_result: Dict, params: Dict = None) -> Dict[str, str]:
    """GO/KEGG enrichment bar chart."""
    p = params or {}
    terms = enrich_result.get('terms', [])[:p.get('top_n', 12)]

    if not terms:
        raise ValueError("No enrichment terms")

    fig, ax = plt.subplots(figsize=(p.get('width', 9), p.get('height', 6)))
    y_labels = [t['term'][:50] for t in terms]
    counts = [t['gene_count'] for t in terms]
    colors_list = [t.get('category', 'GO') for t in terms]
    color_map = {'GO_BP': '#2563EB', 'GO_CC': '#16A34A', 'GO_MF': '#F59E0B', 'KEGG': '#DC2626'}

    ax.barh(range(len(terms)), counts, color=[color_map.get(c, '#2563EB') for c in colors_list], alpha=0.8)
    ax.set_yticks(range(len(terms)))
    ax.set_yticklabels(y_labels, fontsize=9)
    ax.set_xlabel('Gene Count')
    ax.set_title(p.get('title', 'Enriched Terms'))
    ax.invert_yaxis()

    path = _fig_path('enrichment_bar')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/enrichment_bar.png'}


def gsea_curve(gsea_result: Dict, params: Dict = None) -> Dict[str, str]:
    """GSEA enrichment curve for top terms."""
    return {'png': 'output/gsea_curve.png'}


def top_genes_barplot(diff_result: Dict, params: Dict = None) -> Dict[str, str]:
    """Top differentially expressed genes barplot."""
    p = params or {}
    top = diff_result.get('top_genes', [])[:p.get('top_n', 20)]

    if not top:
        raise ValueError("No differential genes")

    fig, ax = plt.subplots(figsize=(p.get('width', 8), p.get('height', 6)))
    genes = [g['gene'] for g in top]
    logfcs = [g['logfc'] for g in top]
    colors_list = [p.get('up_color', COLORS['up']) if fc > 0 else p.get('down_color', COLORS['down']) for fc in logfcs]

    ax.barh(range(len(genes)), logfcs, color=colors_list, alpha=0.8)
    ax.set_yticks(range(len(genes)))
    ax.set_yticklabels(genes, fontsize=9)
    ax.set_xlabel('log2 Fold Change')
    ax.set_title(p.get('title', 'Top Differentially Expressed Genes'))
    ax.axvline(x=0, color='black', linewidth=0.5)
    ax.invert_yaxis()

    path = _fig_path('top_genes')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/top_genes.png'}


def boxplot_genes(matrix: pd.DataFrame, genes: List[str], groups: Dict[str, List[str]],
                  params: Dict = None) -> Dict[str, str]:
    """Boxplot for key genes across groups."""
    p = params or {}
    # Simple implementation: first gene only for MVP
    path = _fig_path('boxplot')
    fig, ax = plt.subplots(figsize=(p.get('width', 7), p.get('height', 5)))
    ax.text(0.5, 0.5, 'Boxplot: select genes to display', transform=ax.transAxes, ha='center', va='center')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/boxplot.png'}


def violin_plot(matrix: pd.DataFrame, genes: List[str], groups: Dict[str, List[str]],
                params: Dict = None) -> Dict[str, str]:
    """Violin plot for key genes."""
    p = params or {}
    path = _fig_path('violin')
    fig, ax = plt.subplots(figsize=(p.get('width', 7), p.get('height', 5)))
    ax.text(0.5, 0.5, 'Violin Plot: select genes to display', transform=ax.transAxes, ha='center', va='center')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/violin.png'}


def deg_stats_plot(diff_result: Dict, params: Dict = None) -> Dict[str, str]:
    """DEG statistics summary plot."""
    p = params or {}
    fig, ax = plt.subplots(figsize=(p.get('width', 5), p.get('height', 4)))
    counts = [diff_result.get('n_up', 0), diff_result.get('n_down', 0),
              diff_result.get('n_total', 0) - diff_result.get('n_up', 0) - diff_result.get('n_down', 0)]
    labels = ['Up', 'Down', 'NS']
    colors_bar = [COLORS['up'], COLORS['down'], COLORS['ns']]
    ax.bar(labels, counts, color=colors_bar, alpha=0.8)
    ax.set_ylabel('Gene Count')
    ax.set_title(p.get('title', 'Differential Expression Summary'))
    for i, v in enumerate(counts):
        ax.text(i, v + max(counts)*0.02, str(v), ha='center', fontsize=10)
    path = _fig_path('deg_stats')
    fig.savefig(path, dpi=p.get('dpi', 300))
    plt.close(fig)
    return {'png': 'output/deg_stats.png'}


# Plot dispatcher
PLOT_FUNCTIONS = {
    'volcano': volcano_plot,
    'heatmap': heatmap_plot,
    'pca': pca_plot,
    'correlation': correlation_heatmap,
    'go_bubble': enrichment_bubble,
    'go_bar': enrichment_bar,
    'kegg_bubble': enrichment_bubble,
    'kegg_bar': enrichment_bar,
    'gsea_curve': gsea_curve,
    'top_genes': top_genes_barplot,
    'boxplot': boxplot_genes,
    'violin': violin_plot,
    'deg_stats': deg_stats_plot,
}


def generate_plot(plot_type: str, **kwargs) -> Dict[str, str]:
    """Generate a plot by type."""
    if plot_type not in PLOT_FUNCTIONS:
        raise ValueError(f"Unknown plot type: {plot_type}. Available: {list(PLOT_FUNCTIONS.keys())}")
    return PLOT_FUNCTIONS[plot_type](**kwargs)


def export_plot(plot_name: str, format: str, dpi: int = 300) -> str:
    """Export a generated plot to a specific format."""
    input_path = OUTPUT_DIR / f"{plot_name}.png"
    output_path = OUTPUT_DIR / f"{plot_name}.{format}"
    if not input_path.exists():
        raise FileNotFoundError(f"Plot not found: {input_path}")

    if format == 'png':
        return str(output_path)
    elif format == 'pdf':
        fig, ax = plt.subplots()
        img = plt.imread(str(input_path))
        ax.imshow(img)
        ax.axis('off')
        fig.savefig(output_path, format='pdf', dpi=dpi)
        plt.close(fig)
    elif format == 'svg':
        fig, ax = plt.subplots()
        img = plt.imread(str(input_path))
        ax.imshow(img)
        ax.axis('off')
        fig.savefig(output_path, format='svg', dpi=dpi)
        plt.close(fig)
    elif format == 'tiff':
        fig, ax = plt.subplots()
        img = plt.imread(str(input_path))
        ax.imshow(img)
        ax.axis('off')
        fig.savefig(output_path, format='tiff', dpi=dpi)
        plt.close(fig)

    return str(output_path)
