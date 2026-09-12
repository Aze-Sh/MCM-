from pathlib import Path
import json

from jsonschema import Draft202012Validator

from cumcm_py.content import load_yaml


REQUIRED = {
    "适用条件",
    "不适用条件",
    "数学定义",
    "假设",
    "输入输出",
    "选模理由",
    "Python 入口",
    "MATLAB 入口",
    "验证方法",
    "失败模式",
    "复杂度",
    "论文表达",
    "来源",
}


def test_method_cards_have_required_sections() -> None:
    cards = sorted(Path("knowledge/methods").glob("*.md"))
    assert len(cards) == 13
    for card in cards:
        text = card.read_text(encoding="utf-8")
        headings = {
            line.removeprefix("## ")
            for line in text.splitlines()
            if line.startswith("## ")
        }
        assert REQUIRED <= headings, card


def test_method_index_is_schema_valid_and_links_real_cards() -> None:
    index_path = Path("knowledge/methods/index.yaml")
    data = load_yaml(index_path)
    schema = json.loads(
        Path("schemas/method-card.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    assert len(data["methods"]) == 13
    for entry in data["methods"]:
        assert tuple(validator.iter_errors(entry)) == (), entry
        assert Path(entry["file"]).exists()
        assert entry["python_callable"]
        assert entry["matlab_callable"]
        assert entry["fixture_ids"]
