import numpy as np
import pandas as pd

from cumcm_py.preprocess import audit_dataframe


def test_audit_dataframe_reports_quality_without_mutating() -> None:
    frame = pd.DataFrame({"id": [1, 1, 3], "x": [1.0, np.nan, np.inf]})
    original = frame.copy(deep=True)
    result = audit_dataframe(frame, contract={"key": ["id"]})
    assert result.values["missing"]["x"] == 1
    assert result.values["nonfinite"]["x"] == 1
    assert result.values["duplicate_key_rows"] == 2
    pd.testing.assert_frame_equal(frame, original)


def test_audit_dataframe_rejects_non_dataframe() -> None:
    import pytest

    with pytest.raises(TypeError):
        audit_dataframe([[1, 2]])

