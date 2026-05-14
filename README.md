# BEing Bio

A desktop bioinformatics analysis platform. RNA-seq data in → publication-ready figures out.

## Download

[Releases](https://github.com/GodVfollower/auto-bioinfo/releases) → `BEing-Bio-Setup-x.x.x.exe` → install → launch. No Python required.

---

## What It Does

```
Data Import → QC → Differential Analysis → Enrichment → Visualization → Export
```

### Analysis Engine

| Module | Method |
|--------|--------|
| Differential | DESeq2-like (median-of-ratios normalization + dispersion shrinkage + Wald test), t-test, Wilcoxon, limma-like |
| Enrichment | Hypergeometric test + BH-FDR + Storey q-value, backed by MSigDB Hallmark gene sets |
| GSEA | Permutation-based pre-ranked GSEA (1000 permutations), NES, leading edge |
| Multiple testing | Benjamini-Hochberg FDR + Storey q-value |

### Figure Export

All figures export as **vector PDF/SVG** (for Adobe Illustrator / Inkscape editing) and **300/600 DPI TIFF** (for journal submission). Standard academic workflow: export → refine in Illustrator → submit.

### AI Features *(DeepSeek API key required)*

- Interpretation: auto-generated Results section, figure legends, discussion
- Storyline: 3–5 mechanism hypotheses with validation suggestions

All other features work fully offline with no API key.

---

## Quick Start

1. Launch → **Data Import** → paste your expression matrix path → **Auto-Detect**
2. **QC** → **Differential** → **Enrichment** → **Visualization**
3. Export figures as PDF/SVG → refine in Illustrator → publish

---

## Language

Default English. Switch to Chinese via the dropdown next to Settings. Technical terms (RNA, DNA, GO, KEGG, log2FC, FDR, etc.) are never translated.

---

## Build from Source

```bash
git clone https://github.com/GodVfollower/auto-bioinfo.git
cd auto-bioinfo
pip install -r backend/requirements.txt
python start.py
```

For the Electron desktop app:
```bash
npm install
npm start
npm run build
```

---

## Tech Stack

Python / FastAPI / Electron / numpy / scipy / pandas / matplotlib / seaborn / statsmodels / openpyxl / python-docx / python-pptx

## License

MIT
