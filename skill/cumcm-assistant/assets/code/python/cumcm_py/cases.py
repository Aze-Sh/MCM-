"""Problem-card loading and provenance checks."""

from pathlib import Path
from typing import Any, Mapping

from .content import load_yaml
from .types import ValidationIssue


def load_problem_card(path: Path) -> Mapping[str, Any]:
    """Load one problem card and reject non-mapping documents."""

    card = load_yaml(path)
    if not isinstance(card, Mapping):
        raise TypeError(f"problem card must be a mapping: {path}")
    return card


def validate_evidence_links(
    card: Mapping[str, Any], catalog: Mapping[str, Any]
) -> tuple[ValidationIssue, ...]:
    """Validate source IDs and conservative award-causality rules."""

    known = {
        source.get("id")
        for source in catalog.get("sources", [])
        if isinstance(source, Mapping)
    }
    issues: list[ValidationIssue] = []
    for index, evidence in enumerate(card.get("evidence", [])):
        source_ids = tuple(evidence.get("source_ids", ()))
        for source_id in source_ids:
            if source_id not in known:
                issues.append(
                    ValidationIssue(
                        code="evidence.unknown-source",
                        severity="error",
                        message=f"unknown source ID: {source_id}",
                        path=f"evidence.{index}.source_ids",
                    )
                )
        claim = str(evidence.get("claim", ""))
        if evidence.get("kind") != "official" and any(
            phrase in claim for phrase in ("因此获奖", "获奖是因为", "评委因此")
        ):
            issues.append(
                ValidationIssue(
                    code="evidence.unsupported-causality",
                    severity="error",
                    message="causal award language requires official evidence",
                    path=f"evidence.{index}.claim",
                )
            )
        if evidence.get("kind") == "inference":
            has_criterion = "OFF-CUMCM-NATIONAL-JUDGING" in source_ids
            has_observation = any("PAPER" in source_id for source_id in source_ids)
            if not (has_criterion and has_observation):
                issues.append(
                    ValidationIssue(
                        code="evidence.inference-basis",
                        severity="error",
                        message="inference needs an official criterion and paper observation",
                        path=f"evidence.{index}.source_ids",
                    )
                )
    return tuple(issues)
