"""Leakage-aware small-model evaluation."""

from collections.abc import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .types import ModelResult


def evaluate_models(
    X: Sequence[Sequence[float]] | np.ndarray,
    y: Sequence[int] | np.ndarray,
    groups: Sequence[int] | np.ndarray | None = None,
    models: Sequence[str] | None = None,
    *,
    repeated_measurements: bool = False,
) -> ModelResult:
    """Cross-validate compact classification baselines inside a preprocessing pipeline."""

    features = np.asarray(X, dtype=float)
    labels = np.asarray(y)
    if features.ndim != 2 or labels.ndim != 1 or features.shape[0] != labels.size:
        raise ValueError("X and y shapes are incompatible")
    if not np.isfinite(features).all() or np.unique(labels).size < 2:
        raise ValueError("features must be finite and y must contain at least two classes")
    if repeated_measurements and groups is None:
        raise ValueError("groups are required for repeated measurements")
    names = list(models or ["logistic"])
    if names != ["logistic"] and any(name != "logistic" for name in names):
        raise ValueError("only the explicit logistic baseline is currently supported")
    group_array = None if groups is None else np.asarray(groups)
    if group_array is not None:
        if group_array.shape != (labels.size,):
            raise ValueError("groups must match observations")
        unique_groups = np.unique(group_array)
        if unique_groups.size < 2:
            raise ValueError("at least two groups are required")
        folds = min(4, unique_groups.size)
        splitter = GroupKFold(n_splits=folds)
        split_args = {"groups": group_array}
        group_disjoint = True
    else:
        minimum_class = int(np.min(np.bincount(np.unique(labels, return_inverse=True)[1])))
        folds = min(5, minimum_class)
        if folds < 2:
            raise ValueError("insufficient samples per class")
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=0)
        split_args = {}
        group_disjoint = False
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=0))
    predictions = cross_val_predict(pipeline, features, labels, cv=splitter, **split_args)
    accuracy = float(accuracy_score(labels, predictions))
    return ModelResult(
        method="ml-clustering-pca",
        values={"best_model": "logistic", "accuracy": accuracy, "predictions": predictions.tolist()},
        diagnostics={"folds": int(folds), "group_disjoint": group_disjoint, "preprocessing_inside_folds": True},
        assumptions=("Cross-validation units match independent deployment units.",),
    )

