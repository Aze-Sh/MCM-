import numpy as np

from cumcm_py.optimization import solve_linear_program


def test_linear_program_returns_feasible_optimum() -> None:
    result = solve_linear_program(
        [-1.0, -1.0], A_ub=[[1.0, 2.0]], b_ub=[4.0], bounds=[(0, None), (0, None)]
    )
    assert result.diagnostics["success"]
    assert result.diagnostics["max_constraint_violation"] <= 1e-9
    assert np.isclose(result.values["objective"], -4.0)


def test_linear_program_reports_infeasible_without_fake_solution() -> None:
    result = solve_linear_program([1.0], A_ub=[[1.0], [-1.0]], b_ub=[0.0, -1.0])
    assert not result.diagnostics["success"]
    assert result.values["solution"] is None

