"""Run the bundled offline tests without connecting to the simulator."""

from pathlib import Path
import sys
import unittest


def main():
    root = Path(__file__).resolve().parent
    # Run in a separate process from pytest and other solutions: this project
    # contains its own coverage.py and uses same-directory module imports.
    sys.path.insert(0, str(root / "python"))
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
