"""Differential expression — DESeq2-like + classical methods. Pure Python."""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.stats.multitest import multipletests
from typing import Dict, List


def run_differential(matrix: pd.DataFrame, group1_samples: List[str], group2_samples: List[str],
                     method: str = 'deseq2', logfc_threshold: float = 1.0,
                     pval_threshold: float = 0.05, fdr_threshold: float = 0.05,
                     log2_transform: bool = False, filter_low: bool = True,
                     min_count: int = 10, min_samples: int = 3) -> Dict:

    g1 = [c for c in group1_samples if c in matrix.select_dtypes(include=[np.number]).columns]
    g2 = [c for c in group2_samples if c in matrix.select_dtypes(include=[np.number]).columns]
    if len(g1) < 2 or len(g2) < 2:
        raise ValueError(f"Need >=2 samples per group. G1:{len(g1)} G2:{len(g2)}")

    data = matrix.copy()
    if filter_low:
        numeric = data.select_dtypes(include=[np.number])
        keep = (numeric >= min_count).sum(axis=1) >= min(min_samples, len(g1 + g2) // 2)
        data = data.loc[keep]

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

    result_df['log2FC'] = pd.to_numeric(result_df['log2FC'], errors='coerce').fillna(0)
    result_df['fdr'] = pd.to_numeric(result_df['fdr'], errors='coerce').fillna(1)
    result_df['pvalue'] = pd.to_numeric(result_df['pvalue'], errors='coerce').fillna(1)

    result_df['direction'] = 'ns'
    result_df.loc[(result_df['fdr']<fdr_threshold)&(result_df['log2FC']>=logfc_threshold),'direction']='up'
    result_df.loc[(result_df['fdr']<fdr_threshold)&(result_df['log2FC']<=-logfc_threshold),'direction']='down'
    result_df = result_df.sort_values('pvalue')

    return {
        'n_total': len(result_df), 'n_up': int((result_df['direction']=='up').sum()),
        'n_down': int((result_df['direction']=='down').sum()),
        'n_sig': int((result_df['direction']!='ns').sum()),
        'logfc_threshold': logfc_threshold, 'fdr_threshold': fdr_threshold,
        'method': method, 'group1': g1, 'group2': g2,
        'top_genes': result_df[result_df['direction']!='ns'].head(50)
            .rename(columns={'log2FC':'logfc','pvalue':'pval'})[['gene','logfc','pval','fdr','direction']]
            .to_dict('records'),
        'all_genes': result_df.to_dict('records'),
        'up_genes': result_df[result_df['direction']=='up']['gene'].tolist(),
        'down_genes': result_df[result_df['direction']=='down']['gene'].tolist(),
        'sig_genes': result_df[result_df['direction']!='ns']['gene'].tolist(),
    }


def _run_r_diff(matrix, g1, g2, method):
    tmpdir = Path(tempfile.mkdtemp(prefix='bdiff_'))
    count_file = tmpdir / 'counts.csv'
    matrix[g1+g2].round().astype(int).to_csv(count_file)

    r_code = f'''
    suppressMessages({{ library(DESeq2); library(edgeR); library(limma) }})
    counts <- as.matrix(read.csv("{str(count_file).replace(chr(92),'/')}", row.names=1, check.names=FALSE))
    counts <- counts[rowSums(counts) > 0, , drop=FALSE]
    g1 <- c({','.join(repr(s) for s in g1)})
    g2 <- c({','.join(repr(s) for s in g2)})
    counts <- counts[, c(g1, g2), drop=FALSE]
    group <- factor(c(rep("G1", length(g1)), rep("G2", length(g2))))
    if ("{method}" == "edger") {{
      dge <- DGEList(counts=counts, group=group)
      dge <- calcNormFactors(dge)
      dge <- estimateDisp(dge)
      et <- exactTest(dge)
      res <- as.data.frame(topTags(et, n=nrow(counts))$table)
      res$gene <- rownames(res)
      colnames(res) <- c("log2FC","logCPM","pvalue","fdr","gene")
      res <- res[, c("gene","log2FC","pvalue","fdr")]
    }} else if ("{method}" == "limma") {{
      dge <- DGEList(counts=counts, group=group)
      dge <- calcNormFactors(dge)
      design <- model.matrix(~0+group)
      colnames(design) <- c("G1","G2")
      v <- voom(dge, design)
      fit <- lmFit(v, design)
      contrast <- makeContrasts(G1-G2, levels=design)
      fit2 <- contrasts.fit(fit, contrast)
      fit2 <- eBayes(fit2)
      res <- as.data.frame(topTable(fit2, number=nrow(counts)))
      res$gene <- rownames(res)
      colnames(res)[c(1,4,5)] <- c("log2FC","pvalue","fdr")
      res <- res[, c("gene","log2FC","pvalue","fdr")]
    }} else {{
      colData <- data.frame(condition=group, row.names=colnames(counts))
      dds <- DESeqDataSetFromMatrix(countData=counts, colData=colData, design=~condition)
      dds <- DESeq(dds)
      res <- as.data.frame(results(dds, contrast=c("condition","G1","G2")))
      res$gene <- rownames(res)
      colnames(res)[c(2,5,6)] <- c("log2FC","pvalue","fdr")
      res <- res[, c("gene","log2FC","pvalue","fdr")]
    }}
    write.csv(res, "{str(tmpdir / 'res.csv').replace(chr(92),'/')}", row.names=FALSE, quote=FALSE)
    cat("DONE\\n")
    '''.replace('chr(92)', '\\\\')

    run_r(r_code, timeout=120)
    result = pd.read_csv(tmpdir / 'res.csv')
    import shutil; shutil.rmtree(tmpdir, ignore_errors=True)
    return result


def _python_fallback(matrix, g1, g2, logfc_threshold, fdr_threshold):
    from scipy import stats
    results = []
    data = np.log2(matrix.select_dtypes(include=[np.number]).clip(lower=0) + 1)
    for gene in data.index:
        v1 = data.loc[gene, g1].astype(float).dropna()
        v2 = data.loc[gene, g2].astype(float).dropna()
        if len(v1) < 2 or len(v2) < 2: continue
        t, p = stats.ttest_ind(v1, v2, equal_var=False)
        results.append({'gene': gene, 'log2FC': v1.mean()-v2.mean(), 'pvalue': p, 'fdr': 1.0})
    df = pd.DataFrame(results)
    _, fdrs, _, _ = multipletests(df['pvalue'].values, method='fdr_bh')
    df['fdr'] = fdrs
    df['direction'] = 'ns'
    df.loc[(df['fdr']<fdr_threshold)&(df['log2FC']>=logfc_threshold),'direction']='up'
    df.loc[(df['fdr']<fdr_threshold)&(df['log2FC']<=-logfc_threshold),'direction']='down'
    return {
        'n_total': len(df), 'n_up': int((df['direction']=='up').sum()),
        'n_down': int((df['direction']=='down').sum()), 'n_sig': int((df['direction']!='ns').sum()),
        'logfc_threshold': logfc_threshold, 'fdr_threshold': fdr_threshold,
        'method': 'ttest (fallback)', 'group1': g1, 'group2': g2,
        'top_genes': df[df['direction']!='ns'].head(50).rename(
            columns={'log2FC':'logfc','pvalue':'pval'}).to_dict('records'),
        'all_genes': df.to_dict('records'),
        'up_genes': df[df['direction']=='up']['gene'].tolist(),
        'down_genes': df[df['direction']=='down']['gene'].tolist(),
        'sig_genes': df[df['direction']!='ns']['gene'].tolist(),
    }
