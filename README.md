# BEing Bio — Intelligent Platform

An AI-powered bioinformatics desktop application. Go from raw data to publication-ready figures, interpretation, and report export — no Python required.

---

## Download

Go to [Releases](https://github.com/GodVfollower/auto-bioinfo/releases) → download `BEing-Bio-Setup-x.x.x.exe` → double-click to install.

> Windows SmartScreen may warn because the app is not code-signed. Click "More info" → "Run anyway".

---

## Quick Start

1. Launch BEing Bio from the desktop shortcut
2. **Data Import** → enter your expression matrix file path → click **Auto-Detect**
3. Follow the workflow: **QC** → **Differential** → **Enrichment** → **Visualization**
4. Optionally: **Settings** → paste DeepSeek API Key → use **Interpretation** & **Storyline**

---

## Features

### Data Import & Auto-Detection
Automatically identifies expression matrices (counts/TPM/FPKM), metadata, differential results, and enrichment tables. Supports CSV, TSV, TXT, Excel, and GEO accession numbers.

### Quality Control (7 checks)
Sample name matching, missing values, duplicate genes, non-numeric data, outlier detection, log2 transform recommendation, group balance assessment.

### Differential Expression Analysis
t-test (Welch), Wilcoxon rank-sum, limma-like moderated t-test with BH-FDR correction. Customizable thresholds for |log2FC|, P-value, and FDR.

### Enrichment Analysis
GO (BP/CC/MF), KEGG pathway, and GSEA with built-in gene sets and hypergeometric test.

### Visualization (13 plot types)
Volcano plot, heatmap, PCA, correlation heatmap, GO/KEGG bubble/bar charts, GSEA curve, top DEG barplot, boxplot, violin plot, DEG statistics. All publication-quality with Academic Blue style. Export as PNG, PDF, SVG, or TIFF at 300/600 DPI.

### AI-Powered Intelligence *(requires DeepSeek API Key)*
- **Interpretation**: Summary, Results section, Figure legends, Discussion, Validation recommendations
- **Storyline**: 3–5 mechanism hypotheses with key genes, pathways, validation experiments, and suggested figures

### Report Export *(no API key needed)*
- **Excel**: Multi-sheet workbook (Differential / Up genes / Down genes / Enrichment / GSEA / Summary)
- **Word**: Full analysis report with tables, interpretation, and methods
- **PowerPoint**: 9-slide presentation for lab meetings or grants

---

## DeepSeek API Key (optional)

Only needed for Interpretation and Storyline. All other features work offline.

1. Go to [platform.deepseek.com](https://platform.deepseek.com)
2. Register → **API Keys** → Create new key
3. **Top up** (minimum ~10 RMB via Alipay/WeChat)
4. Paste the key into BEing Bio → Settings

Pricing: ~1 RMB per 1M tokens. A full interpretation costs ~0.01–0.05 RMB.

---

## Language Switching

The interface defaults to English. To switch:

1. Click **Settings** (top-right)
2. Under **Language**, select **中文**

Technical terms (RNA, DNA, PCR, GO, KEGG, GSEA, PCA, log2FC, FDR, P-value, etc.) are never translated.

---

## Build from Source

```bash
git clone https://github.com/GodVfollower/auto-bioinfo.git
cd auto-bioinfo
pip install -r backend/requirements.txt
python start.py
# Open http://localhost:8000
```

For the Electron desktop build:

```bash
npm install
npm start
npm run build    # produces the installer
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / FastAPI / Uvicorn |
| Frontend | Vanilla JS / Academic Blue Theme |
| Desktop | Electron 28 |
| AI | DeepSeek API (OpenAI-compatible) |
| Analysis | numpy, pandas, scipy, scikit-learn, matplotlib, seaborn, statsmodels |
| Reports | openpyxl, python-docx, python-pptx |
| Packaging | electron-builder (NSIS installer) |

---

## License

MIT
