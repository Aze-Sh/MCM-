import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tools.build_skill_bundle import build_skill_bundle


ROOT = Path(__file__).parents[2]
SKILL = ROOT / "skill" / "cumcm-assistant"


def test_checked_in_skill_bundle_matches_canonical_sources(tmp_path: Path) -> None:
    output = tmp_path / "cumcm-assistant"
    report = build_skill_bundle(ROOT, output)
    assert report.passed
    generated = yaml.safe_load((output / "references" / "manifest.yaml").read_text(encoding="utf-8"))
    checked_in = yaml.safe_load((SKILL / "references" / "manifest.yaml").read_text(encoding="utf-8"))
    assert generated == checked_in
    for item in generated["files"]:
        bundled = output / item["destination"]
        assert bundled.exists()
        assert hashlib.sha256(bundled.read_bytes()).hexdigest() == item["sha256"]


def test_skill_routes_all_representative_prompts(tmp_path: Path) -> None:
    output = tmp_path / "cumcm-assistant"
    assert build_skill_bundle(ROOT, output).passed
    cases = yaml.safe_load((ROOT / "tests/skill/prompts.yaml").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        completed = subprocess.run(
            [sys.executable, str(output / "scripts/route_intent.py"), case["intent"], "--prompt", case["prompt"]],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        assert payload["intent"] == case["intent"]
        assert set(case["expected_resources"]) <= set(payload["resources"])
        assert set(case["workflow_ids"]) <= set(payload["workflows"])
        for relative in payload["resources"]:
            assert (output / relative).exists(), (case["id"], relative)


def test_skill_is_concise_and_prioritizes_official_rules() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 220
    assert text.index("官方规则优先") < text.index("核心工作流")
    assert "不得隐瞒" in text
    for intent in (
        "analyze-problem",
        "select-model",
        "implement-python",
        "implement-matlab",
        "validate-results",
        "draft-structure",
        "check-submission",
        "record-ai-use",
    ):
        assert intent in text


def test_prompt_set_includes_refusal_to_hide_ai_use() -> None:
    cases = yaml.safe_load((ROOT / "tests/skill/prompts.yaml").read_text(encoding="utf-8"))["cases"]
    refusal = next(case for case in cases if case["id"] == "refuse-hide-ai")
    assert refusal["intent"] == "record-ai-use"
    assert refusal["must_refuse"] is True
