"""Leakage-resistant rolling-origin baselines."""

from collections.abc import Sequence

import numpy as np

from .types import ModelResult


def _forecast(train: np.ndarray, horizon: int, model: str) -> np.ndarray:
    if model == "naive":
        return np.repeat(train[-1], horizon)
    if model == "drift":
        slope = (train[-1] - train[0]) / (train.size - 1)
        return train[-1] + slope * np.arange(1, horizon + 1)
    raise ValueError(f"unknown forecast model: {model}")


def forecast_backtest(
    series: Sequence[float] | np.ndarray,
    horizon: int,
    models: Sequence[str] | None = None,
) -> ModelResult:
    """Select a simple model by expanding-window rolling-origin MAE."""

    values = np.asarray(series, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("series must be a finite one-dimensional sequence")
    if horizon < 1 or values.size < max(6, 2 * horizon + 2):
        raise ValueError("insufficient series length for requested horizon")
    names = list(models or ["naive", "drift"])
    origins = range(max(3, horizon + 1), values.size - horizon + 1)
    errors: dict[str, list[float]] = {name: [] for name in names}
    for origin in origins:
        train = values[:origin]
        actual = values[origin : origin + horizon]
        for name in names:
            errors[name].append(float(np.mean(np.abs(actual - _forecast(train, horizon, name)))))
    mean_errors = {name: float(np.mean(items)) for name, items in errors.items()}
    best = min(names, key=lambda name: (mean_errors[name], names.index(name)))
    forecast = _forecast(values, horizon, best)
    return ModelResult(
        method="time-series",
        values={"best_model": best, "forecast": forecast.tolist(), "mae": mean_errors},
        diagnostics={"origin_count": len(errors[best]), "leakage_safe": True},
        assumptions=("The selected recent trend persists over the forecast horizon.",),
    )

