"""Run the bundled objective submission checkers without repository access."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--stage", choices=("draft", "submission"), default="submission")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(skill_root / "assets/code/python"))
    from cumcm_checkers.cli import main as checker_main

    command = ["check", str(args.target), "--rules", str(skill_root / "assets/checkers/rules/cumcm-2026.yaml")]
    command.extend(["--stage", args.stage])
    if args.json_path:
        command.extend(["--json", str(args.json_path)])
    return checker_main(command)


if __name__ == "__main__":
    raise SystemExit(main())
