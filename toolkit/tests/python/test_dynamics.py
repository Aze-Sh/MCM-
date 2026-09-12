import numpy as np
import pytest

from cumcm_py.dynamics import solve_ode


def test_solve_ode_matches_exponential_decay() -> None:
    result = solve_ode(lambda _t, y: -y, (0.0, 1.0), [1.0], t_eval=[0.0, 1.0])
    assert result.diagnostics["success"]
    assert np.isclose(result.values["y"][0][-1], np.exp(-1), rtol=1e-5)


def test_solve_ode_rejects_reversed_interval() -> None:
    with pytest.raises(ValueError, match="increasing"):
        solve_ode(lambda _t, y: y, (1.0, 0.0), [1.0])

