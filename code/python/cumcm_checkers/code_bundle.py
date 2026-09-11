"""Check code portability and a discoverable run entry."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from cumcm_py.types import CheckReport

from .reporting import issue, make_report, rule_sources


ABSOLUTE_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/]{1,2}|/(?:Users|home)/)")
ENTRY_NAMES = ("main.py", "main.m", "run.py", "run.m")


def run_check(target: str | Path, config: Mapping[str, Any]) -> CheckReport:
    target = Path(target)
    stage = str(config.get("stage", "submission"))
    roots = [target / "code"] if (target / "code").is_dir() else [target]
    files = sorted(path for root in roots for path in root.rglob("*") if path.suffix.lower() in {".py", ".m"})
    issues = []
    if stage == "draft":
        has_entry = any((target / name).is_file() for name in ENTRY_NAMES) or any((target / folder / name).is_file() for folder in ("python", "matlab") for name in ENTRY_NAMES)
    else:
        code_root = roots[0]
        has_entry = any((code_root / name).is_file() for name in ENTRY_NAMES)
    if not has_entry:
        issues.append(issue("code.missing_entry", "代码包缺少 main.py、main.m、run.py 或 run.m 入口。", path=str(roots[0].relative_to(target)) or ".", source_ids=rule_sources(config, "entry")))
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if ABSOLUTE_PATH.search(text):
            issues.append(issue("code.absolute_path", "代码中检测到绝对路径，无法保证换机复现。", path=str(path.relative_to(target)), source_ids=rule_sources(config, "portable_paths")))
    return make_report("code_bundle", issues, {"files_checked": len(files)})
