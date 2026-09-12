"""Shared immutable result types used across the repository."""

from dataclasses import dataclass
from typing import Any, Literal, Mapping


ReadStatus = Literal[
    "full-read", "partial-read", "metadata-only", "blocked", "dead-link"
]
EvidenceKind = Literal["official", "observable", "inference"]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    path: str | None = None
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckReport:
    checker: str
    passed: bool
    issues: tuple[ValidationIssue, ...]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class ModelResult:
    method: str
    values: Mapping[str, Any]
    diagnostics: Mapping[str, Any]
    assumptions: tuple[str, ...]

