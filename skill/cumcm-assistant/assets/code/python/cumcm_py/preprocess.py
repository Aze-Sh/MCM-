"""Non-mutating data-quality audits."""

from typing import Any, Mapping

import numpy as np
import pandas as pd

from .types import ModelResult


def audit_dataframe(
    df: pd.DataFrame, contract: Mapping[str, Any] | None = None
) -> ModelResult:
    """Audit a DataFrame without silently cleaning or imputing it."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    contract = dict(contract or {})
    missing = {str(column): int(df[column].isna().sum()) for column in df}
    nonfinite: dict[str, int] = {}
    for column in df:
        if pd.api.types.is_numeric_dtype(df[column]):
            values = df[column].to_numpy(dtype=float, na_value=np.nan)
            nonfinite[str(column)] = int(np.isinf(values).sum())
    key = list(contract.get("key", []))
    absent = [column for column in key if column not in df.columns]
    if absent:
        raise ValueError(f"contract key columns missing: {absent}")
    duplicate_rows = int(df.duplicated(subset=key, keep=False).sum()) if key else 0
    return ModelResult(
        method="data-audit",
        values={
            "rows": int(len(df)),
            "columns": [str(column) for column in df.columns],
            "missing": missing,
            "nonfinite": nonfinite,
            "duplicate_key_rows": duplicate_rows,
        },
        diagnostics={"mutated": False, "contract_checked": bool(contract)},
        assumptions=("Missing, zero, and non-finite values have distinct meanings.",),
    )

