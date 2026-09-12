"""Transparent multi-criteria decision helpers."""

from collections.abc import Sequence

import numpy as np

from .types import ModelResult


def entropy_topsis(
    matrix: Sequence[Sequence[float]] | np.ndarray,
    benefit: Sequence[bool] | np.ndarray,
    weights: Sequence[float] | np.ndarray | None = None,
) -> ModelResult:
    """Rank alternatives with min-max orientation and entropy/declared weights."""

    data = np.asarray(matrix, dtype=float)
    directions = np.asarray(benefit, dtype=bool)
    if data.ndim != 2 or data.shape[0] < 2 or data.shape[1] < 1:
        raise ValueError("matrix must contain at least two alternatives")
    if directions.shape != (data.shape[1],) or not np.isfinite(data).all():
        raise ValueError("benefit shape must match finite matrix columns")
    spans = np.ptp(data, axis=0)
    if np.any(spans == 0):
        raise ValueError("constant criterion columns are not informative")
    normalized = (data - np.min(data, axis=0)) / spans
    normalized[:, ~directions] = 1.0 - normalized[:, ~directions]
    if weights is None:
        column_sums = np.sum(normalized, axis=0)
        probabilities = np.divide(
            normalized,
            column_sums,
            out=np.full_like(normalized, 1.0 / data.shape[0]),
            where=column_sums > 0,
        )
        logs = np.zeros_like(probabilities)
        positive = probabilities > 0
        logs[positive] = np.log(probabilities[positive])
        entropy = -np.sum(probabilities * logs, axis=0) / np.log(data.shape[0])
        divergence = 1.0 - entropy
        if np.allclose(np.sum(divergence), 0):
            weight_array = np.repeat(1.0 / data.shape[1], data.shape[1])
        else:
            weight_array = divergence / np.sum(divergence)
    else:
        weight_array = np.asarray(weights, dtype=float)
        if weight_array.shape != (data.shape[1],) or np.any(weight_array < 0) or not np.isfinite(weight_array).all():
            raise ValueError("weights must be finite, nonnegative, and match criteria")
        if np.sum(weight_array) <= 0:
            raise ValueError("weights must have positive sum")
        weight_array = weight_array / np.sum(weight_array)
    weighted = normalized * weight_array
    ideal = np.max(weighted, axis=0)
    anti = np.min(weighted, axis=0)
    d_pos = np.linalg.norm(weighted - ideal, axis=1)
    d_neg = np.linalg.norm(weighted - anti, axis=1)
    score = np.divide(d_neg, d_pos + d_neg, out=np.zeros_like(d_neg), where=(d_pos + d_neg) > 0)
    ranking = np.argsort(-score, kind="stable")
    return ModelResult(
        method="ahp-entropy-topsis",
        values={"weights": weight_array.tolist(), "scores": score.tolist(), "ranking": ranking.tolist()},
        diagnostics={"weight_source": "entropy" if weights is None else "provided", "criterion_count": data.shape[1]},
        assumptions=("Criteria are compensatory after explicit orientation.",),
    )
