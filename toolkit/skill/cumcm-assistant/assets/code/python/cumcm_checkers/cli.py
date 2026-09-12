"""Command-line entry for all repository checkers."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import yaml

from . import ai_usage, citations, code_bundle, package, paper
from .reporting import aggregate_to_dict


CHECKERS = (paper, citations, ai_usage, code_bundle, package)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cumcm-check")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("target", type=Path)
    check.add_argument("--rules", type=Path, required=True)
    check.add_argument("--json", dest="json_path", type=Path)
    check.add_argument("--stage", choices=("draft", "submission"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    rules = yaml.safe_load(args.rules.read_text(encoding="utf-8")) or {}
    configs = rules.get("checkers", {})
    reports = [module.run_check(args.target, {**configs.get(module.__name__.rsplit(".", 1)[-1], {}), **({"stage": args.stage} if args.stage else {})}) for module in CHECKERS]
    payload = aggregate_to_dict(reports)
    payload["stage"] = args.stage or "legacy"
    payload["scope"] = "仓库格式与工程预检；通过不等于数学正确或主办方验收。"
    for item in payload["checkers"]:
        print(f"{item['checker']}: {'PASS' if item['passed'] else 'FAIL'} ({item['issue_count']} issues)")
    for item in payload["issues"]:
        print(f"[{item['severity']}] {item['checker']} {item['code']} {item.get('path') or '-'}: {item['message']}")
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
