"""
Differential expression analysis with DESeq2-like normalization,
dispersion estimation, and proper RNA-seq statistical methods.
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple


def run_differential(matrix: pd.DataFrame, group1_samples: List[str], group2_samples: List[str],
                     method: str = 'deseq2', logfc_threshold: float = 1.0,
                     pval_threshold: float = 0.05, fdr_threshold: float = 0.05,
                     log2_transform: bool = False, filter_low: bool = True,
                     min_count: int = 10, min_samples: int = 3) -> Dict:
    """
    Run differential expression analysis.

    Methods:
        - 'deseq2': DESeq2-like (median-of-ratios normalization + dispersion estimation)
        - 'ttest': Welch t-test on log2-transformed data
        - 'wilcoxon': Mann-Whitney U test
        - 'limma': limma-like moderated t-test
    """

    numeric_cols = matrix.select_dtypes(include=[np.number]).columns.tolist()
    g1 = [c for c in group1_samples if c in numeric_cols]
    g2 = [c for c in group2_samples if c in numeric_cols]

    if len(g1) < 2 or len(g2) < 2:
        raise ValueError(f"Need at least 2 samples per group. Group1: {len(g1)}, Group2: {len(g2)}")

    data = matrix.copy()

    # Filter low expression
    if filter_low:
        numeric = data.select_dtypes(include=[np.number])
        keep = (numeric >= min_count).sum(axis=1) >= min(min_samples, len(g1 + g2) // 2)
        data = data.loc[keep]

    # Apply method
    if method == 'deseq2':
        norm_data = _deseq2_normalize(data, g1 + g2)
        results = _deseq2_test(norm_data, g1, g2)
    elif method == 'ttest':
        norm_data = _log2_cpm(data, g1 + g2)
        results = _ttest_genes(norm_data, g1, g2)
    elif method == 'wilcoxon':
        norm_data = _log2_cpm(data, g1 + g2)
        results = _wilcoxon_genes(norm_data, g1, g2)
    elif method == 'limma':
        norm_data = _log2_cpm(data, g1 + g2)
        results = _limma_genes(norm_data, g1, g2)
    else:
        norm_data = _log2_cpm(data, g1 + g2)
        results = _ttest_genes(norm_data, g1, g2)

    if not results:
        raise ValueError("No genes could be tested.")

    result_df = pd.DataFrame(results)

    # Multiple testing correction (BH)
    pvals = result_df['pvalue'].values
    _, fdrs, _, _ = multipletests(pvals, alpha=fdr_threshold, method='fdr_bh')
    result_df['fdr'] = fdrs

    # q-value approximation (Storey)
    pi0 = min(1.0, sum(1 for p in pvals if p > 0.5) / max(1, len(pvals) * 0.5))
    result_df['qvalue'] = [min(f * pi0, 1.0) for f in fdrs]

    # Classify
    result_df['direction'] = 'ns'
    sig_up = (result_df['fdr'] < fdr_threshold) & (result_df['log2FC'] >= logfc_threshold)
    sig_down = (result_df['fdr'] < fdr_threshold) & (result_df['log2FC'] <= -logfc_threshold)
    result_df.loc[sig_up, 'direction'] = 'up'
    result_df.loc[sig_down, 'direction'] = 'down'

    result_df = result_df.sort_values('pvalue')

    top_genes = result_df[result_df['direction'] != 'ns'].head(50)
    all_genes_list = result_df.to_dict('records')

    return {
        'n_total': len(result_df),
        'n_up': int(sig_up.sum()),
        'n_down': int(sig_down.sum()),
        'n_sig': int(sig_up.sum() + sig_down.sum()),
        'logfc_threshold': logfc_threshold,
        'pval_threshold': pval_threshold,
        'fdr_threshold': fdr_threshold,
        'method': method,
        'group1': group1_samples,
        'group2': group2_samples,
        'group1_name': 'Group1',
        'group2_name': 'Group2',
        'top_genes': top_genes[['gene','log2FC','pvalue','fdr','qvalue','direction']].rename(
            columns={'log2FC':'logfc','pvalue':'pval'}).to_dict('records'),
        'all_genes': all_genes_list,
        'up_genes': result_df[result_df['direction']=='up']['gene'].tolist(),
        'down_genes': result_df[result_df['direction']=='down']['gene'].tolist(),
        'sig_genes': result_df[result_df['direction']!='ns']['gene'].tolist(),
        'pi0': float(pi0),
    }


# ========== DESeq2-like Methods ==========

def _deseq2_normalize(data: pd.DataFrame, all_samples: List[str]) -> pd.DataFrame:
    """Median-of-ratios normalization (DESeq2 style)."""
    numeric = data[all_samples].astype(float)
    numeric = numeric.clip(lower=0)

    # Geometric mean per gene (excluding zeros)
    log_geomean = np.log(numeric.replace(0, np.nan)).mean(axis=1)
    log_geomean = log_geomean.replace(-np.inf, np.nan)

    # Size factors: median of ratios
    ratios = numeric.div(np.exp(log_geomean), axis=0)
    size_factors = ratios.median(axis=0)
    size_factors = size_factors / np.exp(np.mean(np.log(size_factors.replace(0, 1))))
    size_factors = size_factors.replace(0, 1).replace(np.inf, 1).fillna(1)

    result = data.copy()
    result[all_samples] = numeric.div(size_factors, axis=1)
    return result


def _log2_cpm(data: pd.DataFrame, all_samples: List[str]) -> pd.DataFrame:
    """Simple log2(CPM + 1) normalization."""
    numeric = data[all_samples].astype(float).clip(lower=0)
    lib_sizes = numeric.sum(axis=0).replace(0, 1)
    cpm = numeric.div(lib_sizes, axis=1) * 1e6
    result = data.copy()
    result[all_samples] = np.log2(cpm + 1)
    return result


def _deseq2_test(norm_data: pd.DataFrame, g1: List[str], g2: List[str]) -> List[Dict]:
    """DESeq2-like Wald test with dispersion estimation."""
    results = []
    all_samples = g1 + g2
    n1, n2 = len(g1), len(g2)

    # Estimate per-gene dispersion
    norm_vals = norm_data[all_samples].values
    means = norm_vals.mean(axis=1)
    vars_ = norm_vals.var(axis=1, ddof=1)

    # Parametric dispersion: var = mu + alpha * mu^2
    # Fit alpha (dispersion) using method of moments
    valid = (means > 0) & (vars_ > means)
    alpha_raw = np.zeros_like(means)
    alpha_raw[valid] = (vars_[valid] - means[valid]) / (means[valid] ** 2)
    alpha_raw = np.maximum(alpha_raw, 1e-8)

    # Shrink dispersion toward trend (simplified empirical Bayes)
    log_means = np.log(means + 1)
    trend = np.polyfit(log_means[valid], np.log(alpha_raw[valid] + 1e-8), 1)
    trend_alpha = np.exp(np.polyval(trend, log_means))
    # Blend: use trend for low-expressed genes
    alpha_shrunk = 0.5 * alpha_raw + 0.5 * trend_alpha
    alpha_shrunk = np.maximum(alpha_shrunk, 1e-8)

    for i, gene in enumerate(norm_data.index):
        vals1 = norm_data.loc[gene, g1].astype(float).values
        vals2 = norm_data.loc[gene, g2].astype(float).values

        mean1, mean2 = vals1.mean(), vals2.mean()
        if mean1 < 0.1 and mean2 < 0.1:
            continue

        logfc = np.log2((mean1 + 0.5) / (mean2 + 0.5))

        # Wald statistic
        disp = alpha_shrunk[i]
        mu1, mu2 = mean1 + 0.5, mean2 + 0.5
        se = np.sqrt(disp * (mu1 / n1 + mu2 / n2) + 1e-8)
        w = logfc / se if se > 0 else 0
        pval = 2 * scipy_stats.norm.sf(abs(w))
        pval = min(max(pval, 1e-300), 1.0)

        results.append({
            'gene': gene,
            'mean_group1': mean1,
            'mean_group2': mean2,
            'log2FC': logfc,
            'statistic': w,
            'pvalue': float(pval),
        })

    return results


# ========== Classical Methods ==========

def _ttest_genes(norm_data: pd.DataFrame, g1: List[str], g2: List[str]) -> List[Dict]:
    """Welch t-test per gene."""
    results = []
    for gene, row in norm_data.iterrows():
        v1 = row[g1].astype(float).dropna()
        v2 = row[g2].astype(float).dropna()
        if len(v1) < 2 or len(v2) < 2:
            continue
        stat, pval = scipy_stats.ttest_ind(v1, v2, equal_var=False)
        logfc = v1.mean() - v2.mean()
        results.append({
            'gene': gene, 'mean_group1': v1.mean(), 'mean_group2': v2.mean(),
            'log2FC': logfc, 'statistic': stat, 'pvalue': float(pval),
        })
    return results


def _wilcoxon_genes(norm_data: pd.DataFrame, g1: List[str], g2: List[str]) -> List[Dict]:
    """Mann-Whitney U test per gene."""
    results = []
    for gene, row in norm_data.iterrows():
        v1 = row[g1].astype(float).dropna()
        v2 = row[g2].astype(float).dropna()
        if len(v1) < 2 or len(v2) < 2:
            continue
        stat, pval = scipy_stats.mannwhitneyu(v1, v2, alternative='two-sided')
        logfc = v1.mean() - v2.mean()
        results.append({
            'gene': gene, 'mean_group1': v1.mean(), 'mean_group2': v2.mean(),
            'log2FC': logfc, 'statistic': stat, 'pvalue': float(pval),
        })
    return results


def _limma_genes(norm_data: pd.DataFrame, g1: List[str], g2: List[str]) -> List[Dict]:
    """Limma-like moderated t-test."""
    results = []
    n1, n2 = len(g1), len(g2)
    prior_df, prior_var = 3, 0.01
    for gene, row in norm_data.iterrows():
        v1 = row[g1].astype(float).dropna()
        v2 = row[g2].astype(float).dropna()
        if len(v1) < 2 or len(v2) < 2:
            continue
        v_pool = ((n1-1)*v1.var(ddof=1) + (n2-1)*v2.var(ddof=1) + prior_df*prior_var) / (n1+n2-2+prior_df)
        se = np.sqrt(v_pool * (1/n1 + 1/n2))
        if se < 1e-10: se = 1e-10
        t_stat = (v1.mean() - v2.mean()) / se
        df = n1 + n2 - 2 + prior_df
        pval = 2 * scipy_stats.t.sf(abs(t_stat), df)
        results.append({
            'gene': gene, 'mean_group1': v1.mean(), 'mean_group2': v2.mean(),
            'log2FC': v1.mean() - v2.mean(), 'statistic': t_stat, 'pvalue': float(pval),
        })
    return results
