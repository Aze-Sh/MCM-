"""Reproducible Monte Carlo summaries."""

from collections.abc import Callable

import numpy as np

from .types import ModelResult


def monte_carlo(
    simulator: Callable[[np.random.Generator], float], n: int, seed: int = 0
) -> ModelResult:
    """Run independent scalar replications and return a normal CI summary."""

    if n < 2:
        raise ValueError("n must be at least 2")
    rng = np.random.default_rng(seed)
    samples = np.asarray([simulator(rng) for _ in range(n)], dtype=float)
    if samples.ndim != 1 or not np.isfinite(samples).all():
        raise ValueError("simulator must return one finite scalar per replication")
    mean = float(np.mean(samples))
    standard_error = float(np.std(samples, ddof=1) / np.sqrt(n))
    ci = [mean - 1.96 * standard_error, mean + 1.96 * standard_error]
    return ModelResult(
        method="monte-carlo-des",
        values={"mean": mean, "ci95": ci, "samples": samples.tolist()},
        diagnostics={"n": int(n), "seed": int(seed), "standard_error": standard_error},
        assumptions=("Replications are independent under the supplied simulator.",),
    )

