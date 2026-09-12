"""Compare normalized Python and MATLAB result JSON files."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

from cumcm_py.types import CheckReport, ValidationIssue


def _get_path(document: Mapping[str, Any], path: str) -> Any:
    value: Any = document
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise KeyError(path)
        value = value[part]
    return value


def compare_result_files(
    python_json: Path, matlab_json: Path, manifest: Path
) -> CheckReport:
    """Compare declared properties with exact or numeric semantics."""

    python_result = json.loads(python_json.read_text(encoding="utf-8"))
    matlab_result = json.loads(matlab_json.read_text(encoding="utf-8"))
    specification = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    absolute = float(specification.get("absolute_tolerance", 0.0))
    relative = float(specification.get("relative_tolerance", 0.0))
    issues: list[ValidationIssue] = []
    properties = specification.get("properties", [])
    for item in properties:
        path = str(item["path"])
        try:
            left = _get_path(python_result, path)
            right = _get_path(matlab_result, path)
        except KeyError:
            issues.append(
                ValidationIssue(
                    code="cross.missing_property",
                    severity="error",
                    message=f"declared comparison property is missing: {path}",
                    path=path,
                )
            )
            continue
        comparison = item.get("comparison", "exact")
        if comparison == "numeric":
            try:
                equal = np.allclose(
                    np.asarray(left, dtype=float),
                    np.asarray(right, dtype=float),
                    atol=absolute,
                    rtol=relative,
                    equal_nan=False,
                )
            except (TypeError, ValueError):
                equal = False
            code = "cross.numeric_mismatch"
        else:
            equal = left == right
            code = "cross.exact_mismatch"
        if isinstance(equal, np.ndarray):
            equal = bool(np.all(equal))
        if not equal:
            issues.append(
                ValidationIssue(
                    code=code,
                    severity="error",
                    message=f"Python and MATLAB differ at {path}",
                    path=path,
                )
            )
    return CheckReport(
        checker="cross-language",
        passed=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
        metadata={
            "fixture_id": specification.get("id"),
            "compared_properties": len(properties),
            "absolute_tolerance": absolute,
            "relative_tolerance": relative,
        },
    )


def _values_equal(left: Any, right: Any, absolute: float, relative: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(
            float(left), float(right), abs_tol=absolute, rel_tol=relative
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _values_equal(left[key], right[key], absolute, relative) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _values_equal(a, b, absolute, relative) for a, b in zip(left, right)
        )
    return left == right


def compare_fixture_manifest(
    expected_dir: Path, matlab_dir: Path, manifest: Path
) -> CheckReport:
    """Compare every declared fixture property against MATLAB output."""

    specification = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    fixtures = specification.get("fixtures", [])
    issues: list[ValidationIssue] = []
    compared_properties = 0
    for fixture in fixtures:
        fixture_id = str(fixture["id"])
        expected_path = expected_dir / f"{fixture_id}.json"
        matlab_path = matlab_dir / f"{fixture_id}.json"
        if not expected_path.exists() or not matlab_path.exists():
            missing = expected_path if not expected_path.exists() else matlab_path
            issues.append(
                ValidationIssue(
                    code="cross.missing_output",
                    severity="error",
                    message=f"fixture output is missing: {fixture_id}",
                    path=str(missing),
                )
            )
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        matlab = json.loads(matlab_path.read_text(encoding="utf-8"))
        absolute = float(fixture.get("absolute_tolerance", 0.0))
        relative = float(fixture.get("relative_tolerance", 0.0))
        for property_path in fixture.get("properties", []):
            path = str(property_path)
            compared_properties += 1
            try:
                left = _get_path(expected, path)
                right = _get_path(matlab, path)
            except KeyError:
                issues.append(
                    ValidationIssue(
                        code="cross.missing_property",
                        severity="error",
                        message=f"declared comparison property is missing: {path}",
                        path=f"{fixture_id}:{path}",
                    )
                )
                continue
            if not _values_equal(left, right, absolute, relative):
                issues.append(
                    ValidationIssue(
                        code="cross.value_mismatch",
                        severity="error",
                        message=f"reference and MATLAB differ at {path}",
                        path=f"{fixture_id}:{path}",
                    )
                )
    return CheckReport(
        checker="cross-language-manifest",
        passed=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
        metadata={
            "fixture_count": len(fixtures),
            "compared_properties": compared_properties,
        },
    )


def _serialize_report(report: CheckReport) -> dict[str, Any]:
    return {
        "checker": report.checker,
        "passed": report.passed,
        "issues": [issue.__dict__ for issue in report.issues],
        "metadata": dict(report.metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-json", type=Path)
    parser.add_argument("--matlab-json", type=Path)
    parser.add_argument("--expected-dir", type=Path)
    parser.add_argument("--matlab-dir", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    direct = bool(args.python_json and args.matlab_json)
    fixture_manifest = bool(args.expected_dir and args.matlab_dir)
    if direct == fixture_manifest:
        parser.error(
            "provide either --python-json/--matlab-json or "
            "--expected-dir/--matlab-dir"
        )
    if direct:
        report = compare_result_files(args.python_json, args.matlab_json, args.manifest)
    else:
        report = compare_fixture_manifest(
            args.expected_dir, args.matlab_dir, args.manifest
        )
    payload = _serialize_report(report)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
