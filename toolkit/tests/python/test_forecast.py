import numpy as np
import pytest

from cumcm_py.forecast import forecast_backtest


def test_forecast_backtest_beats_bad_zero_baseline_on_trend() -> None:
    series = np.arange(1.0, 21.0)
    result = forecast_backtest(series, horizon=2, models=["naive", "drift"])
    assert result.values["best_model"] == "drift"
    assert len(result.values["forecast"]) == 2
    assert result.diagnostics["origin_count"] >= 2


def test_forecast_backtest_rejects_short_series() -> None:
    with pytest.raises(ValueError, match="insufficient"):
        forecast_backtest([1.0, 2.0, 3.0], horizon=2)

