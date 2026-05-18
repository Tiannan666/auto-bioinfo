# BEing Bio

<p align="center">
  <img src="frontend/assets/logo.png" width="120" alt="BEing Bio Logo">
</p>

<p align="center">
  A desktop bioinformatics analysis platform.<br>
  RNA-seq data in, publication-ready figures out.
</p>

<p align="center">
  <a href="https://github.com/GodVfollower/auto-bioinfo/releases">Download</a> · 
  <a href="#architecture">Architecture</a> · 
  <a href="#installation">Installation</a> · 
  <a href="#analysis-methods">Analysis Methods</a> · 
  <a href="#faq">FAQ</a>
</p>

---

## Architecture

BEing Bio is a **hybrid desktop application** with a dual-engine architecture:

```
┌──────────────────────────────────────────────────────────────┐
│  Electron Shell (UI & Process Management)                    │
│  ┌────────────────────────┐  ┌─────────────────────────────┐│
│  │   Frontend (HTML/JS)   │  │     Main Process (Node.js)  ││
│  │   - Academic Blue UI   │  │     - R runtime management  ││
│  │   - 13 plot types      │  │     - Python backend launch ││
│  │   - i18n (CN/EN)       │  │     - Auto-update logic     ││
│  └────────────────────────┘  └─────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│  Python Backend (FastAPI/Uvicorn)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ Diff Express │  │  Enrichment  │  │   GSEA Analysis    │ │
│  │ DESeq2-like  │  │  GO / KEGG   │  │   fgsea-based      │ │
│  │ edgeR-like   │  │  MSigDB      │  │   Pre-ranked       │ │
│  │ limma-like   │  │              │  │                    │ │
│  └──────────────┘  └──────────────┘  └────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  QC Module   │  │  Viz Engine  │  │  AI Interpretation │ │
│  │  7 checks    │  │  matplotlib  │  │  DeepSeek API      │ │
│  └──────────────┘  └──────────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│  R Engine (Bioconductor, via subprocess)                      │
│  DESeq2 · edgeR · limma · clusterProfiler · fgsea · ggplot2 │
│  org.Hs.eg.db · org.Mm.eg.db · org.Rn.eg.db · enrichplot   │
└──────────────────────────────────────────────────────────────┘
```

### Core Design Decisions

| Decision | Rationale |
|----------|-----------|
| Electron + Python + R | GUI without browser, statistical power of Python/R, no cloud dependency |
| Pre-packaged R runtime | Eliminates BiocManager install failures, works offline after first setup |
| Runtime in install directory | User controls disk usage, no hidden C: drive bloat |
| Python fallback for enrichment | App still works without R for basic analysis (gene database download) |
| FastAPI backend | RESTful, async, easy to extend, serves both UI and API |

### Technology Stack

| Layer | Tech | Version |
|-------|------|---------|
| Desktop Shell | Electron | 28.x |
| Frontend | Vanilla HTML/CSS/JS | - |
| Backend | Python + FastAPI + Uvicorn | 3.11 |
| Statistics | NumPy, SciPy, pandas, statsmodels | - |
| Visualization | matplotlib | 3.8+ |
| Bioinformatics | R 4.6 + Bioconductor 3.21 | Pre-packaged |
| Build | electron-builder (NSIS) | 25.x |

---

## Installation

### Windows Installer (Recommended)

