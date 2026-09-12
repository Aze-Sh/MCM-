from pathlib import Path
import re


def test_inferred_award_patterns_are_labeled_and_sourced() -> None:
    text = Path("knowledge/award-patterns.md").read_text(encoding="utf-8")
    conclusions = [line for line in text.splitlines() if line.startswith("- 结论：")]
    assert len(conclusions) >= 12
    for line in conclusions:
        assert re.search(r"类型：(官方评价|论文观察|分析推断)", line), line
        assert re.search(r"来源：\[[A-Z0-9, -]+\]", line), line
        if "类型：分析推断" in line:
            assert "OFF-CUMCM-NATIONAL-JUDGING" in line
            assert "PAPERS" in line


def test_problem_type_guides_are_actionable() -> None:
    required = {
        "## 识别信号",
        "## 快速基线",
        "## 候选模型",
        "## 数据要求",
        "## 否决性假设",
        "## 最低验证",
        "## 适合图表",
        "## 方法卡链接",
    }
    guides = sorted(Path("knowledge/problem-types").glob("*.md"))
    assert len(guides) == 6
    for guide in guides:
        text = guide.read_text(encoding="utf-8")
        headings = {line for line in text.splitlines() if line.startswith("## ")}
        assert required <= headings, guide


def test_model_selection_has_required_vocabulary() -> None:
    text = Path("knowledge/model-selection.md").read_text(encoding="utf-8")
    for token in (
        "识别信号",
        "基线",
        "候选模型",
        "必须验证",
        "失败模式",
        "证据 ID",
    ):
        assert token in text


def test_manual_review_does_not_claim_full_automation() -> None:
    text = Path("validation/award-feature-review.md").read_text(encoding="utf-8")
    assert "不得自动判定" in text
    assert "人工复核" in text
