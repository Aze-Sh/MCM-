import numpy as np

from cumcm_py.simulation import monte_carlo


def test_monte_carlo_is_seed_reproducible() -> None:
    def simulator(rng):
        return rng.normal()

    one = monte_carlo(simulator, 1000, seed=7)
    two = monte_carlo(simulator, 1000, seed=7)
    assert one.values["mean"] == two.values["mean"]
    assert one.values["samples"] == two.values["samples"]
    assert np.isfinite(one.values["ci95"]).all()

