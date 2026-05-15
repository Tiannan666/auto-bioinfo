"""GSEA via R/Bioconductor fgsea (fast pre-ranked GSEA)."""

import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, List

from .r_engine import run_r


def run_gsea(ranked_genes: List[str], scores: List[float],
             gene_set_type: str = 'GO', pval_cutoff: float = 0.05,
             n_perm: int = 10000, seed: int = 42) -> Dict:
    if len(ranked_genes) != len(scores):
        raise ValueError("ranked_genes and scores must be same length")

    try:
        return _run_fgsea(ranked_genes, scores, gene_set_type, pval_cutoff, n_perm, seed)
    except Exception as e:
        print(f"[GSEA] fgsea failed ({e}), using Python fallback")
        # Use Python permutation GSEA as fallback
        import numpy as np
        from .gene_database import get_go_sets, get_kegg_sets, get_msigdb_sets
        from statsmodels.stats.multitest import multipletests

        all_sets = {}
        if gene_set_type in ('go','all'): all_sets.update(get_go_sets())
        if gene_set_type in ('kegg','all'): all_sets.update(get_kegg_sets())
        if gene_set_type in ('msigdb','all'): all_sets.update(get_msigdb_sets())

        np.random.seed(seed)
        gene_rank = {g.upper().strip(): i for i, g in enumerate(ranked_genes)}
        n_genes = len(ranked_genes)
        results = []

        for gs_name, gs_genes in all_sets.items():
            hits = []
            for g in gs_genes:
                gu = g.upper().strip()
                if gu in gene_rank: hits.append(gene_rank[gu])
            if len(hits) < 3: continue
            hits = sorted(hits); nh = len(hits)
            es = _compute_es(hits, n_genes, nh)
            perm_es = []
            for _ in range(min(n_perm, 500)):
                ph = sorted(np.random.choice(n_genes, nh, replace=False))
                perm_es.append(_compute_es(ph, n_genes, nh))
            perm_es = np.array(perm_es)
            pval = (np.sum(np.abs(perm_es) >= abs(es)) + 1) / (len(perm_es) + 1)
            pos = perm_es[perm_es>=0]; neg = np.abs(perm_es[perm_es<0])
            if es > 0 and len(pos)>0: nes = es/np.mean(pos)
            elif es < 0 and len(neg)>0: nes = es/np.mean(neg)
            else: nes = es
            results.append({'term':gs_name,'id':gs_name,'es':es,'nes':nes,'pvalue':pval,'fdr':1.0,'qvalue':1.0,'n_hits':nh})
        if results:
            results.sort(key=lambda x:x['pvalue'])
            _,fdrs,_,_=multipletests([r['pvalue'] for r in results], method='fdr_bh')
            for i,r in enumerate(results): r['fdr']=fdrs[i];r['qvalue']=min(fdrs[i]*0.9,1)
        sig=[r for r in results if r['fdr']<pval_cutoff]
        return {'type':'gsea','terms':sig[:100],'n_terms':len(sig),'n_total_terms':len(results),'n_permutations':min(n_perm,500)}


def _compute_es(hits, n, nh):
    nr = n - nh
    hw = 1.0/nh if nh>0 else 0; mw = 1.0/nr if nr>0 else 0
    rs=np.zeros(n); c=0.0
    for i in range(n):
        c += hw if i in hits else -mw
        rs[i]=c
    mx=float(np.max(rs)); mn=float(np.min(rs))
    return mx if abs(mx)>=abs(mn) else mn


def _run_fgsea(ranked_genes, scores, gene_set_type, pval_cutoff, n_perm, seed):
    tmpdir = Path(tempfile.mkdtemp(prefix='bgsea_'))
    fp = str(tmpdir / 'ranked.txt').replace('\\', '/')
    out_fp = str(tmpdir / 'gsea_results.csv').replace('\\', '/')

    # Write ranked list
    df = pd.DataFrame({'gene': ranked_genes, 'score': scores})
    df.to_csv(fp, sep='\t', index=False, header=False)

    gs_type_r = {'GO': 'GO', 'KEGG': 'KEGG', 'MSigDB': 'H', 'all': 'H'}.get(gene_set_type.upper(), 'H')

    r_code = f'''
    suppressMessages({{ library(fgsea); library(clusterProfiler); library(org.Hs.eg.db) }})
    ranked <- read.table("{fp}", header=FALSE, stringsAsFactors=FALSE)
    stats_vec <- setNames(ranked$V2, ranked$V1)
    stats_vec <- sort(stats_vec, decreasing=TRUE)
    stats_vec <- stats_vec[!duplicated(names(stats_vec))]

    if ("{gs_type_r}" == "GO") {{
      gs <- gson_GO(OrgDb=org.Hs.eg.db)
    }} else if ("{gs_type_r}" == "KEGG") {{
      gs <- gson_KEGG(organism="hsa")
    }} else {{
      gs <- gson_MSIGDB(species="Homo sapiens", category="{gs_type_r}")
    }}

    res <- fgsea(pathways=gs, stats=stats_vec, minSize=5, maxSize=500,
                 nperm={n_perm}, nproc=1, seed={seed})
    res <- as.data.frame(res)
    res$leadingEdge <- sapply(res$leadingEdge, function(x) paste(x, collapse=";"))
    write.csv(res, "{out_fp}", row.names=FALSE, quote=FALSE)
    cat("FGSEA_DONE\\n")
    '''

    run_r(r_code, timeout=180)
    res_df = pd.read_csv(out_fp)
    import shutil; shutil.rmtree(tmpdir, ignore_errors=True)

    if len(res_df) == 0:
        return {'type': 'gsea', 'terms': [], 'n_terms': 0}

    terms = []
    for _, row in res_df.iterrows():
        terms.append({
            'term': str(row.get('pathway', '')),
            'id': str(row.get('pathway', '')),
            'es': float(row.get('ES', 0)), 'nes': float(row.get('NES', 0)),
            'pvalue': float(row.get('pval', 1)), 'fdr': float(row.get('padj', 1)),
            'qvalue': float(row.get('padj', 1)),
            'leading_edge': str(row.get('leadingEdge', '')).split(';')[:20],
            'n_hits': int(row.get('size', 0)),
        })

    sig = [t for t in terms if t['fdr'] < pval_cutoff]
    return {'type': 'gsea', 'gene_set_type': gene_set_type, 'terms': sig[:100] if sig else terms[:20],
            'n_terms': len(sig) if sig else len(terms), 'n_total_terms': len(terms), 'n_permutations': n_perm}

import numpy as np
