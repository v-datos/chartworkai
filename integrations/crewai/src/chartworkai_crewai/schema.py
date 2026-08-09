"""Standard-library validation against the bundled run-manifest schema."""

from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any


class ManifestValidationError(ValueError):
    """A generated run manifest does not match the bundled schema."""


def _schema() -> dict[str, Any]:
    resource = files("chartworkai_crewai.schemas").joinpath("run-manifest-v1.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return False


def _validate(value: Any, schema: dict[str, Any], path: str) -> None:
    expected = schema.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, choice) for choice in choices):
            raise ManifestValidationError(f"{path} must have type {' or '.join(choices)}")

    if "const" in schema and value != schema["const"]:
        raise ManifestValidationError(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ManifestValidationError(f"{path} is not an allowed value")
    if isinstance(value, str) and "pattern" in schema:
        if re.search(schema["pattern"], value) is None:
            raise ManifestValidationError(f"{path} does not match its required pattern")
    if isinstance(value, str) and "maxLength" in schema:
        if len(value) > schema["maxLength"]:
            raise ManifestValidationError(
                f"{path} exceeds its {schema['maxLength']}-character limit"
            )
    if isinstance(value, int) and "minimum" in schema and value < schema["minimum"]:
        raise ManifestValidationError(f"{path} must be at least {schema['minimum']}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise ManifestValidationError(f"{path} is missing: {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ManifestValidationError(f"{path} has unknown fields: {', '.join(unknown)}")
        for key, item in value.items():
            if key in properties:
                _validate(item, properties[key], f"{path}.{key}")

    if isinstance(value, list) and "items" in schema:
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ManifestValidationError(f"{path} exceeds its {schema['maxItems']}-item limit")
        for index, item in enumerate(value):
            _validate(item, schema["items"], f"{path}[{index}]")


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Validate one generated manifest or raise ``ManifestValidationError``."""
    _validate(manifest, _schema(), "manifest")
