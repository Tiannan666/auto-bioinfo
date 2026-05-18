"""Immune cell infiltration estimation via ssGSEA."""

import numpy as np
import pandas as pd
from typing import Dict, List

IMMUNE_SIGNATURES = {
    'B cells naive': ['BLK', 'CD19', 'FCRL2', 'MS4A1', 'KIAA0125', 'TNFRSF17', 'TCL1A', 'SPIB', 'PNOC'],
    'B cells memory': ['AIM2', 'BANK1', 'BLK', 'CD19', 'CD79A', 'CD79B', 'CR2', 'HVCN1', 'MS4A1'],
    'Plasma cells': ['IGHA1', 'IGHG1', 'IGKC', 'IGLC1', 'IGLC2', 'JCHAIN', 'MZB1', 'SDC1', 'TNFRSF17'],
    'T cells CD8': ['CD8A', 'CD8B', 'GZMK', 'GZMA', 'PRF1', 'NKG7', 'IFNG', 'CXCR3'],
    'T cells CD4 naive': ['CCR7', 'IL7R', 'LEF1', 'MAL', 'SELL', 'TCF7'],
    'T cells CD4 memory': ['IL2RA', 'IL7R', 'CD40LG', 'ICOS', 'CCR4', 'CD44'],
    'T cells follicular helper': ['CXCL13', 'CXCR5', 'ICOS', 'IL21', 'PDCD1', 'SH2D1A', 'BCL6'],
    'T cells regulatory (Tregs)': ['FOXP3', 'IL2RA', 'CTLA4', 'IKZF2', 'TNFRSF18', 'CCR8'],
    'T cells gamma delta': ['TRGC1', 'TRGC2', 'TRDC', 'TRDV1', 'TRDV2', 'KLRC1'],
    'NK cells resting': ['KIR2DL1', 'KIR2DL3', 'KIR3DL1', 'KIR3DL2', 'NCAM1'],
    'NK cells activated': ['GZMB', 'GNLY', 'NKG7', 'PRF1', 'KLRD1', 'KLRK1', 'FGFBP2'],
    'Monocytes': ['CD14', 'VCAN', 'S100A8', 'S100A9', 'FCN1', 'LYZ', 'MNDA'],
    'Macrophages M0': ['CD68', 'CD163', 'CSF1R', 'MSR1', 'MRC1'],
    'Macrophages M1': ['CCL2', 'CCL3', 'CCL4', 'CXCL10', 'IDO1', 'IL1B', 'NOS2', 'TNF'],
    'Macrophages M2': ['CCL18', 'CD163', 'MRC1', 'MSR1', 'IL10', 'TGFB1', 'ARG1'],
    'Dendritic cells resting': ['CCL13', 'CD1C', 'CD1E', 'HSD11B1', 'PKIB'],
    'Dendritic cells activated': ['CCL17', 'CCL22', 'CD40', 'CD80', 'CD83', 'CD86', 'LAMP3'],
    'Mast cells resting': ['CPA3', 'HDC', 'MS4A2', 'TPSAB1', 'TPSB2'],
    'Mast cells activated': ['CMA1', 'CTSG', 'IL4', 'MS4A2', 'TPSAB1'],
    'Eosinophils': ['CCR3', 'CLC', 'IL5RA', 'PRG2', 'SIGLEC8'],
    'Neutrophils': ['CEACAM8', 'CSF3R', 'CXCR1', 'CXCR2', 'FCGR3B', 'FPR1', 'S100A12'],
    'Fibroblasts': ['COL1A1', 'COL1A2', 'COL3A1', 'DCN', 'LUM', 'FAP', 'PDGFRA'],
}


def ssgsea_score(expression: pd.DataFrame, gene_set: List[str]) -> pd.Series:
    """Calculate ssGSEA enrichment score for one gene set across all samples."""
    ranks = expression.rank(ascending=False, method='min')
    overlap = [g for g in gene_set if g in ranks.index]
    if len(overlap) < 3:
        return pd.Series(0.0, index=expression.columns)

    n = len(ranks)
    n_hit = len(overlap)
    miss_penalty = 1.0 / (n - n_hit) if n > n_hit else 0.0
    scores = pd.Series(0.0, index=expression.columns)

    for sample in expression.columns:
        r = ranks[sample]
        sorted_genes = r.sort_values().index
        hit_set = set(overlap)
        hit_weights = np.abs(r[overlap].values) ** 0.25
        hit_sum = hit_weights.sum()
        if hit_sum == 0:
            continue

        hit_weight_map = dict(zip(overlap, hit_weights))
        running = 0.0
        max_dev = 0.0

        for gene in sorted_genes:
            if gene in hit_set:
                running += hit_weight_map[gene] / hit_sum
            else:
                running -= miss_penalty
            if abs(running) > abs(max_dev):
                max_dev = running

        scores[sample] = max_dev

    return scores


def run_immune_infiltration(expression: pd.DataFrame, method: str = 'ssgsea') -> Dict:
    """Run immune infiltration analysis on expression matrix."""
    if expression.index.name != 'gene' and 'gene' in expression.columns:
        expression = expression.set_index('gene')

    expr_num = expression.select_dtypes(include=['number'])
    if expr_num.empty:
        raise ValueError("No numeric columns found in expression matrix")

    results = {}
    for cell_type, genes in IMMUNE_SIGNATURES.items():
        results[cell_type] = ssgsea_score(expr_num, genes)

    score_df = pd.DataFrame(results).T

    score_range = score_df.max(axis=1) - score_df.min(axis=1)
    score_norm = score_df.sub(score_df.min(axis=1), axis=0).div(score_range + 1e-10, axis=0)

    return {
        'type': 'immune_infiltration',
        'method': method,
        'cell_types': list(score_df.index),
        'samples': list(score_df.columns),
        'scores': score_df.to_dict(orient='index'),
        'scores_normalized': score_norm.to_dict(orient='index'),
        'n_cell_types': len(score_df),
        'n_samples': len(score_df.columns),
    }
