import numpy as np
import pytest

from cumcm_py.fit import fit_candidates


def test_fit_candidates_recovers_linear_relation() -> None:
    x = np.arange(6.0)
    y = 2.0 * x + 1.0
    result = fit_candidates(x, y, candidates=["linear", "quadratic"])
    assert result.values["best_model"] == "linear"
    assert np.allclose(result.values["predictions"], y)
    assert result.diagnostics["rmse"] < 1e-10


def test_fit_candidates_rejects_nan() -> None:
    with pytest.raises(ValueError, match="finite"):
        fit_candidates([0, 1], [1, np.nan])

