"""Data loader: reads CSV, TSV, Excel, GEO SOFT, MINiML, and plain text files."""

import re
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


def load_file(path: str) -> pd.DataFrame:
    """Load a file into a pandas DataFrame. Auto-detects format."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    # Gzipped files
    if suffix == '.gz':
        content = _read_raw(path)
        # Try to detect format from first bytes
        if content.startswith(b'\x1f\x8b'):
            content = gzip.decompress(content)
        text = content.decode('utf-8', errors='replace')
        return _parse_any_format(text, str(path))

    try:
        if suffix in ('.csv',):
            return pd.read_csv(path, index_col=None)
        elif suffix in ('.tsv', '.txt', '.tab'):
            return pd.read_csv(path, sep='\t', index_col=None)
        elif suffix in ('.xlsx', '.xls'):
            return pd.read_excel(path, index_col=None, engine='openpyxl')
        elif suffix in ('.soft',):
            return _parse_soft(str(path))
        elif suffix in ('.xml', '.miniml'):
            return _parse_miniml(str(path))
        else:
            return _parse_any_format(path.read_text(encoding='utf-8', errors='replace'), str(path))
    except Exception as e:
        raise ValueError(f"Failed to load {path}: {e}")


def _read_raw(path: Path) -> bytes:
    """Read raw bytes from a file (handles gzip)."""
    with open(path, 'rb') as f:
        data = f.read()
    if data[:2] == b'\x1f\x8b':
        return gzip.decompress(data)
    return data


def _parse_any_format(text: str, filename: str) -> pd.DataFrame:
    """Auto-detect and parse any supported format from raw text."""
    lower_name = filename.lower()

    # GEO SOFT format detection
    if text.startswith('^') or '.soft' in lower_name:
        return _parse_soft_text(text)

    # MINiML (XML) detection
    if text.strip().startswith('<') or '.miniml' in lower_name or '.xml' in lower_name:
        return _parse_miniml_text(text)

    # Try delimiter detection
    lines = [l for l in text.strip().split('\n') if l.strip()]
    if len(lines) >= 2:
        # Count delimiters in first few lines
        first_lines = lines[:min(5, len(lines))]
        delim_counts = {'\t': 0, ',': 0, ';': 0}
        for line in first_lines:
            for delim in delim_counts:
                delim_counts[delim] += line.count(delim)

        best_delim = max(delim_counts, key=delim_counts.get)
        if best_delim and delim_counts[best_delim] > len(first_lines):
            from io import StringIO
            return pd.read_csv(StringIO(text), sep=best_delim, index_col=None)

    raise ValueError(f"Cannot auto-detect format for: {filename}")


# ========== GEO SOFT Format Parser ==========

def _parse_soft(filepath: str) -> pd.DataFrame:
    """Parse GEO SOFT format file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    return _parse_soft_text(text)


def _parse_soft_text(text: str) -> pd.DataFrame:
    """Parse GEO SOFT format from text."""
    lines = text.strip().split('\n')

    # Find the data table section
    in_table = False
    headers = []
    rows = []
    metadata = {}

    for line in lines:
        line = line.rstrip()
        if not line:
            continue

        if line.startswith('!'):
            # Metadata line: !field = value
            parts = line[1:].split('=', 1)
            if len(parts) == 2:
                metadata[parts[0].strip()] = parts[1].strip()
            continue

        if line.startswith('#'):
            # Header line for table
            headers = [h.strip().strip('"') for h in line[1:].split('\t')]
            in_table = True
            continue

        if in_table:
            values = line.split('\t')
            if len(values) >= len(headers) * 0.5:
                rows.append(values)
            else:
                in_table = False

    if not headers or not rows:
        # Fallback: try to interpret metadata as a table
        if metadata:
            return pd.DataFrame([metadata])
        raise ValueError("No data table found in SOFT format")

    try:
        df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
        # Set the first column as gene ID if it's usually ID_REF
        if 'ID_REF' in df.columns:
            df = df.set_index('ID_REF')
        return df
    except Exception:
        raise ValueError("Failed to parse SOFT data table")


# ========== GEO MINiML (XML) Format Parser ==========

def _parse_miniml(filepath: str) -> pd.DataFrame:
    """Parse GEO MINiML XML format."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    return _parse_miniml_text(text)


def _parse_miniml_text(text: str) -> pd.DataFrame:
    """Parse MINiML XML from text."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        raise ValueError("Invalid MINiML XML")

    # Namespace handling
    ns = '{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}'

    # Look for Sample nodes with data tables
    records = []
    for sample in root.iter(f'{ns}Sample') or root.iter('Sample'):
        record = {}
        # Collect all columns
        for col in sample.iter(f'{ns}Column') or sample.iter('Column'):
            name = col.findtext(f'{ns}Name') or col.findtext('Name') or ''
            val = col.findtext(f'{ns}Value') or col.findtext('Value') or ''
            record[name] = val
        if record:
            records.append(record)

    if records:
        return pd.DataFrame(records)

    # Fallback: try simpler key-value extraction
    data = {}
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if elem.text and elem.text.strip() and tag not in ('Sample', 'Samples', 'Series', 'Platform'):
            data[tag] = elem.text.strip()

    if data:
        return pd.DataFrame([data])

    raise ValueError("No data extracted from MINiML")


# ========== Expression matrix helpers ==========

def load_expression_matrix(path: str) -> Dict:
    """Load expression matrix and return structured data."""
    df = load_file(path)

    # Try to identify gene column (non-numeric, high uniqueness)
    gene_col = None
    for col in df.columns[:10]:
        if col.lower() in ('id_ref', 'gene', 'symbol', 'gene_symbol', 'genesymbol', 'probe_id', 'probeid'):
            gene_col = col
            break

    if gene_col is None:
        for col in df.columns[:5]:
            if df[col].dtype == object and not _looks_like_sample(df[col].iloc[:3].tolist()):
                if df[col].nunique() > len(df) * 0.3:
                    gene_col = col
                    break

    if gene_col:
        df = df.set_index(gene_col)

    # Keep only numeric columns as samples
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        # Try converting all columns to numeric
        for c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            except Exception:
                pass
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        raise ValueError("No numeric expression data found in file")

    return {
        "gene_ids": df.index.tolist()[:500],
        "sample_ids": numeric_cols[:30],
        "n_genes": len(df),
        "n_samples": len(numeric_cols),
        "matrix": df[numeric_cols],
        "data_type": _guess_data_type(df[numeric_cols]),
        "sample_ids_full": numeric_cols,
    }


def load_metadata(path: str) -> pd.DataFrame:
    """Load metadata/group file."""
    return load_file(path)


def _looks_like_sample(values: List[str]) -> bool:
    """Guess if a list of strings looks like sample names."""
    if len(values) < 2:
        return False
    patterns = sum(1 for v in values if bool(re.search(r'\d+$', str(v))))
    return patterns >= len(values) * 0.3


def _guess_data_type(df: pd.DataFrame) -> str:
    """Guess expression data type from value ranges."""
    v = df.values.flatten()
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return "unknown"
    mean_val = np.mean(v)
    if mean_val < 20:
        return "log2-transformed"
    elif mean_val < 50:
        return "counts"
    elif mean_val < 500:
        return "TPM/FPKM"
    return "expression_matrix"
