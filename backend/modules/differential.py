"""Differential expression analysis using t-test, Wilcoxon, and limma-like methods."""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List


def run_differential(matrix: pd.DataFrame, group1_samples: List[str], group2_samples: List[str],
                     method: str = 'ttest', logfc_threshold: float = 1.0,
                     pval_threshold: float = 0.05, fdr_threshold: float = 0.05,
                     log2_transform: bool = True, filter_low: bool = True) -> Dict:
    """Run differential expression analysis."""

    numeric_cols = matrix.select_dtypes(include=[np.number]).columns.tolist()
    g1 = [c for c in group1_samples if c in numeric_cols]
    g2 = [c for c in group2_samples if c in numeric_cols]

    if len(g1) < 2 or len(g2) < 2:
        raise ValueError(f"Need at least 2 samples per group. Group1: {len(g1)}, Group2: {len(g2)}")

    data = matrix.copy()
    numeric = data.select_dtypes(include=[np.number])

    # Log2 transform
    if log2_transform:
        vals = numeric.values.flatten()
        vals = vals[~np.isnan(vals)]
        if len(vals) > 0 and np.mean(vals) > 20:
            numeric = np.log2(numeric.clip(lower=0) + 1)

    # Filter low expression
    if filter_low:
        keep = (numeric >= 1).sum(axis=1) >= min(3, len(g1 + g2) // 2)
        data = data.loc[keep]
        numeric = data.select_dtypes(include=[np.number])

    # Run test per gene
    results = []
    for gene, row in data.iterrows():
        vals1 = row[g1].astype(float).dropna()
        vals2 = row[g2].astype(float).dropna()

        if len(vals1) < 2 or len(vals2) < 2:
            continue

        mean1, mean2 = vals1.mean(), vals2.mean()
        logfc = mean1 - mean2  # For log2 data, this is log2FC

        try:
            if method == 'ttest':
                stat, pval = stats.ttest_ind(vals1, vals2, equal_var=False)
            elif method == 'wilcoxon':
                stat, pval = stats.mannwhitneyu(vals1, vals2, alternative='two-sided')
            elif method == 'limma':
                stat, pval = _moderated_t(vals1, vals2)
            else:
                stat, pval = stats.ttest_ind(vals1, vals2, equal_var=False)
        except Exception:
            pval = 1.0
            stat = 0

        results.append({
            'gene': gene,
            'mean_group1': mean1,
            'mean_group2': mean2,
            'log2FC': logfc,
            'statistic': stat,
            'pvalue': pval,
        })

    if not results:
        raise ValueError("No genes could be tested. Check your data and group assignments.")

    result_df = pd.DataFrame(results)

    # Multiple testing correction (Benjamini-Hochberg)
    pvals = result_df['pvalue'].values
    n = len(pvals)
    ranked = np.argsort(pvals)
    fdr = np.ones(n)
    for i, idx in enumerate(ranked):
        fdr[idx] = min(pvals[idx] * n / (i + 1), 1.0)
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        fdr[ranked[i]] = min(fdr[ranked[i]], fdr[ranked[i + 1]])
    result_df['fdr'] = fdr

    # Classify
    result_df['direction'] = 'ns'
    sig_up = (result_df['fdr'] < fdr_threshold) & (result_df['log2FC'] >= logfc_threshold)
    sig_down = (result_df['fdr'] < fdr_threshold) & (result_df['log2FC'] <= -logfc_threshold)
    result_df.loc[sig_up, 'direction'] = 'up'
    result_df.loc[sig_down, 'direction'] = 'down'

    # Sort by significance
    result_df = result_df.sort_values('pvalue')

    # Prepare output
    top_genes = result_df[result_df['direction'] != 'ns'].head(50)
    all_genes_list = result_df.to_dict('records')
    up_genes = result_df[result_df['direction'] == 'up']
    down_genes = result_df[result_df['direction'] == 'down']

    return {
        "n_total": len(result_df),
        "n_up": len(up_genes),
        "n_down": len(down_genes),
        "n_sig": len(up_genes) + len(down_genes),
        "logfc_threshold": logfc_threshold,
        "pval_threshold": pval_threshold,
        "fdr_threshold": fdr_threshold,
        "method": method,
        "group1": group1_samples,
        "group2": group2_samples,
        "group1_name": "Group1",
        "group2_name": "Group2",
        "top_genes": top_genes[['gene', 'log2FC', 'pvalue', 'fdr', 'direction']].rename(
            columns={'log2FC': 'logfc', 'pvalue': 'pval'}).to_dict('records'),
        "all_genes": all_genes_list,
        "up_genes": up_genes['gene'].tolist(),
        "down_genes": down_genes['gene'].tolist(),
        "sig_genes": result_df[result_df['direction'] != 'ns']['gene'].tolist(),
    }


def _moderated_t(vals1, vals2) -> tuple:
    """Simplified moderated t-test (limma-like empirical Bayes shrinkage)."""
    n1, n2 = len(vals1), len(vals2)
    v1, v2 = vals1.var(ddof=1) if n1 > 1 else 0, vals2.var(ddof=1) if n2 > 1 else 0
    # Pooled variance with small prior
    prior_df = 3
    prior_var = 0.01
    pooled = ((n1 - 1) * v1 + (n2 - 1) * v2 + prior_df * prior_var) / (n1 + n2 - 2 + prior_df)
    se = np.sqrt(pooled * (1/n1 + 1/n2))
    if se < 1e-10:
        se = 1e-10
    t_stat = (vals1.mean() - vals2.mean()) / se
    df = n1 + n2 - 2 + prior_df
    pval = 2 * stats.t.sf(abs(t_stat), df)
    return t_stat, pval
