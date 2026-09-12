import json
from pathlib import Path

import yaml

from tools.compare_outputs import compare_fixture_manifest, compare_result_files


ROOT = Path("tests/fixtures/cross-language")


def test_cross_language_comparison_accepts_tolerance() -> None:
    report = compare_result_files(
        ROOT / "python.json",
        ROOT / "matlab-close.json",
        ROOT / "manifest.yaml",
    )
    assert report.passed
    assert report.metadata["compared_properties"] == 4


def test_cross_language_comparison_rejects_wrong_ranking() -> None:
    report = compare_result_files(
        ROOT / "python.json",
        ROOT / "matlab-wrong.json",
        ROOT / "manifest.yaml",
    )
    assert not report.passed
    assert any(issue.code == "cross.exact_mismatch" for issue in report.issues)


def test_cross_language_comparison_rejects_missing_property() -> None:
    report = compare_result_files(
        ROOT / "python.json",
        ROOT / "matlab-missing.json",
        ROOT / "manifest.yaml",
    )
    assert not report.passed
    assert any(issue.code == "cross.missing_property" for issue in report.issues)


def test_shared_manifest_covers_every_method_fixture() -> None:
    method_index = yaml.safe_load(
        Path("knowledge/methods/index.yaml").read_text(encoding="utf-8")
    )
    manifest = yaml.safe_load(
        Path("code/fixtures/manifest.yaml").read_text(encoding="utf-8")
    )
    expected = {item["fixture_ids"][0] for item in method_index["methods"]}
    actual = {item["id"] for item in manifest["fixtures"]}
    assert actual == expected
    for item in manifest["fixtures"]:
        assert (Path("code/fixtures") / item["input"]).exists()
        assert (Path("code/fixtures/expected") / f'{item["id"]}.json').exists()


def test_fixture_manifest_compares_every_declared_output(tmp_path: Path) -> None:
    expected_dir = tmp_path / "expected"
    actual_dir = tmp_path / "actual"
    expected_dir.mkdir()
    actual_dir.mkdir()
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """schema_version: 1
fixtures:
  - id: exact
    properties: [values.label]
    absolute_tolerance: 0
    relative_tolerance: 0
  - id: numeric
    properties: [values.score]
    absolute_tolerance: 1.0e-6
    relative_tolerance: 1.0e-6
""",
        encoding="utf-8",
    )
    (expected_dir / "exact.json").write_text(
        json.dumps({"values": {"label": "winner"}}), encoding="utf-8"
    )
    (actual_dir / "exact.json").write_text(
        json.dumps({"values": {"label": "winner"}}), encoding="utf-8"
    )
    (expected_dir / "numeric.json").write_text(
        json.dumps({"values": {"score": [1.0, 2.0]}}), encoding="utf-8"
    )
    (actual_dir / "numeric.json").write_text(
        json.dumps({"values": {"score": [1.0, 2.0000005]}}), encoding="utf-8"
    )

    report = compare_fixture_manifest(expected_dir, actual_dir, manifest)

    assert report.passed
    assert report.metadata["fixture_count"] == 2
    assert report.metadata["compared_properties"] == 2


def test_fixture_manifest_rejects_missing_matlab_output(tmp_path: Path) -> None:
    expected_dir = tmp_path / "expected"
    actual_dir = tmp_path / "actual"
    expected_dir.mkdir()
    actual_dir.mkdir()
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """schema_version: 1
fixtures:
  - id: missing
    properties: [values.score]
    absolute_tolerance: 0
    relative_tolerance: 0
""",
        encoding="utf-8",
    )
    (expected_dir / "missing.json").write_text(
        json.dumps({"values": {"score": 1.0}}), encoding="utf-8"
    )

    report = compare_fixture_manifest(expected_dir, actual_dir, manifest)

    assert not report.passed
    assert any(issue.code == "cross.missing_output" for issue in report.issues)
