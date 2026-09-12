from pathlib import Path

from cumcm_checkers.code_bundle import run_check


def test_runnable_relative_code_bundle_passes() -> None:
    assert run_check(Path("tests/fixtures/checkers/valid"), {}).passed


def test_absolute_path_and_missing_entry_fail() -> None:
    report = run_check(Path("tests/fixtures/checkers/invalid"), {})
    codes = {issue.code for issue in report.issues}
    assert {"code.absolute_path", "code.missing_entry"} <= codes


def test_http_url_is_not_mistaken_for_a_windows_drive_path(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text(
        "BASE_URL = 'http://127.0.0.1:2026'\n",
        encoding="utf-8",
    )

    assert run_check(tmp_path, {"stage": "draft"}).passed
