"""
GO/KEGG enrichment using real gene set databases + hypergeometric test.
Backed by NCBI gene2go, KEGG REST API, and MSigDB Hallmark.
"""

import numpy as np
from scipy import stats as scipy_stats
from statsmodels.stats.multitest import multipletests
from typing import Dict, List

from .gene_database import get_go_sets, get_kegg_sets, get_msigdb_sets, get_all_gene_sets, get_background_size


def run_enrichment(gene_list: List[str], pval_cutoff: float = 0.05,
                   go_bp: bool = True, go_cc: bool = True, go_mf: bool = True,
                   kegg: bool = True, msigdb: bool = False) -> Dict:
    """
    Run hypergeometric enrichment using real gene set databases.

    Returns q-values (Storey) in addition to BH-FDR.
    """

    gene_set_input = set(g.upper().strip() for g in gene_list)
    n_query = len(gene_set_input)
    total_bg = get_background_size()
    results = []

    # GO enrichment
    if go_bp or go_cc or go_mf:
        categories = []
        if go_bp: categories.append('BP')
        if go_cc: categories.append('CC')
        if go_mf: categories.append('MF')
        go_all = get_go_sets(categories)

        for term_id, term_genes in go_all.items():
            term_set = set(g.upper().strip() for g in term_genes)
            overlap = gene_set_input & term_set
            if len(overlap) < 2:
                continue
            k = len(overlap)
            m = len(term_set)
            pval = scipy_stats.hypergeom.sf(k - 1, total_bg, m, n_query)
            cat = 'GO_BP'
            if 'GO:CC' in term_id or '(CC)' in term_id:
                cat = 'GO_CC'
            elif 'GO:MF' in term_id or '(MF)' in term_id:
                cat = 'GO_MF'
            results.append({
                'term': _extract_term_name(term_id),
                'id': _extract_term_id(term_id),
                'category': cat,
                'gene_count': k,
                'pvalue': pval,
                'fdr': 1.0,
                'qvalue': 1.0,
                'genes': sorted(overlap)[:15],
                'total_genes': m,
            })

    # KEGG enrichment
    if kegg:
        kegg_all = get_kegg_sets()
        for pathway, pathway_genes in kegg_all.items():
            term_set = set(g.upper().strip() for g in pathway_genes)
            overlap = gene_set_input & term_set
            if len(overlap) < 2:
                continue
            k = len(overlap)
            m = len(term_set)
            pval = scipy_stats.hypergeom.sf(k - 1, total_bg, m, n_query)
            results.append({
                'term': pathway,
                'id': pathway.split()[0] if ' ' in pathway else pathway,
                'category': 'KEGG',
                'gene_count': k,
                'pvalue': pval,
                'fdr': 1.0,
                'qvalue': 1.0,
                'genes': sorted(overlap)[:15],
                'total_genes': m,
            })

    # MSigDB Hallmark
    if msigdb:
        msig_all = get_msigdb_sets()
        for gs_name, gs_genes in msig_all.items():
            term_set = set(g.upper().strip() for g in gs_genes)
            overlap = gene_set_input & term_set
            if len(overlap) < 2:
                continue
            k = len(overlap)
            m = len(term_set)
            pval = scipy_stats.hypergeom.sf(k - 1, total_bg, m, n_query)
            results.append({
                'term': gs_name,
                'id': gs_name,
                'category': 'MSigDB_Hallmark',
                'gene_count': k,
                'pvalue': pval,
                'fdr': 1.0,
                'qvalue': 1.0,
                'genes': sorted(overlap)[:15],
                'total_genes': m,
            })

    if not results:
        return {'type': 'go_kegg_msigdb', 'terms': [], 'n_terms': 0, 'gene_count': n_query}

    # Sort by p-value
    results.sort(key=lambda x: x['pvalue'])

    # BH-FDR correction
    n = len(results)
    pvals = [r['pvalue'] for r in results]
    _, fdrs, _, _ = multipletests(pvals, alpha=pval_cutoff, method='fdr_bh')

    for i, r in enumerate(results):
        r['fdr'] = float(fdrs[i])

    # Storey q-value approximation
    bh_sorted = sorted(fdrs)
    for i, r in enumerate(results):
        idx = list(fdrs).index(r['fdr']) if r['fdr'] in fdrs else i
        pi0 = min(1.0, sum(1 for p in pvals if p > 0.5) / max(1, n * 0.5))
        r['qvalue'] = float(min(r['fdr'] * pi0, 1.0))

    # Filter by FDR
    significant = [r for r in results if r['fdr'] < pval_cutoff]

    return {
        'type': 'go_kegg_msigdb',
        'terms': significant[:200],
        'n_terms': len(significant),
        'gene_count': n_query,
        'total_background': total_bg,
    }


def _extract_term_name(term_id: str) -> str:
    """Extract human-readable name from GO term string."""
    if ' ' in term_id:
        return ' '.join(term_id.split(' ')[1:])
    return term_id


def _extract_term_id(term_id: str) -> str:
    """Extract GO ID from term string."""
    if ' ' in term_id:
        return term_id.split(' ')[0]
    return term_id
