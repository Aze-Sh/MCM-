from pathlib import Path

from cumcm_checkers.package import run_check


def test_valid_submission_structure_passes() -> None:
    assert run_check(Path("tests/fixtures/checkers/valid"), {}).passed


def test_temporary_file_and_invalid_structure_fail() -> None:
    report = run_check(Path("tests/fixtures/checkers/invalid"), {})
    codes = {issue.code for issue in report.issues}
    assert {"package.temporary_file", "package.invalid_structure"} <= codes
