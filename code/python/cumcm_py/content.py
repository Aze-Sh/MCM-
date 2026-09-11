"""Load and validate repository YAML/JSON knowledge documents."""

from pathlib import Path
from typing import Any
import json

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
import yaml

from .types import ValidationIssue


def load_yaml(path: Path) -> Any:
    """Load a UTF-8 YAML document."""

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_schema(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_document(
    path: Path, schema_path: Path
) -> tuple[ValidationIssue, ...]:
    """Return stable, path-aware JSON Schema issues for a YAML document."""

    document = load_yaml(path)
    schema_path = schema_path.resolve()
    schema = _load_schema(schema_path)
    schema.setdefault("$id", schema_path.as_uri())
    registry = Registry()
    for sibling in schema_path.parent.glob("*.schema.json"):
        sibling_schema = _load_schema(sibling)
        sibling_schema.setdefault("$id", sibling.resolve().as_uri())
        registry = registry.with_resource(
            sibling.resolve().as_uri(), Resource.from_contents(sibling_schema)
        )
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    return tuple(
        ValidationIssue(
            code=f"schema.{error.validator}",
            severity="error",
            message=error.message,
            path=".".join(str(part) for part in error.absolute_path) or None,
        )
        for error in errors
    )
