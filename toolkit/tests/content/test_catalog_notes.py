from pathlib import Path

import yaml


AUDITED_GROUPS = {
    "COURSE",
    "BOOK",
    "PYDOC",
    "MATLABDOC",
    "DATA",
    "LITERATURE",
    "PAPER",
}


def test_every_learning_or_data_source_has_a_note() -> None:
    entries = yaml.safe_load(
        Path("sources/catalog.yaml").read_text(encoding="utf-8")
    )["sources"]
    for entry in entries:
        audited_group = entry["id"].split("-", 1)[0] in AUDITED_GROUPS
        if audited_group and entry["read_status"] not in {"blocked", "dead-link"}:
            note = Path("sources/reading-notes") / f'{entry["id"]}.md'
            assert note.exists(), entry["id"]
