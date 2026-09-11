import json
from pathlib import Path

from cumcm_checkers.cli import main


RULES = Path("checkers/rules/cumcm-2026.yaml")


def test_cli_valid_and_invalid_exit_codes(tmp_path: Path) -> None:
    valid_json = tmp_path / "valid.json"
    invalid_json = tmp_path / "invalid.json"
    assert main(["check", "tests/fixtures/checkers/valid", "--rules", str(RULES), "--json", str(valid_json)]) == 0
    assert main(["check", "tests/fixtures/checkers/invalid", "--rules", str(RULES), "--json", str(invalid_json)]) == 1
    valid = json.loads(valid_json.read_text(encoding="utf-8"))
    invalid = json.loads(invalid_json.read_text(encoding="utf-8"))
    assert valid["passed"] is True
    assert invalid["passed"] is False
    assert invalid["issues"] == sorted(invalid["issues"], key=lambda item: (item["checker"], item["code"], item.get("path") or ""))