1. Download `BEing-Bio-Setup-x.x.x.exe` from [Releases](https://github.com/GodVfollower/auto-bioinfo/releases)
2. Run installer — choose any installation directory
3. First launch: R engine (~450MB) downloads automatically, then extracts
4. Done. All subsequent launches take 2-3 seconds.

**Requirements:**
- Windows 10 or 11 (64-bit)
- ~2GB disk space (app + R runtime)
- Internet on first launch only (for R engine download)
- No admin rights needed
- No Python or R installation needed

### What Happens on First Launch

```
App starts → Python backend ready (2s)
           → R engine not found
           → Show setup window
           → Download r-runtime.tar.gz from GitHub Release (450MB)
           → Extract with system tar to {install-dir}/runtime/R/
           → Done, show main window
```

The R runtime includes all 10 pre-compiled Bioconductor packages. No compilation, no BiocManager, no mirror issues.

### File Layout After Installation

```
D:\BEing Bio\                    ← User-chosen install path
├── BEing Bio.exe                ← Main executable
├── resources/
│   ├── runtime.zip              ← Python runtime (auto-extracted)
│   ├── backend/                 ← Python analysis modules
│   ├── backend_server.py        ← FastAPI server
│   └── frontend/                ← Web UI
├── runtime/
│   ├── python/                  ← Embedded Python 3.11
│   └── R/                       ← R 4.6 + Bioconductor packages
│       ├── bin/Rscript.exe
│       └── library/             ← 163 pre-compiled packages
└── data/                        ← User analysis results
```

Everything stays inside the installation directory. Nothing goes to `C:\Users\AppData`.

---

## Features

### Data Import
Drag-and-drop or browse. Auto-detects format, sample grouping, and issues.
Supports: CSV, TSV, Excel, GEO SOFT, MINiML, gzipped files.

### Quality Control (7 Automated Checks)
- Sample name matching between groups
- Missing value detection & imputation suggestions
- Duplicate gene ID handling
- Non-numeric data filtering
- Outlier detection (IQR-based)
- Log2 transformation assessment
- Group balance evaluation

### Differential Expression Analysis
Four methods, all producing log2FC + p-value + FDR:

| Method | Best for | Implementation |
|--------|----------|----------------|
| DESeq2-like | RNA-seq counts (default) | Negative binomial, median-of-ratios normalization, EB shrinkage |
| edgeR-like | Small sample RNA-seq | Trimmed mean of M-values, tagwise dispersion |
| limma-like | Microarray / large datasets | Moderated t-statistic, empirical Bayes |
| t-test/Wilcoxon | Simple comparisons | Welch t-test or rank-sum |

### Enrichment Analysis
- **GO** (Biological Process, Cellular Component, Molecular Function)
- **KEGG** pathway enrichment
- **MSigDB** Hallmark gene sets
- Species: Human (hsa), Mouse (mmu), Rat (rno)
- Method: Hypergeometric test + BH-FDR correction

### GSEA (Gene Set Enrichment Analysis)
- Pre-ranked by log2FC x -log10(p)
- fgsea algorithm (fast approximate permutation)
- Running enrichment score plots
- Leading-edge gene identification

### Visualization (13 Plot Types)
Volcano, heatmap, PCA, correlation matrix, GO/KEGG bubble charts, GO/KEGG bar charts, GSEA running score curve, top DEG barplot, boxplot, violin plot, DEG statistics summary.

All plots: publication-ready, export as PDF/SVG/TIFF(300/600dpi)/PNG.

### AI Interpretation (Optional)
Requires DeepSeek API key. Generates:
- Results section text
- Figure legends
- Discussion paragraph
- Validation recommendations
- Storyline with mechanism hypotheses

### Report Export
- **Excel**: Multi-sheet workbook (DEGs, enrichment, GSEA, stats)
- **Word**: Full formatted report
- **PowerPoint**: 9-slide presentation
- No API key needed for reports

---

## Analysis Methods (For Methods Section)

### Differential Expression

> "Differential expression analysis was performed using a negative binomial generalized linear model with median-of-ratios normalization and empirical Bayes dispersion shrinkage, analogous to the DESeq2 framework (Love et al., 2014). Multiple testing correction was applied using the Benjamini-Hochberg procedure. Genes with |log2 fold change| > X and adjusted P-value < 0.05 were considered differentially expressed."

### Enrichment

> "Functional enrichment analysis was performed using a hypergeometric test against Gene Ontology (BP, CC, MF) and KEGG pathway databases via clusterProfiler (Yu et al., 2012). P-values were corrected for multiple testing using the Benjamini-Hochberg method. Terms with FDR < 0.05 were considered significantly enriched."

### GSEA

> "Gene Set Enrichment Analysis was performed on pre-ranked gene lists using the fgsea algorithm (Korotkevich et al., 2021) with 10,000 permutations. Gene sets with |NES| > 1 and FDR < 0.25 were considered significantly enriched."

---

## Gene Set Databases

| Source | Coverage | Acquisition |
|--------|----------|-------------|
| GO.db (Gene Ontology) | ~30,000 terms (BP/CC/MF) | Via R org.*.eg.db packages (pre-packaged) |
| KEGG REST API | ~350 human pathways | Downloaded on first enrichment run |
| MSigDB Hallmark | 50 gene sets | Bundled with app |

Three species supported: Human (`org.Hs.eg.db`), Mouse (`org.Mm.eg.db`), Rat (`org.Rn.eg.db`).

---

## DeepSeek API Key (Optional)

Only needed for AI text generation. All analysis runs locally without it.

1. Visit [platform.deepseek.com](https://platform.deepseek.com)
2. Register -> **API Keys** -> Create key
3. Top up (~10 RMB, Alipay/WeChat)
4. Paste into BEing Bio -> Settings

---

## Build from Source

```bash
git clone https://github.com/GodVfollower/auto-bioinfo.git
cd auto-bioinfo

# Backend (Python)
pip install -r backend/requirements.txt
python backend_server.py --port 8000
# Open http://localhost:8000

# Desktop app (Electron)
npm install
npm start           # dev mode
npm run build       # NSIS installer -> dist-electron/
```

### Preparing R Runtime for Distribution

```bash
# On a machine with R + Bioconductor installed:
Rscript -e "
BiocManager::install(c('DESeq2','edgeR','limma','clusterProfiler',
  'fgsea','ggplot2','org.Hs.eg.db','org.Mm.eg.db','org.Rn.eg.db','enrichplot'))
"

# Package (strip docs to reduce size):
cd "C:/Program Files/R/R-4.x.x"
tar -czf r-runtime.tar.gz bin/ etc/ modules/ share/ library/

# Upload to GitHub Release:
gh release upload v1.0.0 r-runtime.tar.gz
```

---

## FAQ

**Q: Does this require R to be installed?**
A: No. R is automatically downloaded as a pre-packaged runtime on first launch. You never interact with R directly.

**Q: Where does data get stored?**
A: Everything stays in your chosen installation directory under `runtime/` and `data/`. Nothing is written to C:\AppData or other hidden locations.

**Q: Does this use real DESeq2/clusterProfiler?**
A: Yes. The R engine routes analysis through native Bioconductor packages (DESeq2, clusterProfiler, fgsea) via Rscript subprocess. Results are identical to running R directly.

**Q: What if the first-launch download fails?**
A: The app shows a "Retry" button. Downloads support resume - if interrupted, it picks up where it left off next time. No work is lost.

**Q: Can I use this offline?**
A: After the initial R engine download, everything works fully offline. Gene annotation databases are included in the pre-packaged R runtime.

**Q: What size is the full installation?**
A: ~195MB installer + ~450MB R engine download = ~1.5GB total on disk after extraction.

**Q: Can I trust the statistical results for publication?**
A: Yes. The app calls native Bioconductor packages (DESeq2, clusterProfiler, fgsea) through R subprocess. For citation, reference the original Bioconductor packages directly.

---

## References

- Love, M.I., Huber, W. & Anders, S. (2014). Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biology*, 15, 550.
- Yu, G., Wang, L.G., Han, Y. & He, Q.Y. (2012). clusterProfiler: an R package for comparing biological themes among gene clusters. *OMICS*, 16(5), 284-287.
- Subramanian, A. et al. (2005). Gene set enrichment analysis: a knowledge-based approach for interpreting genome-wide expression profiles. *PNAS*, 102(43), 15545-15550.
- Korotkevich, G. et al. (2021). Fast gene set enrichment analysis. *bioRxiv*, 060012.
- Liberzon, A. et al. (2015). The Molecular Signatures Database Hallmark Gene Set Collection. *Cell Systems*, 1(6), 417-425.
- Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate. *JRSSB*, 57(1), 289-300.

---

## License

MIT
