#!/usr/bin/env python3
"""Canonical state-artifact dual-write helpers and schema validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_path, resolve_repo_root  # noqa: E402


DEFAULT_SCHEMA_PATH = Path("scripts/lib/infra/schemas/state_artifact.schema.json")
CANONICAL_SCHEMA_VERSION = "1.0.0"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _load_schema(path: Path) -> dict[str, Any]:
    schema = _load_json(path)
    if schema.get("type") != "object":
        raise ValueError(f"schema root type must be object: {path}")
    return schema


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


def _validate_json_schema(instance: Any, schema: dict[str, Any], *, path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            if not any(_matches_type(instance, candidate) for candidate in expected_type):
                errors.append(f"{path}: expected one of types {expected_type}, got {type(instance).__name__}")
                return errors
        elif isinstance(expected_type, str):
            if not _matches_type(instance, expected_type):
                errors.append(f"{path}: expected type {expected_type}, got {type(instance).__name__}")
                return errors

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and instance not in enum_values:
        errors.append(f"{path}: expected one of enum {enum_values}, got {instance!r}")
        return errors

    errors.extend(_validate_numeric_keywords(instance, schema, path=path))

    if isinstance(instance, dict):
        errors.extend(_validate_object(instance, schema, path=path))
    elif isinstance(instance, list):
        errors.extend(_validate_array(instance, schema, path=path))
    return errors


def _validate_numeric_keywords(instance: Any, schema: dict[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(instance, bool) or not isinstance(instance, (int, float)):
        return errors

    minimum = schema.get("minimum")
    if isinstance(minimum, (int, float)) and instance < minimum:
        errors.append(f"{path}: expected value >= {minimum}, got {instance}")

    maximum = schema.get("maximum")
    if isinstance(maximum, (int, float)) and instance > maximum:
        errors.append(f"{path}: expected value <= {maximum}, got {instance}")

    exclusive_minimum = schema.get("exclusiveMinimum")
    if isinstance(exclusive_minimum, (int, float)) and instance <= exclusive_minimum:
        errors.append(f"{path}: expected value > {exclusive_minimum}, got {instance}")

    exclusive_maximum = schema.get("exclusiveMaximum")
    if isinstance(exclusive_maximum, (int, float)) and instance >= exclusive_maximum:
        errors.append(f"{path}: expected value < {exclusive_maximum}, got {instance}")

    return errors


def _validate_object(instance: dict[str, Any], schema: dict[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    if isinstance(required, list):
        for name in required:
            if isinstance(name, str) and name not in instance:
                errors.append(f"{path}: missing required property {name!r}")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    additional = schema.get("additionalProperties", True)

    for key, value in instance.items():
        child_path = f"{path}.{key}"
        if key in properties and isinstance(properties[key], dict):
            errors.extend(_validate_json_schema(value, properties[key], path=child_path))
            continue
        if additional is False:
            errors.append(f"{child_path}: additional property is not allowed")
            continue
        if isinstance(additional, dict):
            errors.extend(_validate_json_schema(value, additional, path=child_path))
    return errors


def _validate_array(instance: list[Any], schema: dict[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []
    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(instance) < min_items:
        errors.append(f"{path}: expected at least {min_items} items, got {len(instance)}")

    items = schema.get("items")
    if isinstance(items, dict):
        for index, value in enumerate(instance):
            errors.extend(_validate_json_schema(value, items, path=f"{path}[{index}]"))
    return errors


def _parse_env_payload(path: Path) -> tuple[list[str], dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"state env file does not exist: {path}")
    order: list[str] = []
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in raw_line:
            raise ValueError(f"{path}:{line_number} must follow key=value format")
        key, value = raw_line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{path}:{line_number} has empty key")
        if key in entries:
            raise ValueError(f"{path}:{line_number} duplicates key {key!r}")
        entries[key] = value
        order.append(key)
    return order, entries


def render_state_artifact_payload(
    *,
    repo_root: Path,
    name: str,
    namespace: str,
    env_path: Path,
    json_path: Path,
) -> dict[str, Any]:
    entry_order, entries = _parse_env_payload(env_path)
    return {
        "schemaVersion": CANONICAL_SCHEMA_VERSION,
        "artifact": {
            "name": name,
            "namespace": namespace,
            "envPath": display_repo_path(repo_root, env_path),
            "jsonPath": display_repo_path(repo_root, json_path),
        },
        "entryCount": len(entry_order),
        "entryOrder": entry_order,
        "entries": entries,
    }


def _validate_state_artifact_invariants(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    entry_count = payload.get("entryCount")
    entry_order = payload.get("entryOrder")
    entries = payload.get("entries")
    if not isinstance(entry_count, int) or isinstance(entry_count, bool):
        return errors
    if not isinstance(entry_order, list) or not isinstance(entries, dict):
        return errors

    if entry_count != len(entry_order):
        errors.append(
            f"$.entryCount must equal len($.entryOrder); "
            f"found entryCount={entry_count}, len(entryOrder)={len(entry_order)}"
        )

    key_counts: dict[str, int] = {}
    for key in entry_order:
        if not isinstance(key, str):
            continue
        key_counts[key] = key_counts.get(key, 0) + 1
    duplicate_keys = sorted(key for key, count in key_counts.items() if count > 1)
    if duplicate_keys:
        errors.append(
            "$.entryOrder must not contain duplicate keys; found duplicates: "
            + ", ".join(duplicate_keys)
        )

    order_key_set = {key for key in entry_order if isinstance(key, str)}
    entries_key_set = set(entries.keys())
    missing_from_entries = sorted(order_key_set - entries_key_set)
    extra_in_entries = sorted(entries_key_set - order_key_set)
    if missing_from_entries or extra_in_entries:
        issues: list[str] = []
        if missing_from_entries:
            issues.append("missing from $.entries: " + ", ".join(missing_from_entries))
        if extra_in_entries:
            issues.append("extra in $.entries: " + ", ".join(extra_in_entries))
        errors.append("$.entryOrder/$.entries key mismatch (" + "; ".join(issues) + ")")

    return errors


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _render_command(args: argparse.Namespace, repo_root: Path) -> int:
    schema_path = resolve_repo_path(repo_root, args.schema).resolve()
    schema = _load_schema(schema_path)

    env_path = resolve_repo_path(repo_root, args.env_file).resolve()
    json_path = resolve_repo_path(repo_root, args.output_json).resolve()
    payload = render_state_artifact_payload(
        repo_root=repo_root,
        name=args.name,
        namespace=args.namespace,
        env_path=env_path,
        json_path=json_path,
    )
    errors = _validate_json_schema(payload, schema)
    errors.extend(_validate_state_artifact_invariants(payload))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.check:
        if not json_path.is_file():
            print(f"missing state artifact json: {display_repo_path(repo_root, json_path)}", file=sys.stderr)
            return 1
        existing = _load_json(json_path)
        if existing != payload:
            print(
                "state artifact json out of date: "
                f"{display_repo_path(repo_root, json_path)}",
                file=sys.stderr,
            )
            return 1
        return 0

    _write_json(json_path, payload)
    return 0


def _validate_command(args: argparse.Namespace, repo_root: Path) -> int:
    schema_path = resolve_repo_path(repo_root, args.schema).resolve()
    schema = _load_schema(schema_path)
    json_path = resolve_repo_path(repo_root, args.json_file).resolve()

    payload = _load_json(json_path)
    errors = _validate_json_schema(payload, schema)
    errors.extend(_validate_state_artifact_invariants(payload))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=REPO_ROOT,
        help="Repository root used to resolve relative paths.",
    )
    parser.add_argument(
        "--schema",
        default=DEFAULT_SCHEMA_PATH,
        help="Schema path used to validate state artifact JSON payloads.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser(
        "render",
        help="Render canonical state artifact JSON from a key=value env payload.",
    )
    render.add_argument("--name", required=True, help="State artifact name (without extension).")
    render.add_argument("--namespace", required=True, help="State namespace (infra/apps/docs).")
    render.add_argument("--env-file", required=True, help="Path to source .env state file.")
    render.add_argument("--output-json", required=True, help="Path to canonical output .json state file.")
    render.add_argument("--check", action="store_true", help="Fail when existing output differs from rendered payload.")

    validate = subparsers.add_parser(
        "validate",
        help="Validate an existing state artifact JSON payload against the canonical schema.",
    )
    validate.add_argument("--json-file", required=True, help="Path to state artifact .json file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    if args.command == "render":
        return _render_command(args, repo_root)
    if args.command == "validate":
        return _validate_command(args, repo_root)
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
