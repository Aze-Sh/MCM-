from pathlib import Path

from pypdf import PdfWriter

from cumcm_checkers.paper import run_check


def test_valid_source_paper_passes() -> None:
    report = run_check(Path("tests/fixtures/checkers/valid"), {})
    assert report.passed


def test_pdf_page_limit_metadata_and_contents_are_checked(tmp_path: Path) -> None:
    writer = PdfWriter()
    for _ in range(31):
        writer.add_blank_page(width=595, height=842)
    writer.add_metadata({"/Author": "Example University"})
    with (tmp_path / "paper.pdf").open("wb") as stream:
        writer.write(stream)
    (tmp_path / "paper.tex").write_text("\\tableofcontents\n学校名称：示例大学", encoding="utf-8")

    report = run_check(tmp_path, {"max_pages": 30, "max_bytes": 20_000_000})
    codes = {issue.code for issue in report.issues}
    assert {"paper.page_limit", "paper.contents_page", "paper.identity"} <= codes


def test_paper_file_size_limit_is_checked(tmp_path: Path) -> None:
    (tmp_path / "paper.tex").write_text("anonymous", encoding="utf-8")
    report = run_check(tmp_path, {"max_bytes": 4})
    assert any(issue.code == "paper.file_size" for issue in report.issues)
