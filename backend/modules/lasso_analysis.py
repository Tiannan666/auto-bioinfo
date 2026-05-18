"""LASSO regression for biomarker selection (sklearn + R glmnet)."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score


def run_lasso(expression: pd.DataFrame, group1_samples: List[str],
              group2_samples: List[str], n_features: int = 50,
              cv_folds: int = 10, seed: int = 42) -> Dict:
    """Run LASSO regression to select biomarker genes."""

    if expression.index.name != 'gene' and 'gene' in expression.columns:
        expression = expression.set_index('gene')

    expr_num = expression.select_dtypes(include=['number'])

    all_samples = group1_samples + group2_samples
    available = [s for s in all_samples if s in expr_num.columns]
    if len(available) < 10:
        raise ValueError("Need at least 10 samples for LASSO (found {})".format(len(available)))

    X = expr_num[available].T
    y = np.array([0] * len([s for s in group1_samples if s in available]) +
                 [1] * len([s for s in group2_samples if s in available]))

    # Pre-filter: top variable genes
    gene_var = X.var()
    top_genes = gene_var.nlargest(min(n_features * 20, len(gene_var))).index
    X_filtered = X[top_genes]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_filtered)

    np.random.seed(seed)
    lasso = LassoCV(cv=min(cv_folds, len(y)), random_state=seed, max_iter=10000)
    lasso.fit(X_scaled, y)

    coefs = pd.Series(lasso.coef_, index=top_genes)
    selected = coefs[coefs != 0].sort_values(key=abs, ascending=False)

    if len(selected) == 0:
        # Use minimum alpha to get some features
        from sklearn.linear_model import Lasso
        alpha_min = lasso.alphas_[-1] * 0.1
        lasso_min = Lasso(alpha=alpha_min, random_state=seed, max_iter=10000)
        lasso_min.fit(X_scaled, y)
        coefs = pd.Series(lasso_min.coef_, index=top_genes)
        selected = coefs[coefs != 0].sort_values(key=abs, ascending=False)

    selected = selected.head(n_features)

    # Cross-validation accuracy with selected features
    if len(selected) > 0:
        X_sel = X_scaled[:, [list(top_genes).index(g) for g in selected.index]]
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(random_state=seed, max_iter=1000)
        cv_scores = cross_val_score(lr, X_sel, y, cv=min(5, len(y)), scoring='accuracy')
        accuracy = float(cv_scores.mean())
        auc_scores = cross_val_score(lr, X_sel, y, cv=min(5, len(y)), scoring='roc_auc')
        auc = float(auc_scores.mean())
    else:
        accuracy = 0.5
        auc = 0.5

    biomarkers = []
    for gene, coef in selected.items():
        biomarkers.append({
            'gene': gene,
            'coefficient': float(coef),
            'direction': 'up' if coef > 0 else 'down',
        })

    return {
        'type': 'lasso',
        'n_samples': len(available),
        'n_genes_input': len(top_genes),
        'n_selected': len(selected),
        'alpha': float(lasso.alpha_),
        'cv_accuracy': accuracy,
        'cv_auc': auc,
        'biomarkers': biomarkers,
    }
