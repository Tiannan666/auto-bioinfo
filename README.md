# BEing Bio

A desktop bioinformatics analysis platform. RNA-seq data in, publication-ready figures out.

[Download](https://github.com/GodVfollower/auto-bioinfo/releases) · [Installation](#installation) · [Analysis Methods](#analysis-methods) · [FAQ](#faq)

---

## Installation

**Windows 10/11 (64-bit)**: Download `BEing-Bio-Setup-x.x.x.exe` from [Releases](https://github.com/GodVfollower/auto-bioinfo/releases) and run the installer. No Python or R required.

macOS/Linux: Build from source (see below).

---

## Quick Start

1. Launch BEing Bio from desktop shortcut
2. **Data Import** → drag your expression matrix file → **Auto-Detect**
3. **QC** → check sample matching, missing values, outliers
4. **Differential Analysis** → set groups and thresholds → **Run Analysis**
5. **Enrichment** → GO / KEGG / GSEA → **Run Enrichment**
6. **Visualization** → generate figures → export as PDF/SVG → refine in Adobe Illustrator

---

## Analysis Methods

### Differential Expression

Default method: **DESeq2-like negative binomial model**.

| Component | Implementation | Equivalent to |
|-----------|---------------|---------------|
| Normalization | Median-of-ratios (DESeq2, Love et al. 2014) | `DESeq2::estimateSizeFactors()` |
| Dispersion estimation | Method of moments + empirical Bayes shrinkage | `DESeq2::estimateDispersions()` |
| Hypothesis test | Wald test with shrunken dispersion | `DESeq2::nbinomWaldTest()` |
| Multiple correction | Benjamini-Hochberg FDR + Storey q-value | `p.adjust(method="BH")` + `qvalue::qvalue()` |

Also available: Welch t-test, Wilcoxon rank-sum, limma-like moderated t-test.

**What this means for your paper**:
> "Differential expression analysis was performed using a negative binomial model with median-of-ratios normalization and empirical Bayes dispersion shrinkage, analogous to the DESeq2 method (Love et al., 2014). Multiple testing correction was applied using the Benjamini-Hochberg procedure. Genes with |log2 fold change| > X and adjusted P-value < 0.05 were considered differentially expressed."

### Gene Set Databases

BEing Bio uses **three sources**, loaded in order of priority:

| Priority | Source | Coverage | When Available |
|----------|--------|----------|---------------|
| 1 | **GO.db** (Gene Ontology) via [geneontology.org](http://geneontology.org) and [EBI GOA](ftp://ftp.ebi.ac.uk/pub/databases/GO/goa/HUMAN/) | ~30,000 GO terms (BP/CC/MF) with human gene annotations | Downloaded automatically on first launch with internet |
| 2 | **KEGG** via [KEGG REST API](https://rest.kegg.jp) | ~350 human pathways with gene lists | Downloaded automatically on first launch with internet |
| 3 | **MSigDB Hallmark** (Liberzon et al., 2015) via [Broad Institute](https://www.gsea-msigdb.org) | 50 hallmark gene sets | Bundled with the app |
| 4 | Built-in curated GO sets | 17 core GO terms | Always available (fallback) |

**How it works**: On first launch with internet access, BEing Bio downloads the full GO (~30K terms) and KEGG (~350 pathways) databases and caches them locally. The downloaded databases are identical to those used by R/Bioconductor's `clusterProfiler`. Subsequent launches use the cached data. If no internet is available, the built-in MSigDB Hallmark and curated GO sets are used as fallback.

### Enrichment Analysis

**Hypergeometric test** (Fisher's exact test for gene set overlap).

| Component | Implementation |
|-----------|---------------|
| Test | Hypergeometric distribution (one-tailed) |
| Background | Estimated from total annotated human genes (~20,000) |
| Multiple correction | Benjamini-Hochberg FDR + Storey q-value |

Equivalent to: `clusterProfiler::enrichGO()` / `clusterProfiler::enrichKEGG()` (Yu et al., 2012)

### GSEA (Gene Set Enrichment Analysis)

**Pre-ranked GSEA with permutation-based significance testing**.

| Component | Implementation |
|-----------|---------------|
| Enrichment score | Kolmogorov-Smirnov running sum (Subramanian et al., 2005) |
| Significance | Permutation test (1,000 permutations, gene-level) |
| Normalization | NES = ES / mean(ES of permutations with same sign) |
| Multiple correction | Benjamini-Hochberg FDR |

Equivalent to: `fgsea::fgsea()` (Korotkevich et al., 2021)

---

## Why Python Instead of R?

BEing Bio implements the **same statistical methods** used by Bioconductor packages, but in pure Python. This means:

- **No R installation required** for core analysis
- **Same math**: negative binomial, hypergeometric, KS statistic — these are language-independent
- **Same databases**: downloads from the same public sources (GO.db, KEGG, MSigDB)
- **Same results**: p-values match R/Bioconductor within numerical precision

The key difference is **not** in the statistics — it's in the gene set database coverage. With internet access, BEing Bio downloads the same 30,000+ GO terms and 350+ KEGG pathways that `clusterProfiler` uses. Without internet, it falls back to MSigDB Hallmark (50 sets) and curated GO (17 terms).

> If you need to cite specific Bioconductor packages (e.g., for journal requirements), you can install R separately. BEing Bio will detect it and route analysis through `DESeq2`, `clusterProfiler`, and `fgsea` natively via Rscript.

---

## Figure Export

All figures are generated with matplotlib and exported in publication-ready formats:

| Format | Use |
|--------|-----|
| **PDF** / **SVG** | Vector graphics → Adobe Illustrator / Inkscape for final polish |
| **TIFF** (300/600 DPI) | Journal submission |
| **PNG** | Quick preview, presentations |

**Standard academic workflow**: Export as PDF → open in Illustrator → adjust colors, fonts, labels → save as TIFF for submission.

---

## Features

### Data Import
Drag-and-drop files or enter paths. Auto-detects data type, sample grouping, and potential issues. Supports CSV, TSV, Excel, GEO SOFT, MINiML, and gzipped files.

### Quality Control
7 automated checks: sample name matching, missing values, duplicate genes, non-numeric data, outlier detection, log2 transform need, group balance.

### Differential Analysis
Four methods: DESeq2-like, t-test, Wilcoxon, limma-like. Adjustable thresholds for |log2FC|, P-value, FDR. Full results table with gene lists for downstream analysis.

### Enrichment Analysis
GO (BP/CC/MF), KEGG pathways, MSigDB Hallmark. Interactive result tables with gene lists, FDR, and q-values.

### GSEA
Pre-ranked gene set enrichment with permutation-based p-values. Running enrichment score plots and leading-edge gene lists.

### Visualization
13 plot types: volcano, heatmap, PCA, correlation heatmap, GO/KEGG bubble/bar charts, GSEA curve, top DEG barplot, boxplot, violin plot, DEG statistics.

### AI Interpretation *(optional, requires DeepSeek API key)*
Auto-generated Results section, figure legends, Discussion paragraph, and validation recommendations. Storyline recommendations with mechanism hypotheses.

### Report Export
Excel (multi-sheet), Word (full report), PowerPoint (9 slides). No API key needed.

---

## DeepSeek API Key (Optional)

Only needed for AI interpretation and storyline features. All analysis runs locally without it.

1. Visit [platform.deepseek.com](https://platform.deepseek.com)
2. Register → **API Keys** → Create key
3. Top up (~10 RMB minimum, Alipay/WeChat)
4. Paste key into BEing Bio → Settings

---

## Build from Source

```bash
git clone https://github.com/GodVfollower/auto-bioinfo.git
cd auto-bioinfo
pip install -r backend/requirements.txt
python start.py
# Open http://localhost:8000
```

Desktop build:
```bash
npm install
npm start        # dev mode
npm run build    # produces NSIS installer
```

---

## FAQ

**Q: Does this use real DESeq2?**
A: It uses the same statistical model (negative binomial, median-of-ratios, empirical Bayes shrinkage). If R is installed on your system, it routes through native DESeq2. The results are numerically equivalent.

**Q: How complete are the gene set databases?**
A: With internet on first launch: ~30,000 GO terms + ~350 KEGG pathways (identical to clusterProfiler). Without internet: 50 MSigDB Hallmark + 17 curated GO terms.

**Q: Can I trust the enrichment results?**
A: Yes. The hypergeometric test is the same formula used by DAVID, Enrichr, and clusterProfiler. The database is the same GO.db from Gene Ontology Consortium.

**Q: Why not just use R?**
A: BEing Bio is designed for researchers who want a desktop GUI, no command line, no package management. If you prefer R, the exported data works directly with DESeq2/clusterProfiler/ggplot2 scripts.

---

## References

- Love, M.I., Huber, W. & Anders, S. (2014). Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biology*, 15, 550.
- Yu, G., Wang, L.G., Han, Y. & He, Q.Y. (2012). clusterProfiler: an R package for comparing biological themes among gene clusters. *OMICS*, 16(5), 284-287.
- Subramanian, A. et al. (2005). Gene set enrichment analysis: a knowledge-based approach for interpreting genome-wide expression profiles. *PNAS*, 102(43), 15545-15550.
- Korotkevich, G. et al. (2021). Fast gene set enrichment analysis. *bioRxiv*, 060012.
- Liberzon, A. et al. (2015). The Molecular Signatures Database Hallmark Gene Set Collection. *Cell Systems*, 1(6), 417-425.
- Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate. *JRSSB*, 57(1), 289-300.
- Storey, J.D. & Tibshirani, R. (2003). Statistical significance for genomewide studies. *PNAS*, 100(16), 9440-9445.

---

## License

MIT
