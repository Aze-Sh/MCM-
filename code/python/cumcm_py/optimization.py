"""Optimization wrappers that preserve status and feasibility evidence."""

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from scipy.optimize import linprog, minimize

from .types import ModelResult


def solve_linear_program(
    c: Sequence[float],
    A_ub: Sequence[Sequence[float]] | None = None,
    b_ub: Sequence[float] | None = None,
    bounds: Sequence[tuple[float | None, float | None]] | None = None,
    integrality: Sequence[int] | None = None,
) -> ModelResult:
    """Solve an LP/MILP using SciPy and independently recompute violations."""

    c_array = np.asarray(c, dtype=float)
    if c_array.ndim != 1 or not np.isfinite(c_array).all():
        raise ValueError("c must be a finite vector")
    A_array = None if A_ub is None else np.asarray(A_ub, dtype=float)
    b_array = None if b_ub is None else np.asarray(b_ub, dtype=float)
    if (A_array is None) != (b_array is None):
        raise ValueError("A_ub and b_ub must be provided together")
    result = linprog(
        c_array,
        A_ub=A_array,
        b_ub=b_array,
        bounds=bounds,
        integrality=integrality,
        method="highs",
    )
    if not result.success:
        return ModelResult(
            method="lp-milp",
            values={"solution": None, "objective": None},
            diagnostics={"success": False, "status": int(result.status), "message": result.message},
            assumptions=("All supplied coefficients are deterministic.",),
        )
    x = np.asarray(result.x, dtype=float)
    violation = 0.0
    if A_array is not None and b_array is not None:
        violation = max(0.0, float(np.max(A_array @ x - b_array)))
    return ModelResult(
        method="lp-milp",
        values={"solution": x.tolist(), "objective": float(c_array @ x)},
        diagnostics={
            "success": True,
            "status": int(result.status),
            "max_constraint_violation": violation,
            "message": result.message,
        },
        assumptions=("Objective direction is minimization and was not changed.",),
    )


def solve_nonlinear_problem(
    objective: Callable[[np.ndarray], float],
    x0: Sequence[float],
    *,
    bounds: Sequence[tuple[float | None, float | None]] | None = None,
    constraints: Sequence[dict[str, Any]] = (),
) -> ModelResult:
    """Minimal nonlinear wrapper with explicit local-optimum semantics."""

    result = minimize(objective, np.asarray(x0, dtype=float), bounds=bounds, constraints=constraints)
    return ModelResult(
        method="nonlinear-multiobjective",
        values={"solution": result.x.tolist() if result.success else None, "objective": float(result.fun) if result.success else None},
        diagnostics={"success": bool(result.success), "message": result.message, "local_optimum_only": True},
        assumptions=("The returned solution is local unless separately proven global.",),
    )
