"""Finite-difference local sensitivity reports."""

from collections.abc import Callable, Mapping

import numpy as np

from .types import ModelResult


def sensitivity_report(
    model: Callable[[Mapping[str, float]], float],
    parameters: Mapping[str, float],
    *,
    relative_step: float = 1e-4,
) -> ModelResult:
    """Estimate central local derivatives without mutating the input mapping."""

    if not 0 < relative_step < 1:
        raise ValueError("relative_step must be between zero and one")
    base = {str(key): float(value) for key, value in parameters.items()}
    if not base or not np.isfinite(list(base.values())).all():
        raise ValueError("parameters must be a nonempty finite mapping")
    derivatives: dict[str, float] = {}
    steps: dict[str, float] = {}
    for key, value in base.items():
        step = relative_step * max(1.0, abs(value))
        upper = dict(base)
        lower = dict(base)
        upper[key] = value + step
        lower[key] = value - step
        derivatives[key] = (float(model(upper)) - float(model(lower))) / (2.0 * step)
        steps[key] = step
    return ModelResult(
        method="sensitivity-robustness",
        values={"baseline": float(model(base)), "derivatives": derivatives},
        diagnostics={"relative_step": relative_step, "absolute_steps": steps, "scheme": "central"},
        assumptions=("The model is locally smooth around the baseline parameters.",),
    )

