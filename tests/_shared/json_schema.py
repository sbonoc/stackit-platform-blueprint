from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def load_json_schema(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"schema payload must be an object: {path}")
    return payload


def assert_json_matches_schema(instance: Any, schema: dict[str, Any], *, path: str = "$") -> None:
    errors = _validate(instance, schema, path=path)
    if errors:
        raise AssertionError("\n".join(errors))


def _validate(instance: Any, schema: dict[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            if not any(_matches_type(instance, candidate) for candidate in expected_type):
                errors.append(f"{path}: expected one of types {expected_type}, got {type(instance).__name__}")
                return errors
        else:
            if not _matches_type(instance, expected_type):
                errors.append(f"{path}: expected type {expected_type}, got {type(instance).__name__}")
                return errors

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and instance not in enum_values:
        errors.append(f"{path}: expected one of enum {enum_values}, got {instance!r}")
        return errors

    if isinstance(instance, dict):
        errors.extend(_validate_object(instance, schema, path=path))
    elif isinstance(instance, list):
        errors.extend(_validate_array(instance, schema, path=path))

    return errors


def _validate_object(instance: dict[str, Any], schema: dict[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    if isinstance(required, list):
        for name in required:
            if name not in instance:
                errors.append(f"{path}: missing required property {name!r}")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    additional = schema.get("additionalProperties", True)

    for key, value in instance.items():
        child_path = f"{path}.{key}"
        if key in properties:
            child_schema = properties[key]
            if isinstance(child_schema, dict):
                errors.extend(_validate(value, child_schema, path=child_path))
            continue
        if additional is False:
            errors.append(f"{child_path}: additional property is not allowed")
            continue
        if isinstance(additional, dict):
            errors.extend(_validate(value, additional, path=child_path))
    return errors


def _validate_array(instance: list[Any], schema: dict[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []
    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(instance) < min_items:
        errors.append(f"{path}: expected at least {min_items} items, got {len(instance)}")

    items = schema.get("items")
    if isinstance(items, dict):
        for index, value in enumerate(instance):
            errors.extend(_validate(value, items, path=f"{path}[{index}]"))
    return errors


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return False
