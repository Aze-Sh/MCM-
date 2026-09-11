"""Build a deterministic, self-contained cumcm-assistant Skill bundle."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import yaml

from cumcm_py.types import CheckReport, ValidationIssue


REFERENCE_FILES = {
    "knowledge/award-patterns.md": "references/award-patterns/award-patterns.md",
    "knowledge/model-selection.md": "references/award-patterns/model-selection.md",
    "workflows/writing-and-figures.md": "references/writing/writing-and-figures.md",
    "validation/paper-template.md": "references/writing/paper-template-validation.md",
    "rules/2026-rules.md": "references/compliance/2026-rules.md",
    "rules/2026-paper-format.md": "references/compliance/2026-paper-format.md",
    "rules/2026-ai-use.md": "references/compliance/2026-ai-use.md",
    "rules/submission-checklist.md": "references/compliance/submission-checklist.md",
}

DIRECTORIES = {
    "knowledge/problem-types": "references/problem-types",
    "knowledge/methods": "references/methods",
    "workflows": "references/workflows",
    "templates/paper": "assets/paper",
    "templates/figures": "assets/figures",
    "templates/project": "assets/project",
    "templates/citations": "assets/citations",
    "templates/ai-usage": "assets/ai-usage",
    "code/python/cumcm_py": "assets/code/python/cumcm_py",
    "code/python/cumcm_checkers": "assets/code/python/cumcm_checkers",
    "code/matlab/+cumcm": "assets/code/matlab/+cumcm",
    "checkers/rules": "assets/checkers/rules",
}

EXCLUDED_NAMES = {"__pycache__", "main.aux", "main.log", "main.out", "main.pdf"}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iter_files(path: Path):
    for item in sorted(path.rglob("*")):
        if item.is_file() and not any(part in EXCLUDED_NAMES for part in item.parts):
            yield item


def build_skill_bundle(repo_root: Path, skill_root: Path) -> CheckReport:
    repo_root = repo_root.resolve()
    skill_root = skill_root.resolve()
    canonical_skill = repo_root / "skill/cumcm-assistant"
    issues: list[ValidationIssue] = []
    if not canonical_skill.exists():
        missing = ValidationIssue("skill.missing_control", "error", "缺少 Skill 控制文件。", str(canonical_skill))
        return CheckReport("skill_bundle", False, (missing,), {})

    if skill_root != canonical_skill:
        if skill_root.exists():
            shutil.rmtree(skill_root)
        skill_root.mkdir(parents=True)
        shutil.copy2(canonical_skill / "SKILL.md", skill_root / "SKILL.md")
        shutil.copytree(canonical_skill / "agents", skill_root / "agents")
        shutil.copytree(canonical_skill / "scripts", skill_root / "scripts")

    for generated in (skill_root / "references", skill_root / "assets"):
        if generated.exists():
            shutil.rmtree(generated)
        generated.mkdir(parents=True)

    mappings: list[tuple[Path, Path]] = []
    mappings.extend((repo_root / source, skill_root / destination) for source, destination in REFERENCE_FILES.items())
    for source_dir, destination_dir in DIRECTORIES.items():
        source_root = repo_root / source_dir
        if not source_root.exists():
            issues.append(ValidationIssue("skill.missing_source", "error", "规范源目录不存在。", source_dir))
            continue
        for source in _iter_files(source_root):
            mappings.append((source, skill_root / destination_dir / source.relative_to(source_root)))

    manifest_files = []
    for source, destination in sorted(mappings, key=lambda pair: str(pair[1])):
        if not source.exists():
            issues.append(ValidationIssue("skill.missing_source", "error", "规范源文件不存在。", str(source.relative_to(repo_root))))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if destination.suffix.lower() == ".md" and "](../" in destination.read_text(encoding="utf-8", errors="replace"):
            issues.append(ValidationIssue("skill.external_relative_link", "error", "资源仍含仓库外相对链接。", str(destination.relative_to(skill_root))))
        manifest_files.append(
            {
                "source": str(source.relative_to(repo_root)).replace("\\", "/"),
                "destination": str(destination.relative_to(skill_root)).replace("\\", "/"),
                "sha256": _hash(destination),
            }
        )

    manifest_path = skill_root / "references/manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump({"version": 1, "files": manifest_files}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return CheckReport(
        "skill_bundle",
        not any(item.severity == "error" for item in issues),
        tuple(issues),
        {"file_count": len(manifest_files), "skill_root": str(skill_root)},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--skill-root", type=Path)
    args = parser.parse_args()
    skill_root = args.skill_root or args.repo_root / "skill/cumcm-assistant"
    report = build_skill_bundle(args.repo_root, skill_root)
    print(f"skill_bundle: {'PASS' if report.passed else 'FAIL'} ({report.metadata.get('file_count', 0)} files)")
    for item in report.issues:
        print(f"[{item.severity}] {item.code} {item.path or '-'}: {item.message}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
