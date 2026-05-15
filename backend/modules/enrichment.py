"""GO/KEGG enrichment via R/Bioconductor clusterProfiler + org.Hs.eg.db."""

import tempfile
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List

from .r_engine import run_r


def run_enrichment(gene_list: List[str], pval_cutoff: float = 0.05,
                   go_bp: bool = True, go_cc: bool = True, go_mf: bool = True,
                   kegg: bool = True, msigdb: bool = False) -> Dict:
    if not gene_list:
        return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': 0}

    try:
        return _run_clusterprofiler(gene_list, pval_cutoff, go_bp, go_cc, go_mf, kegg)
    except Exception as e:
        print(f"[Enrich] clusterProfiler failed ({e}), using Python fallback")
        from .gene_database import get_all_gene_sets, get_background_size
        from scipy import stats as scipy_stats
        from statsmodels.stats.multitest import multipletests
        all_sets = get_all_gene_sets()
        gene_set = set(g.upper().strip() for g in gene_list)
        bg = get_background_size()
        results = []
        for tid, tgenes in all_sets.items():
            ts = set(g.upper().strip() for g in tgenes)
            ov = gene_set & ts
            if len(ov) < 2: continue
            p = scipy_stats.hypergeom.sf(len(ov)-1, bg, len(ts), len(gene_set))
            results.append({'term': tid, 'id': tid, 'category': 'GO', 'gene_count': len(ov),
                          'pvalue': p, 'fdr': 1.0, 'qvalue': 1.0, 'genes': sorted(ov)[:10]})
        if results:
            results.sort(key=lambda x: x['pvalue'])
            _, fdrs, _, _ = multipletests([r['pvalue'] for r in results], method='fdr_bh')
            for i, r in enumerate(results): r['fdr'] = fdrs[i]
        sig = [r for r in results if r['fdr'] < pval_cutoff]
        return {'type': 'go_kegg', 'terms': sig[:200], 'n_terms': len(sig), 'gene_count': len(gene_list)}


def _run_clusterprofiler(gene_list, pval_cutoff, go_bp, go_cc, go_mf, kegg):
    tmpdir = Path(tempfile.mkdtemp(prefix='benrich_'))
    genes_file = tmpdir / 'genes.txt'
    Path(genes_file).write_text('\n'.join(gene_list), encoding='utf-8')

    ont_flags = []
    if go_bp: ont_flags.append('"BP"')
    if go_cc: ont_flags.append('"CC"')
    if go_mf: ont_flags.append('"MF"')
    ont_vec = 'c(' + ','.join(ont_flags) + ')' if ont_flags else 'c("BP")'

    out_file = str(tmpdir / 'enrich_results.csv').replace('\\', '/')
    genes_fp = str(genes_file).replace('\\', '/')

    r_code = f'''
    suppressMessages({{
      library(clusterProfiler)
      library(org.Hs.eg.db)
    }})
    genes <- readLines("{genes_fp}")
    entrez <- bitr(genes, fromType="SYMBOL", toType="ENTREZID", OrgDb=org.Hs.eg.db)
    if (nrow(entrez) == 0) stop("No genes mapped to Entrez")
    entrez_ids <- unique(entrez$ENTREZID)
    all_results <- data.frame()
    for (ont in {ont_vec}) {{
      ego <- enrichGO(gene=entrez_ids, OrgDb=org.Hs.eg.db, ont=ont,
                      pAdjustMethod="BH", pvalueCutoff={pval_cutoff}, qvalueCutoff=0.3)
      if (nrow(ego) > 0) {{
        df <- as.data.frame(ego)
        df$Category <- paste0("GO_", ont)
        all_results <- rbind(all_results, df)
      }}
    }}
    if ({str(kegg).lower()}) {{
      tryCatch({{
        ekegg <- enrichKEGG(gene=entrez_ids, organism="hsa",
                            pAdjustMethod="BH", pvalueCutoff={pval_cutoff})
        if (nrow(ekegg) > 0) {{
          df2 <- as.data.frame(ekegg)
          df2$Category <- "KEGG"
          all_results <- rbind(all_results, df2)
        }}
      }}, error=function(e) {{ cat("KEGG failed:", e$message, "\\n") }})
    }}
    if (nrow(all_results) > 0) {{
      write.csv(all_results, "{out_file}", row.names=FALSE, quote=FALSE)
      cat("ENRICH_DONE\\n")
    }} else {{
      cat("NO_RESULTS\\n")
    }}
    '''

    out = run_r(r_code, timeout=180)

    res_file = Path(tmpdir) / 'enrich_results.csv'
    if not res_file.exists():
        return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': len(gene_list)}

    df = pd.read_csv(res_file)
    terms = []
    for _, row in df.iterrows():
        terms.append({
            'term': str(row.get('Description', '')),
            'id': str(row.get('ID', '')),
            'category': str(row.get('Category', 'GO')),
            'gene_count': int(row.get('Count', 0)),
            'pvalue': float(row.get('pvalue', 1)),
            'fdr': float(row.get('p.adjust', 1)),
            'qvalue': float(row.get('qvalue', 1)) if 'qvalue' in row else float(row.get('p.adjust', 1)),
            'genes': str(row.get('geneID', '')).split('/')[:10] if pd.notna(row.get('geneID', '')) else [],
            'gene_ratio': str(row.get('GeneRatio', '')),
        })

    import shutil; shutil.rmtree(tmpdir, ignore_errors=True)
    terms.sort(key=lambda x: x['pvalue'])
    return {
        'type': 'go_kegg',
        'terms': terms[:200],
        'n_terms': len(terms),
        'gene_count': len(gene_list),
    }
