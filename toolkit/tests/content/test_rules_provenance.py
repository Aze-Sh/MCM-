from pathlib import Path
import re


RULE_FILES = sorted(Path("rules").glob("*.md"))


def test_every_normative_rule_has_source_id() -> None:
    assert RULE_FILES
    for path in RULE_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- 必须") or line.startswith("- 禁止"):
                assert re.search(r"\[OFF-CUMCM-[A-Z0-9-]+\]$", line), (path, line)
