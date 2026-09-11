"""ODE solver wrapper with stable result structure."""

from collections.abc import Callable, Sequence

import numpy as np
from scipy.integrate import solve_ivp

from .types import ModelResult


def solve_ode(
    rhs: Callable[[float, np.ndarray], Sequence[float]],
    t_span: tuple[float, float],
    y0: Sequence[float],
    **options,
) -> ModelResult:
    """Solve an initial-value ODE after validating the time direction."""

    if len(t_span) != 2 or not t_span[1] > t_span[0]:
        raise ValueError("t_span must be strictly increasing")
    initial = np.asarray(y0, dtype=float)
    if initial.ndim != 1 or initial.size == 0 or not np.isfinite(initial).all():
        raise ValueError("y0 must be a nonempty finite vector")
    options.setdefault("rtol", 1e-8)
    options.setdefault("atol", 1e-10)
    result = solve_ivp(rhs, t_span, initial, **options)
    return ModelResult(
        method="ode-difference",
        values={"t": result.t.tolist(), "y": result.y.tolist()},
        diagnostics={
            "success": bool(result.success),
            "message": result.message,
            "function_evaluations": int(result.nfev),
        },
        assumptions=("The right-hand side is valid throughout the integration interval.",),
    )
