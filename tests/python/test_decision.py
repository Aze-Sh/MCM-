import numpy as np
import pytest

from cumcm_py.decision import entropy_topsis


def test_topsis_prefers_strictly_dominant_alternative() -> None:
    matrix = np.array([[9.0, 2.0], [5.0, 5.0], [2.0, 9.0]])
    result = entropy_topsis(matrix, benefit=np.array([True, False]))
    assert result.values["ranking"][0] == 0
    assert np.isclose(sum(result.values["weights"]), 1.0)


def test_topsis_rejects_constant_column_for_entropy_weights() -> None:
    with pytest.raises(ValueError, match="constant"):
        entropy_topsis([[1, 2], [1, 3]], benefit=[True, True])

