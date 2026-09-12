"""Contest entry point: keep paths relative to the project root."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data_path = ROOT / "data" / "raw"
    output_path = ROOT / "output"
    output_path.mkdir(exist_ok=True)
    print(f"Read audited inputs from {data_path}")


if __name__ == "__main__":
    main()

