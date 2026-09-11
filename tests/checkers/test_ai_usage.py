from pathlib import Path

from cumcm_checkers.ai_usage import run_check


def test_complete_ai_log_passes() -> None:
    assert run_check(Path("tests/fixtures/checkers/valid"), {}).passed


def test_missing_ai_fields_fail() -> None:
    report = run_check(Path("tests/fixtures/checkers/invalid"), {})
    assert not report.passed
    assert any(issue.code == "ai.missing_field" for issue in report.issues)
