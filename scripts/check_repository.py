"""Run existing Python test suites in their own working directories."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("solutions", "baseline", "adaptive", "toolkit", "all"), default="solutions")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    groups = {
        "adaptive": (root / "solutions/adaptive", [sys.executable, "run_tests.py"]),
        "baseline": (root / "solutions/baseline", [sys.executable, "-m", "pytest", "tests", "-q"]),
        "toolkit": (root / "toolkit", [sys.executable, "-m", "pytest", "tests", "-q"]),
    }
    selected = ("adaptive", "baseline", "toolkit") if args.suite == "all" else (
        ("adaptive", "baseline") if args.suite == "solutions" else (args.suite,)
    )
    failed = []
    for name in selected:
        cwd, command = groups[name]
        print(f"\nRunning {name}: {cwd}", flush=True)
        if subprocess.run(command, cwd=cwd, check=False).returncode:
            failed.append(name)
    print("\nFailed: " + ", ".join(failed) if failed else "\nAll selected suites passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
