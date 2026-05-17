"""GO/KEGG enrichment via R/Bioconductor clusterProfiler."""

import tempfile, shutil, pandas as pd
from pathlib import Path
from typing import Dict, List
from .r_engine import run_r

SPECIES_CONFIG = {
    'human':   {'orgdb': 'org.Hs.eg.db', 'kegg': 'hsa'},
    'hsa':     {'orgdb': 'org.Hs.eg.db', 'kegg': 'hsa'},
    'mouse':   {'orgdb': 'org.Mm.eg.db', 'kegg': 'mmu'},
    'mmu':     {'orgdb': 'org.Mm.eg.db', 'kegg': 'mmu'},
    'rat':     {'orgdb': 'org.Rn.eg.db', 'kegg': 'rno'},
    'rno':     {'orgdb': 'org.Rn.eg.db', 'kegg': 'rno'},
}

def run_enrichment(gene_list: List[str], pval_cutoff: float = 0.05,
                   go_bp: bool = True, go_cc: bool = True, go_mf: bool = True,
                   kegg: bool = True, species: str = 'human', **kw) -> Dict:
    if not gene_list:
        return {'type': 'go_kegg', 'terms': [], 'n_terms': 0, 'gene_count': 0}

    cfg = SPECIES_CONFIG.get(species.lower(), SPECIES_CONFIG['human'])

    tmpdir = Path(tempfile.mkdtemp(prefix='benrich_'))
    try:
        gf = tmpdir / 'genes.txt'
        gf.write_text('\n'.join(gene_list), encoding='utf-8')
        gf_s = str(gf).replace('\\', '/')
        rf = str(tmpdir / 'results.tsv').replace('\\', '/')

        onts = []
        if go_bp: onts.append('"BP"')
        if go_cc: onts.append('"CC"')
        if go_mf: onts.append('"MF"')
        ont_vec = 'c(' + ','.join(onts) + ')' if onts else 'c("BP")'
        do_kegg = 'TRUE' if kegg else 'FALSE'

        rcode = '''suppressMessages({{ library(clusterProfiler); library({orgdb}, character.only=TRUE) }})
genes <- readLines("{gf}")
entrez <- bitr(genes, fromType="SYMBOL", toType="ENTREZID", OrgDb={orgdb})
if (nrow(entrez) == 0) stop("No genes mapped to Entrez")
eid <- unique(entrez$ENTREZID)
all.res <- data.frame()
for (ont in {onts}) {{
  ego <- enrichGO(gene=eid, OrgDb={orgdb}, ont=ont, pAdjustMethod="BH",
                  pvalueCutoff={pval}, qvalueCutoff=0.3)
  if (nrow(ego) > 0) {{ df <- as.data.frame(ego); df$Category <- paste0("GO_", ont); all.res <- rbind(all.res, df) }}
}}
if ({kegg_flag}) {{
  tryCatch({{
    ekegg <- enrichKEGG(gene=eid, organism="{kegg_org}", pAdjustMethod="BH", pvalueCutoff={pval})
    if (nrow(ekegg) > 0) {{ df2 <- as.data.frame(ekegg); df2$Category <- "KEGG"; all.res <- rbind(all.res, df2) }}
  }}, error=function(e){{}})
}}
write.table(all.res, "{out}", sep="\\t", row.names=FALSE, quote=TRUE)
cat("DONE\\n")'''.format(
    orgdb=cfg['orgdb'], gf=gf_s, out=rf, onts=ont_vec,
    kegg_flag=do_kegg, kegg_org=cfg['kegg'], pval=pval_cutoff)

        run_r(rcode, timeout=180)

        rf_path = tmpdir / 'results.tsv'
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
