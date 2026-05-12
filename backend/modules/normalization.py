"""Expression data normalization methods."""

import numpy as np
import pandas as pd


def log2_transform(data: pd.DataFrame, offset: float = 1.0) -> pd.DataFrame:
    """Apply log2(x + offset) transformation."""
    numeric = data.select_dtypes(include=[np.number])
    data[numeric.columns] = np.log2(numeric.clip(lower=0) + offset)
    return data


def cpm_normalize(data: pd.DataFrame) -> pd.DataFrame:
    """Counts Per Million normalization."""
    numeric = data.select_dtypes(include=[np.number])
    lib_sizes = numeric.sum(axis=0)
    lib_sizes = lib_sizes.replace(0, 1)
    data[numeric.columns] = numeric.div(lib_sizes, axis=1) * 1e6
    return data


def quantile_normalize(data: pd.DataFrame) -> pd.DataFrame:
    """Quantile normalization across samples."""
    numeric = data.select_dtypes(include=[np.number])
    ranked = numeric.rank(axis=0, method='average')
    sorted_data = pd.DataFrame(np.sort(numeric.values, axis=0), index=numeric.index)
    row_means = sorted_data.mean(axis=1)
    result = pd.DataFrame(index=numeric.index, columns=numeric.columns)
    for i in range(len(numeric.columns)):
        result.iloc[:, i] = row_means[ranked.iloc[:, i].astype(int) - 1].values
    data[result.columns] = result
    return data


def filter_low_expression(data: pd.DataFrame, min_count: float = 10, min_samples: int = 3) -> pd.DataFrame:
    """Filter genes with low expression."""
    numeric = data.select_dtypes(include=[np.number])
    keep = (numeric >= min_count).sum(axis=1) >= min_samples
    return data.loc[keep]


def zscore_normalize(data: pd.DataFrame) -> pd.DataFrame:
    """Z-score normalization (for heatmap visualization)."""
    numeric = data.select_dtypes(include=[np.number])
    means = numeric.mean(axis=1)
    stds = numeric.std(axis=1).replace(0, 1)
    data[numeric.columns] = numeric.sub(means, axis=0).div(stds, axis=0)
    return data
