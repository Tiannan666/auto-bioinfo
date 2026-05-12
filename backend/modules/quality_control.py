"""Quality control checks for expression data."""

import numpy as np
import pandas as pd
from typing import Dict, List


def run_qc(matrix: pd.DataFrame, metadata: pd.DataFrame = None, groups: Dict[str, List[str]] = None) -> Dict:
    """Run all QC checks on expression data."""
    checks = []
    numeric_cols = matrix.select_dtypes(include=[np.number]).columns

    # 1. Sample name check
    if metadata is not None:
        meta_samples = set(metadata.iloc[:, 0].astype(str))
        expr_samples = set(numeric_cols)
        missing_in_expr = meta_samples - expr_samples
        missing_in_meta = expr_samples - meta_samples
        if not missing_in_expr and not missing_in_meta:
            checks.append({"name": "Sample Name Matching", "status": "pass",
                          "message": "All samples match between expression and metadata",
                          "detail": f"{len(expr_samples)} samples matched"})
        else:
            checks.append({"name": "Sample Name Matching", "status": "warn",
                          "message": f"Mismatch: {len(missing_in_expr)} in metadata only, {len(missing_in_meta)} in expression only",
                          "detail": f"Missing in expr: {list(missing_in_expr)[:5]}..." if missing_in_expr else ""})
    else:
        checks.append({"name": "Sample Name Matching", "status": "warn",
                       "message": "No metadata provided, skipped sample matching", "detail": ""})

    # 2. Missing values
    missing = matrix[numeric_cols].isnull().sum().sum()
    total = matrix[numeric_cols].size
    pct = missing / total * 100 if total > 0 else 0
    status = "pass" if pct < 1 else ("warn" if pct < 5 else "error")
    checks.append({"name": "Missing Values", "status": status,
                   "message": f"{missing} missing values ({pct:.1f}%)",
                   "detail": "Consider imputation or filtering" if pct > 1 else "Acceptable"})

    # 3. Duplicate genes
    if matrix.index.duplicated().any():
        n_dupes = matrix.index.duplicated().sum()
        checks.append({"name": "Duplicate Gene Names", "status": "warn",
                       "message": f"{n_dupes} duplicate gene names found", "detail": "Consider aggregating duplicates"})
    else:
        checks.append({"name": "Duplicate Gene Names", "status": "pass",
                       "message": "No duplicate gene names", "detail": ""})

    # 4. Non-numeric data
    non_numeric = 0
    for c in numeric_cols:
        non_numeric += pd.to_numeric(matrix[c], errors='coerce').isnull().sum() - matrix[c].isnull().sum()
    if non_numeric > 0:
        checks.append({"name": "Non-Numeric Values", "status": "error",
                       "message": f"{non_numeric} non-numeric values in expression data", "detail": "Check input format"})
    else:
        checks.append({"name": "Non-Numeric Values", "status": "pass",
                       "message": "All expression values are numeric", "detail": ""})

    # 5. Outliers (IQR method)
    vals = matrix[numeric_cols].values.flatten()
    vals = vals[~np.isnan(vals)]
    if len(vals) > 0:
        q1, q3 = np.percentile(vals, [25, 75])
        iqr = q3 - q1
        outliers = np.sum((vals < q1 - 1.5*iqr) | (vals > q3 + 1.5*iqr))
        outlier_pct = outliers / len(vals) * 100
        status = "pass" if outlier_pct < 1 else ("warn" if outlier_pct < 5 else "error")
        checks.append({"name": "Outlier Detection", "status": status,
                       "message": f"{outliers} outlier values ({outlier_pct:.1f}%)",
                       "detail": "IQR method"})

    # 6. Log2 transform check
    if len(vals) > 0:
        mean_val = np.mean(vals)
        if mean_val > 100:
            checks.append({"name": "Log2 Transform Need", "status": "info",
                          "message": f"Mean expression = {mean_val:.0f}, log2 transformation recommended",
                          "detail": "Enable log2 in differential analysis params"})
        elif mean_val < 0:
            checks.append({"name": "Log2 Transform Need", "status": "info",
                          "message": "Data appears already log-transformed", "detail": "No further log2 needed"})
        else:
            checks.append({"name": "Log2 Transform Need", "status": "pass",
                          "message": f"Mean expression = {mean_val:.1f}", "detail": "Transform optional"})

    # 7. Group balance
    if groups:
        sizes = [len(v) for v in groups.values()]
        if len(sizes) >= 2:
            min_s, max_s = min(sizes), max(sizes)
            if min_s < 3:
                checks.append({"name": "Group Size", "status": "error",
                               "message": f"Group has only {min_s} samples. Minimum 3 recommended.", "detail": str(groups)})
            elif max_s / min_s > 3:
                checks.append({"name": "Group Balance", "status": "warn",
                               "message": f"Unbalanced: {min_s} vs {max_s} samples", "detail": "May affect statistical power"})
            else:
                checks.append({"name": "Group Balance", "status": "pass",
                               "message": f"Balanced: {min_s}-{max_s} samples per group", "detail": str(groups)})
    else:
        checks.append({"name": "Group Balance", "status": "warn",
                       "message": "No group info available", "detail": "Please provide metadata"})

    passed = sum(1 for c in checks if c["status"] == "pass")
    warnings_list = [c["message"] for c in checks if c["status"] == "warn"]

    return {
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "warnings": warnings_list,
        "ready": all(c["status"] in ("pass", "info") for c in checks),
    }
