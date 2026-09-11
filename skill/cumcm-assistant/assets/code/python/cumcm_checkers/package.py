"""Check objective submission-directory structure and removable artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from cumcm_py.types import CheckReport

from .reporting import issue, make_report, rule_sources


PAPER_NAMES = ("paper.pdf", "paper.tex", "paper.md", "main.pdf", "main.tex")
ENTRY_NAMES = ("main.py", "main.m", "run.py", "run.m")
TEMP_SUFFIXES = {".tmp", ".bak", ".aux", ".log", ".out", ".pyc"}


def run_check(target: str | Path, config: Mapping[str, Any]) -> CheckReport:
    target = Path(target)
    stage = str(config.get("stage", "submission"))
    issues = []
    code_root = target / "code"
    required_ok = any((target / name).is_file() for name in PAPER_NAMES)
    required_ok = required_ok and code_root.is_dir() and any((code_root / name).is_file() for name in ENTRY_NAMES)
    required_ok = required_ok and any((target / name).is_file() for name in ("AI工具使用详情.md", "ai-usage.md", "AI-use.md"))
    if stage != "draft" and not required_ok:
        issues.append(issue("package.invalid_structure", "提交目录必须在顶层包含论文、AI 使用记录和带运行入口的 code 目录。", path=str(target), source_ids=rule_sources(config, "structure")))
    for path in sorted(item for item in target.rglob("*") if item.is_file()):
        if path.suffix.lower() in TEMP_SUFFIXES or path.name.endswith("~") or "__pycache__" in path.parts:
            issues.append(issue("package.temporary_file", "提交包包含临时或缓存文件。", path=str(path.relative_to(target)), source_ids=rule_sources(config, "temporary_files")))
    return make_report("package", issues, {"target": str(target)})
