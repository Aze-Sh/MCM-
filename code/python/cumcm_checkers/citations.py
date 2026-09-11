"""Check that source IDs cited in paper text are registered."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from cumcm_py.types import CheckReport

from .reporting import issue, make_report, rule_sources


SOURCE_PATTERN = re.compile(r"\[([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)\]")


def _registered(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("sources", []) if isinstance(data, dict) else []
    return {str(item.get("source_id") or item.get("id")) for item in items if isinstance(item, dict) and (item.get("source_id") or item.get("id"))}


def run_check(target: str | Path, config: Mapping[str, Any]) -> CheckReport:
    target = Path(target)
    registry = target / "sources.yaml"
    registered = _registered(registry)
    cited: set[str] = set()
    for folder in (target, target / "paper"):
        for name in ("paper.tex", "paper.md", "main.tex"):
            path = folder / name
            if path.exists():
                cited.update(SOURCE_PATTERN.findall(path.read_text(encoding="utf-8", errors="replace")))
    issues = [
        issue("citation.unregistered_source", f"来源编号 {source_id} 未在 sources.yaml 登记。", path="sources.yaml", source_ids=rule_sources(config))
        for source_id in sorted(cited - registered)
    ]
    if cited and not registry.exists():
        issues.append(issue("citation.registry_missing", "论文使用了来源编号，但 sources.yaml 不存在。", path="sources.yaml", source_ids=rule_sources(config)))
    return make_report("citations", issues, {"cited": sorted(cited), "registered": sorted(registered)})
