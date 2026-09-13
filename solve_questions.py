from pathlib import Path as lj
import sys

sys.path.insert(0, str(lj(__file__).resolve().parent / "src"))
from jammer_solver.questions import main

if __name__ == "__main__":
    main()
