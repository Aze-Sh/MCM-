import numpy as np

from cumcm_py.sensitivity import sensitivity_report


def test_sensitivity_report_matches_linear_model() -> None:
    result = sensitivity_report(
        lambda p: 2.0 * p["x"] - 3.0 * p["y"],
        {"x": 1.0, "y": 2.0},
        relative_step=1e-5,
    )
    assert np.isclose(result.values["derivatives"]["x"], 2.0, rtol=1e-5)
    assert np.isclose(result.values["derivatives"]["y"], -3.0, rtol=1e-5)

