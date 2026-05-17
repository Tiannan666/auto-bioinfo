"""GO/KEGG enrichment via R/Bioconductor clusterProfiler."""

import tempfile, shutil, pandas as pd
from pathlib import Path
from typing import Dict, List
from .r_engine import run_r


def run_enrichment(gene_list: List[str], pval_cutoff: float = 0.05,
                   go_bp: bool = True, go_cc: bool = True, go_mf: bool = True,
                   kegg: bool = True, **kw) -> Dict:
    if not gene_list:
        return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': 0}

    tmpdir = Path(tempfile.mkdtemp(prefix='benrich_'))
    try:
        gf = tmpdir / 'genes.txt'
        gf.write_text('\n'.join(gene_list), encoding='utf-8')
        gf_s = str(gf).replace('\\', '/')
        rf = str(tmpdir / 'results.csv').replace('\\', '/')

        onts = []
        if go_bp: onts.append('"BP"')
        if go_cc: onts.append('"CC"')
        if go_mf: onts.append('"MF"')
        ont_vec = 'c(' + ','.join(onts) + ')' if onts else 'c("BP")'

        rcode = f'''
        suppressMessages({{ library(clusterProfiler); library(org.Hs.eg.db) }})
        genes <- readLines("{gf_s}")
        entrez <- bitr(genes, fromType="SYMBOL", toType="ENTREZID", OrgDb=org.Hs.eg.db)
        if (nrow(entrez) == 0) stop("No genes mapped")
        eid <- unique(entrez$ENTREZID)
        all <- data.frame()
        for (ont in {ont_vec}) {{
          ego <- enrichGO(gene=eid, OrgDb=org.Hs.eg.db, ont=ont, pAdjustMethod="BH",
                          pvalueCutoff={pval_cutoff}, qvalueCutoff=0.3)
          if (nrow(ego) > 0) {{ df <- as.data.frame(ego); df$Category <- paste0("GO_", ont); all <- rbind(all, df) }}
        }}
        do_kegg <- {'TRUE' if kegg else 'FALSE'}
        if (do_kegg) {{
          tryCatch({{
            ekegg <- enrichKEGG(gene=eid, organism="hsa", pAdjustMethod="BH", pvalueCutoff={pval_cutoff})
            if (nrow(ekegg) > 0) {{ df2 <- as.data.frame(ekegg); df2$Category <- "KEGG"; all <- rbind(all, df2) }}
          }}, error=function(e){{}})
        }}
        write.table(all, "{rf}", sep=\"\\t\", row.names=FALSE, quote=TRUE)
        cat("DONE\\n")
        '''
        run_r(rcode, timeout=180)

        rf_path = tmpdir / 'results.csv'
        if not rf_path.exists():
            return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': len(gene_list)}

        df = pd.read_csv(rf_path, sep='\t')
        terms = []
        for _, r in df.iterrows():
            terms.append({
                'term': str(r.get('Description', '')),
                'id': str(r.get('ID', '')),
                'category': str(r.get('Category', 'GO')),
                'gene_count': int(r.get('Count', 0)),
                'pvalue': float(r.get('pvalue', 1)),
                'fdr': float(r.get('p.adjust', 1)),
                'qvalue': float(r.get('qvalue', 1)) if 'qvalue' in r else float(r.get('p.adjust', 1)),
                'genes': str(r.get('geneID', '')).split('/')[:10] if pd.notna(r.get('geneID', '')) else [],
                'gene_ratio': str(r.get('GeneRatio', '')),
            })
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    terms.sort(key=lambda x: x['pvalue'])
    return {'type': 'go_kegg', 'terms': terms[:200], 'n_terms': len(terms), 'gene_count': len(gene_list)}
