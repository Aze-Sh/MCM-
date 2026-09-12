from pathlib import Path


ROOT = Path(__file__).parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_paper_template_has_no_toc_and_has_required_sections() -> None:
    text = read("templates/paper/main.tex")
    assert "\\tableofcontents" not in text
    for section in (
        "摘要",
        "问题重述",
        "模型假设",
        "符号说明",
        "模型建立",
        "模型检验",
        "结论",
        "参考文献",
    ):
        assert section in text


def test_paper_template_is_anonymous_and_source_grounded() -> None:
    main = read("templates/paper/main.tex")
    style = read("templates/paper/cumcm2026.sty")
    combined = main + style
    assert "姓名" not in combined
    assert "学校名称" not in combined
    assert "OFF-CUMCM-2026-FORMAT" in style
    assert "OFF-CUMCM-2026-RULES" in style


def test_ai_disclosure_contains_required_audit_fields() -> None:
    text = read("templates/ai-usage/AI工具使用详情.md")
    for field in ("工具与模型", "使用目的", "关键提示词", "关键回复", "采纳情况", "人工修改"):
        assert field in text
    assert "不得隐瞒" in text


def test_figure_helpers_define_reproducible_exports() -> None:
    python_style = read("templates/figures/python_style.py")
    matlab_style = read("templates/figures/matlabStyle.m")
    assert "dpi=400" in python_style
    assert 'format="pdf"' in python_style
    assert 'format="svg"' in python_style
    assert "exportgraphics" in matlab_style
    assert "Resolution" in matlab_style
    assert "400" in matlab_style


def test_citation_record_and_bibliography_are_present() -> None:
    record = read("templates/citations/source-record.yaml")
    bibliography = read("templates/paper/references.bib")
    for field in ("source_id:", "title:", "url:", "accessed_at:", "evidence_level:"):
        assert field in record
    assert "@misc" in bibliography
