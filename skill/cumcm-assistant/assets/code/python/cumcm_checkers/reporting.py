"""Shared construction and deterministic serialization of checker reports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from cumcm_py.types import CheckReport, ValidationIssue


def make_report(
    checker: str,
    issues: Iterable[ValidationIssue],
    metadata: Mapping[str, Any] | None = None,
) -> CheckReport:
    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.path or "", item.message)))
    return CheckReport(
        checker=checker,
        passed=not any(issue.severity == "error" for issue in ordered),
        issues=ordered,
        metadata=dict(metadata or {}),
    )


def issue(
    code: str,
    message: str,
    *,
    path: str | None = None,
    severity: str = "error",
    source_ids: Iterable[str] = (),
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        path=path,
        source_ids=tuple(source_ids),
    )


def aggregate_to_dict(reports: Iterable[CheckReport]) -> dict[str, Any]:
    reports = tuple(sorted(reports, key=lambda report: report.checker))
    issues = [
        {
            "checker": report.checker,
            "code": item.code,
            "severity": item.severity,
            "path": item.path,
            "message": item.message,
            "source_ids": list(item.source_ids),
        }
        for report in reports
        for item in report.issues
    ]
    issues.sort(key=lambda item: (item["checker"], item["code"], item.get("path") or ""))
    return {
        "passed": all(report.passed for report in reports),
        "checkers": [
            {
                "checker": report.checker,
                "passed": report.passed,
                "issue_count": len(report.issues),
                "metadata": dict(report.metadata),
            }
            for report in reports
        ],
        "issues": issues,
    }


def config_value(config: Mapping[str, Any], key: str, default: Any) -> Any:
    value = config.get(key, default)
    if isinstance(value, Mapping) and "value" in value:
        return value["value"]
    return value


def rule_sources(config: Mapping[str, Any], key: str | None = None) -> tuple[str, ...]:
    if key is not None and isinstance(config.get(key), Mapping):
        nested = config[key]
        if isinstance(nested, Mapping) and "source_ids" in nested:
            return tuple(nested["source_ids"])
    return tuple(config.get("source_ids", ()))
