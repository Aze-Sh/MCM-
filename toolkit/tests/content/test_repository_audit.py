from pathlib import Path

import yaml


def test_every_repository_source_has_an_audit_note() -> None:
    entries = yaml.safe_load(
        Path("sources/catalog.yaml").read_text(encoding="utf-8")
    )["sources"]
    repo_ids = [entry["id"] for entry in entries if entry["id"].startswith("REPO-")]
    assert repo_ids
    for source_id in repo_ids:
        assert (Path("sources/reading-notes") / f"{source_id}.md").exists(), source_id


def test_license_matrix_states_reuse_policy() -> None:
    matrix = Path("sources/repository-license-audit.md").read_text(encoding="utf-8")
    for term in ("MIT", "未发现许可证", "不复制", "2026 官方格式"):
        assert term in matrix
