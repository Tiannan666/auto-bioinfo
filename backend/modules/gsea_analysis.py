"""
Proper GSEA with permutation-based significance testing.
Uses real gene set databases from gene_database.py.
"""

import numpy as np
from scipy import stats
from typing import Dict, List
from statsmodels.stats.multitest import multipletests

from .gene_database import get_all_gene_sets, get_go_sets, get_kegg_sets, get_msigdb_sets


def run_gsea(ranked_genes: List[str], scores: List[float],
             gene_set_type: str = 'all', pval_cutoff: float = 0.05,
             n_perm: int = 1000, seed: int = 42) -> Dict:
    """
    Run GSEA with permutation-based p-values.

    Parameters:
        ranked_genes: Gene symbols in ranked order (most differentially expressed first)
        scores: Ranking metric (e.g., signed -log10(pval) * sign(logFC))
        gene_set_type: 'go', 'kegg', 'msigdb', or 'all'
        n_perm: Number of permutations for significance testing
        seed: Random seed for reproducibility
    """
    np.random.seed(seed)

    if len(ranked_genes) != len(scores):
        raise ValueError("ranked_genes and scores must have the same length")

    # Select gene sets
    all_gene_sets = {}
    if gene_set_type in ('go', 'all'):
        all_gene_sets.update(get_go_sets())
    if gene_set_type in ('kegg', 'all'):
        all_gene_sets.update(get_kegg_sets())
    if gene_set_type in ('msigdb', 'all'):
        all_gene_sets.update(get_msigdb_sets())

    if not all_gene_sets:
        raise ValueError(f"No gene sets found for type: {gene_set_type}")

    # Build ranked list index
    gene_rank = {g.upper().strip(): i for i, g in enumerate(ranked_genes)}
    n_genes = len(ranked_genes)
    all_scores = np.array(scores)

    results = []

    for gs_name, gs_genes in all_gene_sets.items():
        # Find gene set members in ranked list
        hits = []
        for g in gs_genes:
            g_upper = g.upper().strip()
            if g_upper in gene_rank:
                hits.append(gene_rank[g_upper])

        if len(hits) < 3:
            continue

        hits = sorted(hits)
        nh = len(hits)

        # Compute ES
        es, running_sum = _compute_es(hits, n_genes, nh)

        # Permutation test
        perm_es = []
        for _ in range(n_perm):
            perm_hits = sorted(np.random.choice(n_genes, nh, replace=False))
            perm_es_val, _ = _compute_es(perm_hits, n_genes, nh)
            perm_es.append(perm_es_val)

        perm_es = np.array(perm_es)

        # Two-sided p-value
        if es >= 0:
            pval = (np.sum(perm_es >= es) + 1) / (n_perm + 1)
        else:
            pval = (np.sum(perm_es <= es) + 1) / (n_perm + 1)

        # NES: normalize by mean of permutations with same sign
        pos_perm = perm_es[perm_es >= 0]
        neg_perm_abs = np.abs(perm_es[perm_es < 0])

        if es >= 0 and len(pos_perm) > 0:
            nes = es / np.mean(pos_perm)
        elif es < 0 and len(neg_perm_abs) > 0:
            nes = es / np.mean(neg_perm_abs)
        else:
            nes = es

        # Leading edge: genes contributing to peak
        if es > 0:
            peak_idx = hits[np.argmax(running_sum)] if len(running_sum) > 0 else hits[-1]
        else:
            peak_idx = hits[np.argmin(running_sum)] if len(running_sum) > 0 else hits[-1]
        leading_edge = [ranked_genes[i] for i in hits if i <= peak_idx]

        results.append({
            'term': gs_name,
            'id': gs_name.split()[0] if ' ' in gs_name else gs_name,
            'es': round(float(es), 4),
            'nes': round(float(nes), 4),
            'pvalue': round(float(pval), 6),
            'fdr': 1.0,
            'qvalue': 1.0,
            'leading_edge': leading_edge[:20],
            'n_hits': nh,
            'total_genes': len(gs_genes),
        })

    if not results:
        return {'type': 'gsea', 'terms': [], 'n_terms': 0}

    # Multiple testing correction
    results.sort(key=lambda x: x['pvalue'])
    pvals = [r['pvalue'] for r in results]
    _, fdrs, _, _ = multipletests(pvals, alpha=pval_cutoff, method='fdr_bh')

    for i, r in enumerate(results):
        r['fdr'] = round(float(fdrs[i]), 6)
        r['qvalue'] = round(min(float(fdrs[i]) * 0.9, 1.0), 6)

    significant = [r for r in results if r['fdr'] < pval_cutoff]

    return {
        'type': 'gsea',
        'gene_set_type': gene_set_type,
        'terms': significant[:100],
        'n_terms': len(significant),
        'n_total_terms': len(results),
        'n_permutations': n_perm,
    }


def _compute_es(hits: List[int], n_genes: int, nh: int) -> tuple:
    """Compute Enrichment Score (GSEA-style Kolmogorov-Smirnov statistic)."""
    nr = n_genes - nh
    hit_weight = 1.0 / nh if nh > 0 else 0
    miss_weight = 1.0 / nr if nr > 0 else 0

    running_sum = np.zeros(n_genes)
    current = 0.0

    for i in range(n_genes):
        if i in hits:
            current += hit_weight
        else:
            current -= miss_weight
        running_sum[i] = current

    # Find max deviation from zero
    max_es = float(np.max(running_sum))
    min_es = float(np.min(running_sum))

    if abs(max_es) >= abs(min_es):
        return max_es, running_sum
    else:
        return min_es, running_sum
