"""Differential expression — R DESeq2/edgeR/limma-voom."""

import tempfile, shutil, numpy as np, pandas as pd
from pathlib import Path
from typing import Dict, List

from .r_engine import run_r


def run_differential(matrix: pd.DataFrame, group1_samples: List[str], group2_samples: List[str],
                     method: str = 'deseq2', logfc_threshold: float = 1.0,
                     pval_threshold: float = 0.05, fdr_threshold: float = 0.05, **kw) -> Dict:
    g1 = [c for c in group1_samples if c in matrix.select_dtypes(include=[np.number]).columns]
    g2 = [c for c in group2_samples if c in matrix.select_dtypes(include=[np.number]).columns]
    if len(g1) < 2 or len(g2) < 2:
        raise ValueError(f"Need >=2 samples per group. G1:{len(g1)} G2:{len(g2)}")

    tmpdir = Path(tempfile.mkdtemp(prefix='bdiff_'))
    try:
        cnt = matrix[g1+g2].round().clip(lower=0).astype(int)
        cnt = cnt.loc[cnt.sum(axis=1) > 0]
        cnt.to_csv(tmpdir / 'counts.csv')
        cf = str(tmpdir / 'counts.csv').replace('\\', '/')
        rf = str(tmpdir / 'results.csv').replace('\\', '/')
        g1s = ','.join(f'"{s}"' for s in g1)
        g2s = ','.join(f'"{s}"' for s in g2)

        if method == 'deseq2':
            rcode = f'''
            suppressMessages(library(DESeq2))
            cnt <- as.matrix(read.csv("{cf}", row.names=1, check.names=FALSE))
            g1 <- c({g1s}); g2 <- c({g2s})
            cnt <- cnt[, c(g1,g2), drop=FALSE]
            grp <- factor(c(rep("G1",length(g1)), rep("G2",length(g2))))
            cd <- data.frame(condition=grp, row.names=colnames(cnt))
            dds <- DESeqDataSetFromMatrix(countData=cnt, colData=cd, design=~condition)
            dds <- DESeq(dds)
            res <- as.data.frame(results(dds, contrast=c("condition","G1","G2")))
            res$gene <- rownames(res)
            write.csv(res[,c("gene","log2FoldChange","pvalue","padj")], "{rf}", row.names=FALSE, quote=FALSE)
            '''
        elif method == 'edger':
            rcode = f'''
            suppressMessages(library(edgeR))
            cnt <- as.matrix(read.csv("{cf}", row.names=1, check.names=FALSE))
            g1 <- c({g1s}); g2 <- c({g2s})
            cnt <- cnt[, c(g1,g2), drop=FALSE]
            grp <- factor(c(rep("G1",length(g1)), rep("G2",length(g2))))
            dge <- DGEList(counts=cnt, group=grp)
            dge <- calcNormFactors(dge); dge <- estimateDisp(dge)
            et <- exactTest(dge)
            res <- as.data.frame(topTags(et, n=nrow(cnt))$table)
            res$gene <- rownames(res)
            colnames(res)[c(1,3,4)] <- c("log2FoldChange","pvalue","padj")
            write.csv(res[,c("gene","log2FoldChange","pvalue","padj")], "{rf}", row.names=FALSE, quote=FALSE)
            '''
        else:  # limma-voom
            rcode = f'''
            suppressMessages(library(edgeR)); suppressMessages(library(limma))
            cnt <- as.matrix(read.csv("{cf}", row.names=1, check.names=FALSE))
            g1 <- c({g1s}); g2 <- c({g2s})
            cnt <- cnt[, c(g1,g2), drop=FALSE]
            grp <- factor(c(rep("G1",length(g1)), rep("G2",length(g2))))
            dge <- DGEList(counts=cnt, group=grp); dge <- calcNormFactors(dge)
            design <- model.matrix(~0+grp); colnames(design) <- c("G1","G2")
            v <- voom(dge, design); fit <- lmFit(v, design)
            contrast <- makeContrasts(G1-G2, levels=design)
            fit2 <- contrasts.fit(fit, contrast); fit2 <- eBayes(fit2)
            res <- as.data.frame(topTable(fit2, number=nrow(cnt)))
            res$gene <- rownames(res)
            colnames(res)[c(1,4,5)] <- c("log2FoldChange","pvalue","padj")
            write.csv(res[,c("gene","log2FoldChange","pvalue","padj")], "{rf}", row.names=FALSE, quote=FALSE)
            '''

        run_r(rcode, timeout=120)
        df = pd.read_csv(tmpdir / 'results.csv')
        df.columns = ['gene', 'log2FC', 'pvalue', 'fdr']
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    df['log2FC'] = pd.to_numeric(df['log2FC'], errors='coerce').fillna(0)
    df['fdr'] = pd.to_numeric(df['fdr'], errors='coerce').fillna(1)
    df['pvalue'] = pd.to_numeric(df['pvalue'], errors='coerce').fillna(1)
    df['direction'] = 'ns'
    df.loc[(df['fdr']<fdr_threshold)&(df['log2FC']>=logfc_threshold), 'direction'] = 'up'
    df.loc[(df['fdr']<fdr_threshold)&(df['log2FC']<=-logfc_threshold), 'direction'] = 'down'
    df = df.sort_values('pvalue')
    top = df[df['direction'] != 'ns'].head(50)

    return {
        'n_total': len(df), 'n_up': int((df['direction']=='up').sum()),
        'n_down': int((df['direction']=='down').sum()),
        'n_sig': int((df['direction']!='ns').sum()),
        'logfc_threshold': logfc_threshold, 'fdr_threshold': fdr_threshold,
        'method': method, 'group1': g1, 'group2': g2,
        'top_genes': top.rename(columns={'log2FC':'logfc','pvalue':'pval'})[['gene','logfc','pval','fdr','direction']].to_dict('records'),
        'all_genes': df.to_dict('records'),
        'up_genes': df[df['direction']=='up']['gene'].tolist(),
        'down_genes': df[df['direction']=='down']['gene'].tolist(),
        'sig_genes': df[df['direction']!='ns']['gene'].tolist(),
    }
