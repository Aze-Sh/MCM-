"""Safely initialize a CUMCM contest project from repository templates."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import shutil

from cumcm_py.types import CheckReport, ValidationIssue


SUPPORTED = {"python", "matlab"}


def _copy_tree_without_overwrite(
    source: Path, destination: Path, issues: list[ValidationIssue], created: list[str]
) -> None:
    for source_path in sorted(source.rglob("*")):
        relative = source_path.relative_to(source)
        if any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts) or source_path.suffix.lower() in {".pdf", ".aux", ".log", ".out", ".toc", ".pyc", ".gz"}:
            continue
        target = destination / relative
        if source_path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            issues.append(
                ValidationIssue(
                    code="init.skipped_existing",
                    severity="warning",
                    message="existing file preserved",
                    path=str(target),
                )
            )
            continue
        shutil.copy2(source_path, target)
        created.append(str(target))


def initialize_project(
    destination: Path, languages: Sequence[str], *, force: bool = False
) -> CheckReport:
    """Create a project, refusing nonempty destinations unless force is explicit."""

    destination = destination.resolve()
    selected = [language.lower() for language in languages]
    unknown = sorted(set(selected) - SUPPORTED)
    if unknown or not selected:
        return CheckReport(
            checker="project-initializer",
            passed=False,
            issues=(
                ValidationIssue(
                    code="init.invalid_language",
                    severity="error",
                    message=f"unsupported or empty language selection: {unknown}",
                ),
            ),
            metadata={"created": []},
        )
    if destination.exists() and any(destination.iterdir()) and not force:
        return CheckReport(
            checker="project-initializer",
            passed=False,
            issues=(
                ValidationIssue(
                    code="init.nonempty_destination",
                    severity="error",
                    message="destination is nonempty; use force to add only missing files",
                    path=str(destination),
                ),
            ),
            metadata={"created": []},
        )
    template_root = Path(__file__).resolve().parents[1] / "templates" / "project"
    issues: list[ValidationIssue] = []
    created: list[str] = []
    destination.mkdir(parents=True, exist_ok=True)
    _copy_tree_without_overwrite(template_root / "shared", destination, issues, created)
    for language in dict.fromkeys(selected):
        _copy_tree_without_overwrite(
            template_root / language, destination / language, issues, created
        )
    repo_root = template_root.parents[1]
    _copy_tree_without_overwrite(repo_root / "templates" / "paper", destination / "paper", issues, created)
    _copy_tree_without_overwrite(repo_root / "templates" / "figures", destination / "figure-styles", issues, created)
    _copy_tree_without_overwrite(repo_root / "templates" / "ai-usage", destination, issues, created)
    return CheckReport(
        checker="project-initializer",
        passed=True,
        issues=tuple(issues),
        metadata={"created": created, "languages": list(dict.fromkeys(selected))},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--languages", nargs="+", default=["python"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = initialize_project(args.destination, args.languages, force=args.force)
    for issue in report.issues:
        print(f"{issue.severity}: {issue.code}: {issue.message}: {issue.path or ''}")
    print(f"created {len(report.metadata['created'])} files")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
