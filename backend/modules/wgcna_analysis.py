"""WGCNA co-expression network analysis via R."""

import tempfile, shutil, pandas as pd, numpy as np
from pathlib import Path
from typing import Dict, Optional
from .r_engine import run_r


def run_wgcna(expression: pd.DataFrame, n_top_genes: int = 5000,
              soft_power: Optional[int] = None, min_module_size: int = 30) -> Dict:
    """Run WGCNA analysis on expression matrix."""

    if expression.index.name != 'gene' and 'gene' in expression.columns:
        expression = expression.set_index('gene')

    expr_num = expression.select_dtypes(include=['number'])
    if expr_num.shape[1] < 6:
        raise ValueError("WGCNA requires at least 6 samples")

    # Select top variable genes
    gene_var = expr_num.var(axis=1)
    top_genes = gene_var.nlargest(min(n_top_genes, len(gene_var))).index
    expr_subset = expr_num.loc[top_genes]

    tmpdir = Path(tempfile.mkdtemp(prefix='bwgcna_'))
    try:
        data_file = tmpdir / 'expr.csv'
        expr_subset.to_csv(data_file)
        data_path = str(data_file).replace('\\', '/')
        modules_path = str(tmpdir / 'modules.csv').replace('\\', '/')
        hub_path = str(tmpdir / 'hub_genes.csv').replace('\\', '/')
        power_path = str(tmpdir / 'power.csv').replace('\\', '/')

        power_code = ''
        if soft_power is None:
            power_code = f'''
powers <- c(1:20)
sft <- pickSoftThreshold(datExpr, powerVector=powers, verbose=0)
power <- sft$powerEstimate
if(is.na(power)) power <- 6
write.csv(data.frame(power=power, sft$fitIndices), "{power_path}", row.names=FALSE)
'''
        else:
            power_code = f'power <- {soft_power}'

        rcode = f'''
suppressMessages({{library(WGCNA); options(stringsAsFactors=FALSE)}})
allowWGCNAThreads(nThreads=2)

expr <- read.csv("{data_path}", row.names=1)
datExpr <- t(expr)

{power_code}

net <- blockwiseModules(datExpr, power=power,
  TOMType="unsigned", minModuleSize={min_module_size},
  reassignThreshold=0, mergeCutHeight=0.25,
  numericLabels=TRUE, pamRespectsDendro=FALSE,
  verbose=0)

moduleColors <- labels2colors(net$colors)
gene_modules <- data.frame(gene=colnames(datExpr), module=moduleColors, stringsAsFactors=FALSE)
write.csv(gene_modules, "{modules_path}", row.names=FALSE)

# Hub genes per module
hub_list <- list()
for(mod in unique(moduleColors)) {{
  mod_genes <- colnames(datExpr)[moduleColors == mod]
  if(length(mod_genes) < 3) next
  kME <- cor(datExpr[, mod_genes], net$MEs[, paste0("ME", net$colors[moduleColors == mod][1])], use="p")
  top_hub <- head(mod_genes[order(-abs(kME))], 10)
  for(g in top_hub) hub_list[[length(hub_list)+1]] <- data.frame(gene=g, module=mod, kME=kME[g,1])
}}
hub_df <- do.call(rbind, hub_list)
write.csv(hub_df, "{hub_path}", row.names=FALSE)

cat("MODULES:", length(unique(moduleColors)), "\\n")
cat("POWER:", power, "\\n")
cat("DONE\\n")
'''
        output = run_r(rcode, timeout=300)

        modules_file = tmpdir / 'modules.csv'
        hub_file = tmpdir / 'hub_genes.csv'

        if not modules_file.exists():
            raise RuntimeError("WGCNA failed - no module output")

        modules_df = pd.read_csv(modules_file)
        hub_df = pd.read_csv(hub_file) if hub_file.exists() else pd.DataFrame()

        module_summary = modules_df.groupby('module').size().to_dict()

        # Parse power from output
        detected_power = soft_power or 6
        for line in output.split('\n'):
            if line.startswith('POWER:'):
                detected_power = int(line.split(':')[1].strip())

        hub_genes = {}
        if not hub_df.empty:
            for mod, grp in hub_df.groupby('module'):
                hub_genes[mod] = grp.nlargest(5, 'kME')[['gene', 'kME']].to_dict('records')

        return {
            'type': 'wgcna',
            'n_genes': len(modules_df),
            'n_samples': expr_subset.shape[1],
            'n_modules': len(module_summary),
            'soft_power': detected_power,
            'modules': module_summary,
            'hub_genes': hub_genes,
            'gene_modules': modules_df.to_dict('records')[:500],
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
