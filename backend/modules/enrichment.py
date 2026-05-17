"""GO/KEGG/Hallmark enrichment via hypergeometric test. Pure Python, no R dependency."""

from scipy import stats as scipy_stats
from statsmodels.stats.multitest import multipletests
from typing import Dict, List

from .gene_database import get_all_gene_sets, get_background_size


def run_enrichment(gene_list: List[str], pval_cutoff: float = 0.05,
                   go_bp: bool = True, go_cc: bool = True, go_mf: bool = True,
                   kegg: bool = True, msigdb: bool = False) -> Dict:
    if not gene_list:
        return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': 0}

    all_sets = get_all_gene_sets()
    gene_set = set(g.upper().strip() for g in gene_list)
    bg = get_background_size()
    n_query = len(gene_set)
    results = []

    for term_id, term_genes in all_sets.items():
        term_set = set(g.upper().strip() for g in term_genes)
        overlap = gene_set & term_set
        if len(overlap) < 2:
            continue
        pval = scipy_stats.hypergeom.sf(len(overlap) - 1, bg, len(term_set), n_query)
        # Category detection
        cat = 'GO'
        if 'HALLMARK' in term_id.upper():
            cat = 'MSigDB_Hallmark'
        elif term_id.startswith('hsa') or 'KEGG' in term_id.upper():
            cat = 'KEGG'
        results.append({
            'term': term_id,
            'id': term_id.split()[0] if ' ' in term_id else term_id,
            'category': cat,
            'gene_count': len(overlap),
            'pvalue': float(pval),
            'fdr': 1.0,
            'qvalue': 1.0,
            'genes': sorted(overlap)[:15],
            'total_genes': len(term_set),
        })

    if not results:
        return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': n_query}

    # Sort by p-value, apply BH correction
    results.sort(key=lambda x: x['pvalue'])
    pvals = [r['pvalue'] for r in results]
    _, fdrs, _, _ = multipletests(pvals, alpha=pval_cutoff, method='fdr_bh')
    for i, r in enumerate(results):
        r['fdr'] = float(fdrs[i])
        # Storey q-value approximation
        pi0 = min(1.0, sum(1 for p in pvals if p > 0.5) / max(1, len(pvals) * 0.5))
        r['qvalue'] = min(r['fdr'] * pi0, 1.0)

    significant = [r for r in results if r['fdr'] < pval_cutoff]
    return {
        'type': 'go_kegg_msigdb',
        'terms': significant[:200],
        'n_terms': len(significant),
        'gene_count': n_query,
        'total_background': bg,
    }
