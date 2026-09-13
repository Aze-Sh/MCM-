"""Repository entry point for the final Q3/Q4 policy."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from jammer_solver.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
