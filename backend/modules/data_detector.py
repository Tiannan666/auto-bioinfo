"""Auto-detection of data type from file path or GEO accession."""

import os
import re
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np

from .data_loader import load_file


def detect_data(path: str) -> Dict:
    """Detect data type and structure from a file path or GEO ID."""
    # Check for GEO accession
    geo_match = re.match(r'^GSE\d+$', path.strip(), re.IGNORECASE)
    if geo_match:
        return {
            "data_type": "GEO Series",
            "accession": path.strip().upper(),
            "n_samples": "N/A (remote)",
            "n_genes": "N/A (remote)",
            "n_groups": "N/A (remote)",
            "file_type": "GEO",
            "groups": [],
            "sample_list": ["GEO data requires download. Please use local files for full analysis."],
            "issues": [{"level": "warn", "message": "GEO access requires internet and may be slow. Consider downloading data locally."}],
        }

    path = Path(path)

    # Directory detection
    if path.is_dir():
        return _detect_directory(path)

    # Single file detection
    if path.is_file():
        return _detect_file(path)

    return {"error": f"Path not found: {path}", "data_type": "unknown"}


def _detect_file(path: Path) -> Dict:
    """Detect a single file's type."""
    try:
        df = load_file(str(path))
    except Exception as e:
        return {"error": str(e), "data_type": "unknown"}

    result = {
        "file_type": path.suffix.upper().lstrip('.'),
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "sample_list": df.columns[:10].tolist(),
    }

    # Detect if it's an expression matrix
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    object_cols = df.select_dtypes(include=['object']).columns

    if len(numeric_cols) >= 3 and len(object_cols) <= 2:
        # Likely expression matrix
        gene_col = None
        for c in object_cols:
            if df[c].nunique() > len(df) * 0.5:  # High uniqueness = gene IDs
                gene_col = c
                break

        result["data_type"] = "Expression Matrix"
        result["n_samples"] = len(numeric_cols)
        result["gene_column"] = gene_col or "index"
        result["n_genes"] = df[gene_col].nunique() if gene_col else len(df)

        # Guess value type
        vals = df[numeric_cols].values.flatten()
        vals = vals[~np.isnan(vals)]
        if len(vals) > 0:
            if np.mean(vals) < 50:
                result["value_type"] = "Counts (likely)"
            elif np.mean(vals) < 500:
                result["value_type"] = "TPM/FPKM (likely)"
            else:
                result["value_type"] = "Normalized expression"

        # Detect groups from column names
        result["groups"] = _detect_groups_from_samples(df.columns.tolist())
        result["n_groups"] = len(result["groups"])
        result["issues"] = _check_issues(df, numeric_cols, result)
    elif "logFC" in df.columns or "log2FoldChange" in df.columns or "PValue" in df.columns or "pvalue" in df.columns or "padj" in df.columns:
        result["data_type"] = "Differential Gene Results"
        result["n_genes"] = len(df)
        result["issues"] = []
    elif "GO" in str(df.columns) or "Term" in str(df.columns) or "Ontology" in str(df.columns):
        result["data_type"] = "Enrichment Results"
        result["issues"] = []
    else:
        result["data_type"] = "Unknown table"
        result["n_samples"] = len(numeric_cols)
        result["n_genes"] = len(df)
        result["groups"] = []
        result["n_groups"] = 0
        result["issues"] = [{"level": "warn", "message": "Could not determine data type. Please verify file format."}]

    return result


def _detect_directory(path: Path) -> Dict:
    """Detect data in a directory."""
    files = list(path.glob('*'))
    csv_files = [f for f in files if f.suffix.lower() in ('.csv', '.tsv', '.txt')]
    xlsx_files = [f for f in files if f.suffix.lower() in ('.xlsx', '.xls')]

    result = {
        "data_type": "Directory",
        "file_count": len(csv_files) + len(xlsx_files),
        "files": [f.name for f in csv_files + xlsx_files][:20],
        "issues": [],
    }

    # Look for expression matrix
    expr_candidates = [f for f in csv_files + xlsx_files
                       if any(kw in f.name.lower() for kw in ['expr', 'count', 'tpm', 'fpkm', 'rpkm', 'matrix'])]
    meta_candidates = [f for f in csv_files + xlsx_files
                       if any(kw in f.name.lower() for kw in ['meta', 'group', 'sample', 'design', 'pheno'])]
    diff_candidates = [f for f in csv_files + xlsx_files
                       if any(kw in f.name.lower() for kw in ['diff', 'deg', 'de gene', 'result'])]

    if expr_candidates:
        result["expression_files"] = [f.name for f in expr_candidates]
    if meta_candidates:
        result["metadata_files"] = [f.name for f in meta_candidates]
    if diff_candidates:
        result["diff_files"] = [f.name for f in diff_candidates]

    if not expr_candidates and csv_files:
        result["issues"].append({"level": "warn", "message": "No expression matrix file found. Looking for files with 'expr', 'count', 'tpm' in name."})

    if not meta_candidates:
        result["issues"].append({"level": "warn", "message": "No metadata file found. Group information will be guessed from sample names."})

    return result


def _detect_groups_from_samples(samples: List[str]) -> List[str]:
    """Try to detect group names from sample column prefixes."""
    groups = set()
    for s in samples[:20]:
        # Try splitting on common delimiters
        for sep in ['_', '-', '.']:
            parts = s.split(sep)
            if len(parts) >= 2:
                # Take the first part as potential group
                candidate = parts[0]
                if not candidate.isdigit() and len(candidate) >= 2:
                    groups.add(candidate)
    return sorted(groups) if groups else ["Group1", "Group2"]


def _check_issues(df: pd.DataFrame, numeric_cols, result: Dict) -> List[Dict]:
    """Check for common data issues."""
    issues = []
    # Missing values
    missing = df[numeric_cols].isnull().sum().sum()
    if missing > 0:
        issues.append({"level": "warn" if missing < len(df)*0.1 else "error",
                       "message": f"Missing values detected: {missing} NA values"})

    # Duplicate genes
    gene_col = result.get("gene_column")
    if gene_col and gene_col in df.columns:
        dupes = df[gene_col].duplicated().sum()
        if dupes > 0:
            issues.append({"level": "warn", "message": f"Duplicate gene names: {dupes} duplicates found"})

    # Non-numeric data in numeric columns
    non_num = 0
    for c in numeric_cols:
        non_num += pd.to_numeric(df[c], errors='coerce').isnull().sum()
    if non_num > 0:
        issues.append({"level": "error", "message": f"Non-numeric values in expression columns: {non_num} values"})

    # Check if log2 transformation is needed
    vals = df[numeric_cols].values.flatten()
    vals = vals[~np.isnan(vals)]
    if len(vals) > 0 and np.mean(vals) > 100:
        issues.append({"level": "info", "message": "Data range suggests log2 transformation may be beneficial"})

    # Group balance
    groups = result.get("groups", [])
    if len(groups) < 2:
        issues.append({"level": "warn", "message": "Fewer than 2 groups detected. Differential analysis requires at least 2 groups."})
    elif len(groups) > 5:
        issues.append({"level": "info", "message": f"{len(groups)} groups detected. Consider specifying comparison pairs."})

    return issues
