from pathlib import Path


REQUIRED = {
    "## 输入",
    "## 输出",
    "## 步骤",
    "## 停止条件",
    "## 失败处理",
    "## 人工检查点",
    "## 来源",
}


def test_eight_workflows_expose_stable_contract() -> None:
    workflows = sorted(Path("workflows").glob("*.md"))
    assert len(workflows) == 8
    for path in workflows:
        headings = {
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")
        }
        assert REQUIRED <= headings, path


def test_workflows_require_baseline_and_validation_before_conclusion() -> None:
    corpus = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("workflows").glob("*.md")
    )
    assert "基线" in corpus
    assert "数据泄漏" in corpus
    assert "验证证据" in corpus
    assert "AI工具使用详情" in corpus
