"""Exercise the 2026 disclosure rules on actual source documents and PDFs."""

from pathlib import Path

import pytest
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen.canvas import Canvas

from cumcm_checkers.ai_usage import run_check
from cumcm_checkers.cli import main


USED = "本参赛队在竞赛过程中使用了AI工具，主要用于代码调试，详细使用情况见支撑材料。"
UNUSED = "本参赛队在竞赛过程中未使用任何AI工具。"
DETAILS = """工具与模型：Example Tool / Model 1
使用目的：代码调试
主要提示方式：描述异常与输入输出约束
使用过程：输入小规模实例，逐步修正索引
采纳情况：采纳了索引修正
人工修改：调整变量名并补充边界检查
人工核验：队员用手算实例复算，目标值一致
"""


def pdf(path: Path, text: str) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    canvas = Canvas(str(path))
    canvas.setAuthor("")
    canvas.setFont("STSong-Light", 10)
    for index, line in enumerate(text.splitlines()):
        canvas.drawString(40, 800 - index * 18, line)
    canvas.save()


def paper(statement: str = USED) -> str:
    return f"摘要\n模型与结果\nAI工具使用声明\n{statement}\n参考文献\n[1] Example reference"


def codes(report) -> set[str]:
    return {item.code for item in report.issues}


def test_draft_resolves_tex_inputs_and_ignores_commented_unused_example(tmp_path: Path):
    folder = tmp_path / "paper"
    (folder / "sections").mkdir(parents=True)
    (folder / "main.tex").write_text(
        r"\input{sections/ai}" + "\n" + r"\begin{thebibliography}{9}\end{thebibliography}", encoding="utf-8"
    )
    (folder / "sections/ai.tex").write_text(
        "% " + UNUSED + "\n" + r"\section*{AI工具使用声明}" + "\n" + USED, encoding="utf-8"
    )
    (tmp_path / "AI工具使用详情.md").write_text(DETAILS, encoding="utf-8")
    report = run_check(tmp_path, {"stage": "draft"})
    assert report.passed
    assert report.metadata["ai_used"] is True


@pytest.mark.parametrize("statement,want", [
    ("", "ai.declaration_missing"),
    (USED + UNUSED, "ai.declaration_conflict"),
    ("本参赛队在竞赛过程中使用了AI工具，详细使用情况见支撑材料。", "ai.purpose_missing"),
    ("本参赛队在竞赛过程中使用了AI工具，主要用于待填写，详细使用情况见支撑材料。", "ai.placeholder"),
])
def test_draft_rejects_incomplete_or_conflicting_declarations(tmp_path: Path, statement: str, want: str):
    (tmp_path / "paper.md").write_text(paper(statement), encoding="utf-8")
    (tmp_path / "AI工具使用详情.md").write_text(DETAILS, encoding="utf-8")
    assert want in codes(run_check(tmp_path, {"stage": "draft"}))


def test_declaration_after_references_fails(tmp_path: Path):
    (tmp_path / "paper.md").write_text("参考文献\n[1] Example\nAI工具使用声明\n" + USED, encoding="utf-8")
    (tmp_path / "AI工具使用详情.md").write_text(DETAILS, encoding="utf-8")
    assert "ai.declaration_order" in codes(run_check(tmp_path, {}))


def test_submission_requires_actual_paper_and_details_pdfs(tmp_path: Path):
    (tmp_path / "paper.md").write_text(paper(), encoding="utf-8")
    (tmp_path / "AI工具使用详情.md").write_text(DETAILS, encoding="utf-8")
    assert "ai.paper_pdf_missing" in codes(run_check(tmp_path, {"stage": "submission"}))
    pdf(tmp_path / "paper.pdf", paper())
    assert "ai.details_pdf_missing" in codes(run_check(tmp_path, {"stage": "submission"}))
    pdf(tmp_path / "AI工具使用详情.pdf", DETAILS)
    assert run_check(tmp_path, {"stage": "submission"}).passed


def test_submission_reads_pdf_even_if_source_has_corrected_statement(tmp_path: Path):
    pdf(tmp_path / "paper.pdf", "摘要\n模型与结果\n参考文献")
    (tmp_path / "paper.md").write_text(paper(), encoding="utf-8")
    pdf(tmp_path / "AI工具使用详情.pdf", DETAILS)
    assert "ai.declaration_missing" in codes(run_check(tmp_path, {"stage": "submission"}))


def test_unused_statement_does_not_require_details_but_rejects_conflicting_log(tmp_path: Path):
    pdf(tmp_path / "paper.pdf", paper(UNUSED))
    assert run_check(tmp_path, {"stage": "submission"}).passed
    (tmp_path / "AI工具使用详情.md").write_text(DETAILS, encoding="utf-8")
    assert "ai.declaration_conflict" in codes(run_check(tmp_path, {"stage": "submission"}))


@pytest.mark.parametrize("body,want", [
    (DETAILS.replace("人工核验：队员用手算实例复算，目标值一致", ""), "ai.missing_field"),
    (DETAILS.replace("人工核验：队员用手算实例复算，目标值一致", "人工核验：待填写"), "ai.placeholder"),
    (DETAILS.replace("工具与模型：Example Tool / Model 1", "工具与模型："), "ai.empty_field"),
])
def test_details_pdf_content_is_checked(tmp_path: Path, body: str, want: str):
    pdf(tmp_path / "paper.pdf", paper())
    pdf(tmp_path / "AI工具使用详情.pdf", body)
    assert want in codes(run_check(tmp_path, {"stage": "submission"}))


def test_unreadable_pdf_fails_closed(tmp_path: Path):
    pdf(tmp_path / "paper.pdf", paper())
    (tmp_path / "AI工具使用详情.pdf").write_bytes(b"not a PDF")
    assert "ai.invalid_pdf" in codes(run_check(tmp_path, {"stage": "submission"}))


def test_language_polishing_exception_only_applies_when_explicit(tmp_path: Path):
    body = "工具与模型：Example / 1\n使用目的：仅语言润色\n主要提示方式：要求简化语句\n使用过程：润色摘要"
    pdf(tmp_path / "paper.pdf", paper(USED.replace("代码调试", "仅语言润色")))
    pdf(tmp_path / "AI工具使用详情.pdf", body)
    assert run_check(tmp_path, {"stage": "submission"}).passed
    pdf(tmp_path / "paper.pdf", paper())
    assert "ai.missing_field" in codes(run_check(tmp_path, {"stage": "submission"}))


def test_submission_cli_rejects_source_only_project(tmp_path: Path):
    (tmp_path / "paper.md").write_text(paper(), encoding="utf-8")
    (tmp_path / "AI工具使用详情.md").write_text(DETAILS, encoding="utf-8")
    (tmp_path / "code").mkdir()
    (tmp_path / "code/main.py").write_text("print(1)", encoding="utf-8")
    assert main(["check", str(tmp_path), "--rules", "checkers/rules/cumcm-2026.yaml", "--stage", "submission"]) == 1
