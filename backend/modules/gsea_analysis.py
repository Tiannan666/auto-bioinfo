"""GSEA (Gene Set Enrichment Analysis) implementation."""

import numpy as np
from typing import Dict, List

from .enrichment import GO_SETS, KEGG_PATHWAYS


def run_gsea(ranked_genes: List[str], scores: List[float],
             gene_set_type: str = 'go', pval_cutoff: float = 0.05) -> Dict:
    """
    Run GSEA on pre-ranked gene list.
    ranked_genes: gene symbols in ranked order (most up first)
    scores: ranking metric values (e.g., log2FC or -log10(pval)*sign(logFC))
    """

    if len(ranked_genes) != len(scores):
        raise ValueError("ranked_genes and scores must have the same length")

    # Build gene sets
    all_gene_sets = {}
    if gene_set_type in ('go', 'all'):
        for ont in GO_SETS.values():
            for term_id, genes in ont.items():
                all_gene_sets[term_id] = [g.upper() for g in genes]
    if gene_set_type in ('kegg', 'all'):
        all_gene_sets.update({k: [g.upper() for g in v] for k, v in KEGG_PATHWAYS.items()})

    # Build ranked list
    gene_rank = {g.upper(): i for i, g in enumerate(ranked_genes)}
    n_genes = len(ranked_genes)
    results = []

    for gs_name, gs_genes in all_gene_sets.items():
        # Find gene set members in ranked list
        hits = sorted([gene_rank[g] for g in gs_genes if g in gene_rank])
        if len(hits) < 3:
            continue

        nh = len(hits)
        # Running sum (simplified GSEA)
        running_sum, max_es, min_es = _compute_es(hits, n_genes, scores)
        es = max_es if abs(max_es) >= abs(min_es) else min_es

        # Permutation-based p-value (simplified: use parametric approximation)
        # Kolmogorov-Smirnov-like test
        from scipy import stats as scipy_stats
        # Approximate p-value using KS statistic
        nr = n_genes - nh
        ks_stat = abs(es)
        # Simple approximation
        pval = 2 * np.exp(-2 * ks_stat**2 * nh * nr / (nh + nr))
        pval = min(max(pval, 1e-10), 1.0)

        # Leading edge: hits before the peak
        if es > 0:
            peak_idx = hits[np.argmax(running_sum)] if len(running_sum) > 0 else hits[-1]
            leading_edge = [ranked_genes[i] for i in hits if i <= peak_idx]
        else:
            peak_idx = hits[np.argmin(running_sum)] if len(running_sum) > 0 else hits[-1]
            leading_edge = [ranked_genes[i] for i in hits if i <= peak_idx]

        nes = es / (np.std([np.random.normal(0, 0.1/np.sqrt(nh)) for _ in range(100)]) + 1e-10)

        results.append({
            "term": gs_name.split(" ", 1)[1] if " " in gs_name else gs_name,
            "id": gs_name.split(" ", 1)[0] if " " in gs_name else gs_name,
            "es": round(es, 4),
            "nes": round(nes, 4),
            "pvalue": round(pval, 6),
            "fdr": 1.0,
            "leading_edge": leading_edge[:15],
            "n_hits": nh,
            "total_genes": len(gs_genes),
        })

    # Multiple testing correction
    results.sort(key=lambda x: x["pvalue"])
    n = len(results)
    for i, r in enumerate(results):
        r["fdr"] = round(min(r["pvalue"] * n / max(i + 1, 1), 1.0), 6)
    for i in range(n - 2, -1, -1):
        results[i]["fdr"] = min(results[i]["fdr"], results[i + 1]["fdr"])

    significant = [r for r in results if r["fdr"] < pval_cutoff]

    return {
        "type": "gsea",
        "gene_set_type": gene_set_type,
        "terms": significant[:30],
        "n_terms": len(significant),
        "n_total_terms": len(results),
    }


def _compute_es(hits: List[int], n_genes: int, scores: List[float]) -> tuple:
    """Compute enrichment score running sum."""
    nh = len(hits)
    nr = n_genes - nh

    # Hit increment and miss decrement
    hit_inc = 1.0 / nh if nh > 0 else 0
    miss_dec = 1.0 / nr if nr > 0 else 0

    running_sum = np.zeros(n_genes)
    current = 0.0
    for i in range(n_genes):
        if i in hits:
            current += hit_inc
        else:
            current -= miss_dec
        running_sum[i] = current

    return running_sum, np.max(running_sum), np.min(running_sum)
