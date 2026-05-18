"""GSEA via R/Bioconductor fgsea."""

import tempfile, shutil, pandas as pd
from pathlib import Path
from typing import Dict, List
from .r_engine import run_r


def run_gsea(ranked_genes: List[str], scores: List[float],
             gene_set_type: str = 'GO', pval_cutoff: float = 0.05,
             n_perm: int = 10000, seed: int = 42) -> Dict:
    if len(ranked_genes) != len(scores):
        raise ValueError("ranked_genes and scores must be same length")

    tmpdir = Path(tempfile.mkdtemp(prefix='bgsea_'))
    try:
        # Write ranked list
        rf = tmpdir / 'ranked.txt'
        pd.DataFrame({'gene': ranked_genes, 'score': scores}).to_csv(rf, sep='\t', index=False, header=False)
        rf_s = str(rf).replace('\\', '/')
        out_s = str(tmpdir / 'results.csv').replace('\\', '/')

        gs_r = {'GO': 'GO', 'KEGG': 'KEGG', 'MSIGDB': 'H', 'all': 'H'}.get(gene_set_type.upper(), 'H')

        rcode = f'''
        suppressMessages({{ library(fgsea); library(clusterProfiler); library(org.Hs.eg.db) }})
        ranked <- read.table("{rf_s}", header=FALSE, stringsAsFactors=FALSE)
        stats <- setNames(ranked$V2, ranked$V1)
        stats <- sort(stats, decreasing=TRUE)
        stats <- stats[!duplicated(names(stats))]

        if ("{gs_r}" == "GO") {{
          gs <- gson_GO(OrgDb=org.Hs.eg.db)
        }} else if ("{gs_r}" == "KEGG") {{
          gs <- gson_KEGG(organism="hsa")
        }} else {{
          gs <- gson_MSIGDB(species="Homo sapiens", category="{gs_r}")
        }}

        res <- fgsea(pathways=gs, stats=stats, minSize=5, maxSize=500,
                     nperm={n_perm}, nproc=1, seed={seed})
        res <- as.data.frame(res)
        res$leadingEdge <- sapply(res$leadingEdge, paste, collapse=";")
        write.table(res, "{out_s}", sep=\"\\t\", row.names=FALSE, quote=TRUE)
        cat("DONE\\n")
        '''
        run_r(rcode, timeout=180)

        out = tmpdir / 'results.csv'
        if not out.exists():
            return {'type': 'gsea', 'terms': [], 'n_terms': 0}

        df = pd.read_csv(out, sep='\t')
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if len(df) == 0:
        return {'type': 'gsea', 'terms': [], 'n_terms': 0}

    terms = []
    for _, r in df.iterrows():
        terms.append({
            'term': str(r.get('pathway', '')),
            'id': str(r.get('pathway', '')),
            'es': float(r.get('ES', 0)), 'nes': float(r.get('NES', 0)),
            'pvalue': float(r.get('pval', 1)), 'fdr': float(r.get('padj', 1)),
            'qvalue': float(r.get('padj', 1)),
            'leading_edge': str(r.get('leadingEdge', '')).split(';')[:20],
            'n_hits': int(r.get('size', 0)),
        })

    sig = [t for t in terms if t['fdr'] < pval_cutoff]
    return {'type': 'gsea', 'gene_set_type': gene_set_type,
            'terms': sig[:100] if sig else terms[:20],
            'n_terms': len(sig) if sig else len(terms),
            'n_total_terms': len(terms), 'n_permutations': n_perm}
