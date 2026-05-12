# BioInfo Platform

An intelligent bioinformatics analysis desktop application. Go from raw data to publication-ready figures, AI interpretation, and report export — all in one click.

![BioInfo Platform](https://via.placeholder.com/800x450/1E3A8A/FFFFFF?text=BioInfo+Platform+Dashboard)

---

## Download & Install

### Option 1: Installer (Recommended)

1. Go to [Releases](https://github.com/GodVfollower/auto-bioinfo/releases)
2. Download `BioInfo Platform Setup x.x.x.exe`
3. Double-click to install
4. Launch from desktop shortcut or Start Menu

> **Note**: Windows SmartScreen may show a warning because the app is not code-signed. Click "More info" → "Run anyway".

### Option 2: Build from Source

```bash
git clone https://github.com/GodVfollower/auto-bioinfo.git
cd auto-bioinfo
pip install -r backend/requirements.txt
python start.py
# Open http://localhost:8000 in browser
```

---

## Quick Start

1. **Get a DeepSeek API Key** (see below)
2. Launch BioInfo Platform
3. Click **Settings** (top-right) → Paste your API Key → Save
4. Go to **Data Import** → Enter file path → Click **Auto-Detect**
5. Follow the workflow: QC → Differential → Enrichment → Visualization → Interpretation → Export

---

## How to Get a DeepSeek API Key

DeepSeek is a Chinese AI provider with affordable API pricing (~1 RMB per million tokens).

1. Visit [platform.deepseek.com](https://platform.deepseek.com)
2. Register an account (phone number required for Chinese users)
3. Go to **API Keys** → Create a new key
4. **Top up your balance** (minimum ~10 RMB via Alipay/WeChat)
5. Copy the key (starts with `sk-`)
6. Paste it into BioInfo Platform → Settings

![DeepSeek Dashboard](https://via.placeholder.com/700x400/EFF6FF/1E3A8A?text=DeepSeek+Platform+Dashboard)

**Pricing reference**:
- `deepseek-chat` model: ~1 RMB per 1M input tokens, ~2 RMB per 1M output tokens
- Interpretation & storyline generation costs ~0.01-0.05 RMB per request

---

## Language Switching

The interface defaults to **English**. To switch to Chinese:

1. Click **Settings** (top-right gear icon)
2. Under **Language / 语言**, select **中文**
3. The UI switches instantly — all menu items, buttons, and descriptions update

> **Note**: Technical terms (RNA, DNA, PCR, GO, KEGG, GSEA, PCA, log2FC, FDR, P-value, etc.) are **never translated** and remain in English in both modes.

---

## Features

### Data Import & Auto-Detection
- Automatically identifies expression matrices, metadata, differential results, enrichment tables
- Supports CSV, TSV, TXT, Excel (.xlsx), GEO accession numbers
- Detects count matrices, TPM/FPKM, log-transformed data
- Validates sample names, missing values, duplicates, outliers

### Quality Control (7 Checks)
- Sample name matching between expression and metadata
- Missing value detection
- Duplicate gene names
- Non-numeric data detection
- Outlier detection (IQR method)
- log2 transformation recommendation
- Group balance assessment

### Differential Expression Analysis
- Methods: Welch t-test, Wilcoxon rank-sum, limma-like moderated t-test
- BH-FDR multiple testing correction
- Customizable thresholds: |log2FC|, P-value, FDR
- Low-expression gene filtering
- Up/down-regulated gene lists exported

### Enrichment Analysis
- **GO**: Biological Process (BP), Cellular Component (CC), Molecular Function (MF)
- **KEGG**: Pathway enrichment with built-in gene sets
- **GSEA**: Pre-ranked gene set enrichment with NES, ES, leading edge genes

### Visualization (13 Plot Types)
| Plot | Description |
|------|-------------|
| Volcano Plot | Differential expression overview |
| Heatmap | Gene expression patterns |
| PCA Plot | Sample clustering visualization |
| Correlation Heatmap | Sample-to-sample correlation |
| GO Bubble Chart | Enrichment bubble visualization |
| GO Bar Chart | Enrichment bar chart |
| KEGG Bubble Chart | Pathway enrichment bubble |
| KEGG Bar Chart | Pathway enrichment bar |
| GSEA Curve | Enrichment score running curve |
| Top DEG Barplot | Top differentially expressed genes |
| Key Gene Boxplot | Expression distribution |
| Key Gene Violin | Expression density |
| DEG Statistics | Up/down/NS summary |

All plots are **publication-quality** (white background, clean axes, Academic Blue color scheme). Export formats: PNG, PDF, SVG, TIFF (300/600 DPI).

### AI-Powered Intelligence
- **Result Interpretation**: Summary, Results section, Figure legends, Discussion, Validation recommendations
- **Storyline Recommendations**: 3-5 mechanism hypotheses with key genes, pathways, suggested figures, and paper titles

### Report Export
- **Excel**: Multi-sheet workbook (Differential, Up genes, Down genes, Enrichment, GSEA, Summary)
- **Word**: Full analysis report with tables, interpretation, and methods
- **PowerPoint**: 9-slide presentation for lab meetings or grant applications

---

## Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=Dashboard+with+Workflow+Steps)

### Data Import
![Data Import](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=Data+Import+Auto-Detection)

### Differential Analysis
![Differential](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=Differential+Analysis+Results)

### Enrichment Analysis
![Enrichment](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=GO+KEGG+Enrichment)

### Visualization
![Volcano Plot](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=Volcano+Plot+Example)

### AI Interpretation
![Interpretation](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=AI+Result+Interpretation)

### Storyline Recommendations
![Storyline](https://via.placeholder.com/800x450/F8FAFC/1E3A8A?text=Mechanism+Storylines)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / FastAPI / Uvicorn |
| Frontend | Vanilla JS / Academic Blue Theme |
| Desktop | Electron 28 |
| AI | DeepSeek API (OpenAI-compatible) |
| Analysis | numpy, pandas, scipy, scikit-learn, matplotlib, seaborn, statsmodels |
| Packaging | electron-builder (NSIS installer) |

## Project Structure

```
backend/modules/
  data_loader.py       - CSV/TSV/Excel file reading
  data_detector.py     - Auto-detect data type & structure
  quality_control.py   - 7 QC checks
  normalization.py     - log2, CPM, quantile, z-score
  differential.py      - t-test, Wilcoxon, limma, BH-FDR
  enrichment.py        - GO/KEGG hypergeometric test
  gsea_analysis.py     - GSEA implementation
  plotting.py          - 13 publication-quality plot types
  interpretation.py    - AI-powered result interpretation
  storyline.py         - Mechanism hypothesis generation
  report_export.py     - Excel + Word report
  ppt_export.py        - PowerPoint presentation
  scrna_interface.py   - scRNA-seq (coming soon)
frontend/
  js/i18n.js           - Chinese/English bilingual module
  js/pages/            - 11 SPA page modules
  css/academic-blue.css - Academic Blue Theme
```

---

## License

MIT
