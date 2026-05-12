# BioInfo Platform

An intelligent bioinformatics analysis desktop application for RNA-seq data analysis.

## Features

- **Data Auto-Detection**: Automatically identify expression matrices, metadata, differential results, and enrichment tables
- **Quality Control**: 7 built-in QC checks (sample matching, missing values, duplicates, outliers, etc.)
- **Differential Analysis**: t-test, Wilcoxon, limma-like with BH-FDR correction
- **Enrichment Analysis**: GO (BP/CC/MF), KEGG, and GSEA with built-in gene sets
- **13 Publication-Quality Figures**: Volcano, heatmap, PCA, correlation, GO/KEGG bubble/bar, GSEA curve, etc.
- **AI Interpretation**: DeepSeek-powered result interpretation, figure legends, and discussion
- **Storyline Recommendation**: 3-5 mechanism hypotheses with validation suggestions
- **Report Export**: Excel, Word (.docx), PowerPoint (.pptx)
- **Academic Blue Theme**: Clean, professional UI for scientific workflows

## Quick Start

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run (browser mode)
python start.py

# Run (Electron desktop mode, requires Node.js)
npm install
npm start
```

## Build Standalone Installer

```bash
# 1. Set up embedded Python runtime
mkdir runtime
# Download Python 3.9 embed, install pip and dependencies into runtime/python/

# 2. Build installer
npm run build
# Output: dist-electron/BioInfo Platform Setup x.x.x.exe
```

## Project Structure

```
├── backend/            # Python FastAPI backend
│   ├── main.py         # API routes (v1 + v2)
│   ├── modules/        # Analysis modules
│   │   ├── data_loader.py
│   │   ├── data_detector.py
│   │   ├── quality_control.py
│   │   ├── normalization.py
│   │   ├── differential.py
│   │   ├── enrichment.py
│   │   ├── gsea_analysis.py
│   │   ├── plotting.py
│   │   ├── interpretation.py
│   │   ├── storyline.py
│   │   ├── report_export.py
│   │   ├── ppt_export.py
│   │   └── scrna_interface.py
│   └── ...
├── frontend/           # Academic Blue Theme UI
│   ├── index.html
│   ├── css/academic-blue.css
│   └── js/
│       ├── i18n.js     # Chinese/English bilingual
│       ├── app.js      # SPA router
│       ├── api.js      # API layer
│       └── pages/      # 11 page modules
├── electron/           # Electron desktop shell
│   ├── main.js
│   └── preload.js
├── backend_server.py   # Standalone server entry
└── start.py            # Dev launcher
```

## Tech Stack

- **Backend**: Python 3.9+ / FastAPI / Uvicorn
- **Frontend**: Vanilla JS / Academic Blue Theme
- **Desktop**: Electron 28
- **AI**: DeepSeek API (OpenAI-compatible)
- **Analysis**: numpy, pandas, scipy, scikit-learn, matplotlib, seaborn, statsmodels
- **Packaging**: electron-builder (NSIS installer)

## License

MIT
