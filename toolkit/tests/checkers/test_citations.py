from pathlib import Path

from cumcm_checkers.citations import run_check


def test_registered_citation_passes() -> None:
    assert run_check(Path("tests/fixtures/checkers/valid"), {}).passed


def test_unregistered_citation_fails() -> None:
    report = run_check(Path("tests/fixtures/checkers/invalid"), {})
    assert not report.passed
    assert any(issue.code == "citation.unregistered_source" for issue in report.issues)
