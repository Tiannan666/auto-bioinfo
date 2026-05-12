"""scRNA-seq module placeholder — API structure for future implementation."""

from typing import Dict


def scrna_status() -> Dict:
    return {
        "module": "scRNA-seq",
        "status": "coming_soon",
        "planned_features": [
            "10x Genomics data import (mtx, h5, h5ad)",
            "Quality control (n_genes, n_counts, pct_mito)",
            "Normalization (LogNormalize, SCTransform-like)",
            "Highly variable gene selection",
            "Dimensionality reduction (PCA, UMAP, t-SNE)",
            "Cell clustering (Leiden, Louvain)",
            "Cell type annotation (marker-based, reference-based)",
            "Marker gene analysis (Wilcoxon, t-test, logFC)",
            "DotPlot, FeaturePlot, ViolinPlot, StackedViolin",
            "Cell proportion analysis across conditions",
            "Gene set scoring (AUCell, ssGSEA, AddModuleScore)",
            "Pseudotime trajectory analysis (Diffusion Map, Slingshot-like)",
            "Cell-cell communication (CellChat, CellPhoneDB-like)",
            "Sub-clustering and re-analysis",
            "Multi-sample/batch integration (Harmony, CCA, MNN)",
        ],
        "input_formats": [
            "10x Genomics (matrix.mtx + barcodes.tsv + features.tsv)",
            "HDF5 (.h5)",
            "AnnData (.h5ad)",
            "Loom (.loom)",
            "Seurat object (.rds, via rpy2)",
        ],
        "api_preview": {
            "scrna_load": "POST /api/v2/scrna/load",
            "scrna_qc": "POST /api/v2/scrna/qc",
            "scrna_normalize": "POST /api/v2/scrna/normalize",
            "scrna_cluster": "POST /api/v2/scrna/cluster",
            "scrna_annotate": "POST /api/v2/scrna/annotate",
            "scrna_markers": "POST /api/v2/scrna/markers",
            "scrna_plots": "POST /api/v2/scrna/plots",
            "scrna_trajectory": "POST /api/v2/scrna/trajectory",
            "scrna_communication": "POST /api/v2/scrna/communication",
        },
    }
