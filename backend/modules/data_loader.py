"""Data loader: reads CSV, TSV, Excel, and text files."""

import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


def load_file(path: str) -> pd.DataFrame:
    """Load a file into a pandas DataFrame. Supports CSV, TSV, TXT, XLSX."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    try:
        if suffix in ('.csv',):
            return pd.read_csv(path, index_col=None)
        elif suffix in ('.tsv', '.txt'):
            return pd.read_csv(path, sep='\t', index_col=None)
        elif suffix in ('.xlsx', '.xls'):
            return pd.read_excel(path, index_col=None)
        else:
            # Try CSV first, then TSV
            try:
                return pd.read_csv(path, index_col=None)
            except Exception:
                return pd.read_csv(path, sep='\t', index_col=None)
    except Exception as e:
        raise ValueError(f"Failed to load {path}: {e}")


def load_expression_matrix(path: str) -> Dict:
    """Load expression matrix and return structured data."""
    df = load_file(path)
    # Try to identify gene column
    gene_col = None
    for col in df.columns[:5]:
        if df[col].dtype == object and not _looks_like_sample(df[col].iloc[:3].tolist()):
            gene_col = col
            break

    if gene_col:
        df = df.set_index(gene_col)

    # Filter numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    sample_cols = [c for c in df.columns if c in numeric_cols]

    if not sample_cols:
        sample_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    return {
        "gene_ids": df.index.tolist(),
        "sample_ids": sample_cols[:30],  # first 30
        "n_genes": len(df),
        "n_samples": len(sample_cols),
        "matrix": df[sample_cols],
        "data_type": _guess_data_type(df[sample_cols]),
        "sample_ids_full": sample_cols,
    }


def load_metadata(path: str) -> pd.DataFrame:
    """Load metadata/group file."""
    df = load_file(path)
    return df


def _looks_like_sample(values: List[str]) -> bool:
    """Guess if a list of strings looks like sample names."""
    if len(values) < 2:
        return False
    # Sample names often have common prefixes or numeric suffixes
    import re
    patterns = [bool(re.search(r'\d+$', str(v))) for v in values]
    return sum(patterns) >= len(values) * 0.3


def _guess_data_type(df: pd.DataFrame) -> str:
    """Guess expression data type from value ranges."""
    v = df.values.flatten()
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return "unknown"
    mean_val = np.mean(v)
    if mean_val < 50:
        return "counts"
    elif mean_val < 500:
        return "TPM/FPKM"
    elif mean_val < 20:
        return "log2-transformed"
    return "expression_matrix"
