from pathlib import Path

from cumcm_py.cases import load_problem_card, validate_evidence_links
from cumcm_py.content import load_yaml, validate_document


def test_all_2021_2025_problem_cards_exist_and_validate() -> None:
    catalog = load_yaml(Path("sources/catalog.yaml"))
    cards = sorted(Path("cases/2021-2025").glob("20??/[A-E].yaml"))
    assert len(cards) == 25
    assert {(int(path.parent.name), path.stem) for path in cards} == {
        (year, problem)
        for year in range(2021, 2026)
        for problem in "ABCDE"
    }
    for path in cards:
        assert validate_document(path, Path("schemas/problem-card.schema.json")) == ()
        assert validate_evidence_links(load_problem_card(path), catalog) == (), path


def test_each_card_has_human_analysis_and_no_reproduced_statement() -> None:
    for yaml_path in sorted(Path("cases/2021-2025").glob("20??/[A-E].yaml")):
        page = yaml_path.with_suffix(".md")
        assert page.exists()
        text = page.read_text(encoding="utf-8")
        assert "## 难点" in text
        assert "## 获奖证据边界" in text
        assert "不复现题面" in text


def test_award_paper_indexes_state_provenance_limits() -> None:
    indexes = sorted(Path("cases/2021-2025").glob("20??/award-papers.yaml"))
    assert len(indexes) == 5
    for path in indexes:
        data = load_yaml(path)
        assert data["official_display_index"]
        assert data["causality_warning"]
        assert data["papers"]

