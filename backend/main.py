"""FastAPI server — BioInfo Platform."""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .sandbox import run_code, extract_code_blocks
from .deepseek_client import chat, load_config, save_config
from .bio_prompt import is_bio_request

# v2 modules
from .modules.data_detector import detect_data
from .modules.data_loader import load_expression_matrix, load_metadata
from .modules.quality_control import run_qc
from .modules.differential import run_differential
from .modules.enrichment import run_enrichment
from .modules.gsea_analysis import run_gsea
from .modules.plotting import generate_plot, export_plot, set_output_dir, PLOT_FUNCTIONS
from .modules.interpretation import generate_interpretation
from .modules.storyline import generate_storylines
from .modules.report_export import export_excel, export_word
from .modules.ppt_export import export_ppt
from .modules.scrna_interface import scrna_status
from .modules.task_logger import TaskLogger
from .modules.file_manager import get_project_dir, ensure_dir

app = FastAPI(title="BEing Bio", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(os.environ.get("BIOINFO_DATA_DIR", str(Path(__file__).parent.parent)))
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
set_output_dir(OUTPUT_DIR)

logger = TaskLogger(DATA_DIR)

# In-memory state (simplified for MVP)
_state: Dict = {}


# ========== v1 Endpoints (legacy chat) ==========

class ChatRequest(BaseModel):
    messages: List[Dict]

class ConfigRequest(BaseModel):
    deepseek_api_key: str

class ConfigStatus(BaseModel):
    configured: bool
    has_key: bool

@app.get("/api/config/status")
async def get_config_status():
    config = load_config()
    return ConfigStatus(
        configured=bool(config.get("deepseek_api_key")),
        has_key=bool(config.get("deepseek_api_key")),
    )

@app.post("/api/config")
async def update_config(req: ConfigRequest):
    config = load_config()
    config["deepseek_api_key"] = req.deepseek_api_key.strip()
    save_config(config)
    return {"ok": True}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    last_user_msg = ""
    for m in reversed(req.messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break
    if last_user_msg and not is_bio_request(last_user_msg):
        return {
            "message": {"role": "assistant", "content": "Sorry, I only support bioinformatics analysis tasks."},
            "executions": [],
        }
    result = chat(req.messages)
    if result["error"]:
        return {"message": {"role": "assistant", "content": f"**Error**: {result['error']}"}, "executions": []}
    response_text = result["content"] or "No response generated."
    code_blocks = extract_code_blocks(response_text)
    executions = []
    for code in code_blocks:
        exec_result = run_code(code)
        executions.append({
            "output": exec_result.stdout,
            "images": exec_result.images,
            "error": exec_result.error if not exec_result.success else None,
        })
        if exec_result.stdout:
            response_text += "\n\n**Output:**\n```\n" + exec_result.stdout + "\n```\n"
        if exec_result.error:
            response_text += f"\n\n**Error:**\n```\n{exec_result.error}\n```\n"
        for img in exec_result.images:
            response_text += f"\n![Figure]({img})\n"
    return {"message": {"role": "assistant", "content": response_text}, "executions": executions}

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ========== v2 Endpoints ==========

# --- Data ---

class DataDetectRequest(BaseModel):
    path: str

class DataLoadRequest(BaseModel):
    path: str
    metadata_path: Optional[str] = None

@app.post("/api/v2/data/detect")
async def v2_data_detect(req: DataDetectRequest):
    try:
        result = detect_data(req.path)
        _state['last_path'] = req.path
        return result
    except Exception as e:
        return {"error": str(e), "data_type": "unknown"}

@app.post("/api/v2/data/load")
async def v2_data_load(req: DataLoadRequest):
    try:
        expr = load_expression_matrix(req.path)
        project_id = logger.start_session(f"Analysis_{Path(req.path).stem}")
        _state['project_id'] = project_id
        _state['expression_matrix'] = expr['matrix']
        _state['gene_ids'] = expr['gene_ids']
        _state['sample_ids'] = expr['sample_ids_full']

        meta = None
        if req.metadata_path:
            meta = load_metadata(req.metadata_path)
            _state['metadata'] = meta

        logger.log_step(project_id, "data_load", {"path": req.path})
        return {
            "project_id": project_id,
            "data_type": expr['data_type'],
            "n_genes": expr['n_genes'],
            "n_samples": expr['n_samples'],
            "sample_ids": expr['sample_ids_full'][:30],
            "gene_ids_preview": expr['gene_ids'][:10],
            "metadata_loaded": meta is not None,
        }
    except Exception as e:
        return {"error": str(e)}


# --- QC ---

class QCRunRequest(BaseModel):
    project_id: str = "current"

@app.post("/api/v2/qc/run")
async def v2_qc_run(req: QCRunRequest):
    matrix = _state.get('expression_matrix')
    meta = _state.get('metadata')
    if matrix is None:
        return {"error": "No data loaded. Please load data first."}
    groups = _state.get('groups', None)
    result = run_qc(matrix, meta, groups)
    logger.log_step(_state.get('project_id', 'unknown'), "qc", result={"passed": result['passed'], "total": result['total']})
    return result


# --- Analysis ---

class DiffAnalysisRequest(BaseModel):
    project_id: str = "current"
    group1: str = ""
    group2: str = ""
    logfc: float = 1.0
    pval: float = 0.05
    fdr: float = 0.05
    method: str = "ttest"
    log2: bool = True
    filter_low: bool = True

class EnrichmentRequest(BaseModel):
    project_id: str = "current"
    type: str = "go"
    source: str = "diff"
    pval_cutoff: float = 0.05
    go_bp: bool = True
    go_cc: bool = True
    go_mf: bool = True
    msigdb: bool = False
    gsea_geneset: Optional[str] = None

@app.post("/api/v2/analysis/differential")
async def v2_diff_analysis(req: DiffAnalysisRequest):
    matrix = _state.get('expression_matrix')
    if matrix is None:
        return {"error": "No data loaded. Please load data first."}

    sample_ids = _state.get('sample_ids', matrix.select_dtypes(include=['number']).columns.tolist())
    g1_samples = [s for s in sample_ids if req.group1.lower() in s.lower()] if req.group1 else sample_ids[:len(sample_ids)//2]
    g2_samples = [s for s in sample_ids if req.group2.lower() in s.lower()] if req.group2 else sample_ids[len(sample_ids)//2:]

    if not g1_samples or not g2_samples:
        if req.group1 and req.group2:
            # Try using all samples split
            g1_samples = sample_ids[:len(sample_ids)//2]
            g2_samples = sample_ids[len(sample_ids)//2:]
        else:
            return {"error": "Could not determine groups. Please specify group names that match sample IDs."}

    try:
        result = run_differential(
            matrix, g1_samples, g2_samples,
            method=req.method, logfc_threshold=req.logfc,
            pval_threshold=req.pval, fdr_threshold=req.fdr,
            log2_transform=req.log2, filter_low=req.filter_low,
        )
        result['group1_name'] = req.group1 or 'Group1'
        result['group2_name'] = req.group2 or 'Group2'
        _state['diff_result'] = result
        logger.log_step(_state.get('project_id', 'unknown'), "differential",
                       {"method": req.method, "logfc": req.logfc, "fdr": req.fdr},
                       {"n_up": result['n_up'], "n_down": result['n_down']})
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v2/analysis/enrichment")
async def v2_enrichment(req: EnrichmentRequest):
    diff = _state.get('diff_result')
    if not diff:
        return {"error": "No differential analysis results. Run differential analysis first."}

    if req.source == 'up':
        gene_list = diff.get('up_genes', [])
    elif req.source == 'down':
        gene_list = diff.get('down_genes', [])
    else:
        gene_list = diff.get('sig_genes', [])

    if not gene_list:
        return {"error": "No significant genes found. Adjust thresholds or use a different source."}

    try:
        result = run_enrichment(gene_list, pval_cutoff=req.pval_cutoff,
                               go_bp=req.go_bp, go_cc=req.go_cc, go_mf=req.go_mf,
                               kegg=True, msigdb=req.msigdb)
        _state['enrich_result'] = result
        logger.log_step(_state.get('project_id', 'unknown'), "enrichment",
                       {"pval_cutoff": req.pval_cutoff, "n_genes": len(gene_list)},
                       {"n_terms": result['n_terms']})
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v2/analysis/gsea")
async def v2_gsea(req: EnrichmentRequest):
    diff = _state.get('diff_result')
    if not diff:
        return {"error": "No differential analysis results."}

    all_genes = diff.get('all_genes', [])
    if not all_genes:
        return {"error": "No gene data available."}

    ranked = sorted(all_genes, key=lambda g: g.get('log2FC', 0), reverse=True)
    genes = [g['gene'] for g in ranked]
    scores = [g.get('log2FC', 0) for g in ranked]

    try:
        result = run_gsea(genes, scores, gene_set_type=req.gsea_geneset or 'go',
                         pval_cutoff=req.pval_cutoff)
        _state['gsea_result'] = result
        return result
    except Exception as e:
        return {"error": str(e)}


# --- Plots ---

class PlotRequest(BaseModel):
    plot_type: str = "volcano"
    project_id: str = "current"
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    font_size: int = 12
    width: float = 8
    height: float = 6
    dpi: int = 300
    up_color: str = "#DC2626"
    down_color: str = "#2563EB"
    show_labels: bool = False
    show_legend: bool = True
    show_logfc_line: bool = True
    top_n: int = 20

class PlotExportRequest(BaseModel):
    plot_name: str = "volcano"
    format: str = "pdf"
    dpi: int = 300

@app.post("/api/v2/plots/generate")
async def v2_plots_generate(req: PlotRequest):
    set_output_dir(OUTPUT_DIR)
    diff = _state.get('diff_result')
    enrich = _state.get('enrich_result')
    gsea = _state.get('gsea_result')
    matrix = _state.get('expression_matrix')

    params = {k: v for k, v in req.dict().items() if v is not None}

    try:
        if req.plot_type in ('volcano', 'top_genes', 'deg_stats'):
            if not diff:
                return {"error": "Run differential analysis first."}
            result = generate_plot(req.plot_type, diff_result=diff, params=params)
        elif req.plot_type in ('heatmap', 'pca', 'correlation'):
            if matrix is None:
                return {"error": "Load data first."}
            result = generate_plot(req.plot_type, matrix=matrix, params=params)
        elif req.plot_type in ('go_bubble', 'go_bar', 'kegg_bubble', 'kegg_bar'):
            if not enrich:
                return {"error": "Run enrichment analysis first."}
            result = generate_plot(req.plot_type, enrich_result=enrich, params=params)
        elif req.plot_type == 'gsea_curve':
            if not gsea:
                return {"error": "Run GSEA first."}
            result = generate_plot(req.plot_type, gsea_result=gsea, params=params)
        elif req.plot_type in ('boxplot', 'violin'):
            if matrix is None or not diff:
                return {"error": "Load data and run differential analysis first."}
            top_genes = [g['gene'] for g in diff.get('top_genes', [])[:5]]
            result = generate_plot(req.plot_type, matrix=matrix, genes=top_genes, params=params)
        else:
            return {"error": f"Unknown plot type: {req.plot_type}"}

        return {"images": list(result.values()), "plot_type": req.plot_type}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v2/plots/export")
async def v2_plots_export(req: PlotExportRequest):
    try:
        path = export_plot(req.plot_name, req.format, req.dpi)
        return {"file": str(path), "format": req.format}
    except Exception as e:
        return {"error": str(e)}


# --- Intelligence ---

class InterpretationRequest(BaseModel):
    project_id: str = "current"
    focus: str = ""
    language: str = "zh"

class StorylineRequest(BaseModel):
    project_id: str = "current"
    count: int = 5
    language: str = "both"

@app.post("/api/v2/interpretation/generate")
async def v2_interpretation(req: InterpretationRequest):
    diff = _state.get('diff_result')
    enrich = _state.get('enrich_result')
    gsea = _state.get('gsea_result')
    try:
        result = generate_interpretation(diff, enrich, gsea, req.focus, req.language)
        _state['interpretation'] = result
        return result
    except Exception as e:
        return {"error": str(e), "summary": "Interpretation requires API key."}

@app.post("/api/v2/storyline/generate")
async def v2_storyline(req: StorylineRequest):
    diff = _state.get('diff_result')
    enrich = _state.get('enrich_result')
    gsea = _state.get('gsea_result')
    try:
        result = generate_storylines(diff, enrich, gsea, req.count, req.language)
        _state['storyline'] = result
        return result
    except Exception as e:
        return {"error": str(e), "storylines": []}


# --- Report Export ---

class ReportExportRequest(BaseModel):
    project_id: str = "current"
    type: str = "all"
    include_interpretation: bool = True
    include_storyline: bool = True
    include_figures: bool = True

@app.post("/api/v2/report/export")
async def v2_report_export(req: ReportExportRequest):
    diff = _state.get('diff_result')
    enrich = _state.get('enrich_result')
    gsea = _state.get('gsea_result')
    interp = _state.get('interpretation')
    story = _state.get('storyline')

    proj_dir = get_project_dir(DATA_DIR, req.project_id)
    files = []

    if req.type in ('excel', 'all'):
        r = export_excel(diff, enrich, gsea, proj_dir)
        if 'files' in r: files.extend(r['files'])

    if req.type in ('word', 'all'):
        r = export_word(diff, enrich, gsea, interp if req.include_interpretation else None, proj_dir)
        if 'files' in r: files.extend(r['files'])

    if req.type in ('ppt', 'all'):
        r = export_ppt(diff, enrich, story if req.include_storyline else None, proj_dir)
        if 'files' in r: files.extend(r['files'])

    return {
        "files": files,
        "output_dir": str(proj_dir),
        "type": req.type,
    }


# --- Projects ---

@app.get("/api/v2/projects/list")
async def v2_projects_list():
    sessions = logger.list_sessions()
    return {"projects": sessions}

@app.get("/api/v2/tasks/status")
async def v2_task_status(task_id: str = ""):
    return {
        "task_id": task_id,
        "project_id": _state.get('project_id', 'none'),
        "has_data": _state.get('expression_matrix') is not None,
        "has_diff": _state.get('diff_result') is not None,
        "has_enrich": _state.get('enrich_result') is not None,
        "has_gsea": _state.get('gsea_result') is not None,
    }


# --- scRNA-seq ---

@app.get("/api/v2/scrna/status")
async def v2_scrna_status():
    return scrna_status()


# ========== Static Files ==========

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
# Mount sub-directories first so they take priority over root
css_dir = FRONTEND_DIR / "css"
js_dir = FRONTEND_DIR / "js"
if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
