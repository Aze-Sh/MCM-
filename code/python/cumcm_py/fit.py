"""Small, explicit candidate fitting helpers."""

from collections.abc import Sequence

import numpy as np

from .types import ModelResult


def fit_candidates(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    candidates: Sequence[str] | None = None,
) -> ModelResult:
    """Fit linear/quadratic polynomial candidates and select parsimoniously."""

    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if x_array.ndim == 1:
        x_array = x_array[:, None]
    if y_array.ndim != 1 or x_array.shape[0] != y_array.size:
        raise ValueError("x and y shapes are incompatible")
    if x_array.shape[1] != 1:
        raise ValueError("this compact fitter currently accepts one predictor")
    if not (np.isfinite(x_array).all() and np.isfinite(y_array).all()):
        raise ValueError("x and y must be finite")
    names = list(candidates or ["linear"])
    degrees = {"linear": 1, "quadratic": 2}
    unknown = [name for name in names if name not in degrees]
    if unknown:
        raise ValueError(f"unknown candidates: {unknown}")
    if y_array.size <= max(degrees[name] for name in names):
        raise ValueError("insufficient observations for requested candidates")
    fitted: dict[str, dict[str, object]] = {}
    for name in names:
        degree = degrees[name]
        coefficients = np.polyfit(x_array[:, 0], y_array, degree)
        predictions = np.polyval(coefficients, x_array[:, 0])
        rmse = float(np.sqrt(np.mean((y_array - predictions) ** 2)))
        fitted[name] = {
            "coefficients": coefficients.tolist(),
            "predictions": predictions,
            "rmse": rmse,
            "degree": degree,
        }
    minimum = min(float(item["rmse"]) for item in fitted.values())
    tolerance = max(1e-12, minimum * 1e-6)
    eligible = [
        (str(name), item)
        for name, item in fitted.items()
        if float(item["rmse"]) <= minimum + tolerance
    ]
    best_name, best = min(eligible, key=lambda pair: int(pair[1]["degree"]))
    return ModelResult(
        method="interpolation-fitting",
        values={
            "best_model": best_name,
            "coefficients": best["coefficients"],
            "predictions": best["predictions"],
            "candidate_rmse": {
                name: float(item["rmse"]) for name, item in fitted.items()
            },
        },
        diagnostics={"rmse": float(best["rmse"]), "n": int(y_array.size)},
        assumptions=("Candidate polynomial form is valid only inside the observed domain.",),
    )

