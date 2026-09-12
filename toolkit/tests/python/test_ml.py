import numpy as np
import pytest

from cumcm_py.ml import evaluate_models


def test_evaluate_models_uses_group_disjoint_folds() -> None:
    X = np.array([[0], [0.1], [1], [1.1], [2], [2.1], [3], [3.1]])
    y = np.array([0, 0, 1, 1, 0, 0, 1, 1])
    groups = np.repeat(np.arange(4), 2)
    result = evaluate_models(X, y, groups=groups, models=["logistic"])
    assert result.diagnostics["group_disjoint"]
    assert result.diagnostics["folds"] >= 2


def test_evaluate_models_requires_groups_for_repeated_rows() -> None:
    X = np.array([[0], [0], [1], [1]])
    y = np.array([0, 0, 1, 1])
    with pytest.raises(ValueError, match="groups"):
        evaluate_models(X, y, repeated_measurements=True)

