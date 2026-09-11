from pathlib import Path

from cumcm_py.content import validate_document


def test_catalog_matches_source_schema() -> None:
    issues = validate_document(
        Path("sources/catalog.yaml"), Path("schemas/source.schema.json")
    )
    assert issues == ()


def test_invalid_source_reports_missing_read_status() -> None:
    issues = validate_document(
        Path("tests/fixtures/content/invalid-source.yaml"),
        Path("schemas/source.schema.json"),
    )
    assert any(issue.code == "schema.required" for issue in issues)

