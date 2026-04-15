#!/usr/bin/env python3
"""Render/check markdown SDD control catalog from machine-readable control catalog YAML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="surrogateescape")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ValueError(
                "control catalog YAML must be JSON-compatible when PyYAML is unavailable"
            ) from exc
        payload = yaml.safe_load(raw)

    if not isinstance(payload, dict):
        raise ValueError("control catalog must be a mapping")

    controls = payload.get("controls")
    if not isinstance(controls, list) or not controls:
        raise ValueError("control catalog must define a non-empty controls list")

    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _require_str(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"control entry missing required string field: {key}")
    return value.strip()


def _render_markdown(payload: dict[str, Any]) -> str:
    controls_raw = payload["controls"]

    lines: list[str] = []
    lines.append("# SDD Control Catalog")
    lines.append("")
    lines.append("This catalog defines executable guardrail controls for Spec-Driven Development.")
    lines.append("")
    lines.append("| Control ID | Normative Control | Applies In Phase(s) | Validation Command | Evidence Artifact(s) | Owner | Gate |")
    lines.append("|---|---|---|---|---|---|---|")

    normalized_controls: list[dict[str, Any]] = []
    for entry in controls_raw:
        if not isinstance(entry, dict):
            raise ValueError("control entries must be mappings")
        normalized_controls.append(entry)

    for entry in sorted(normalized_controls, key=lambda item: _require_str(item, "id")):
        control_id = _require_str(entry, "id")
        normative = _require_str(entry, "normative_control")
        phases = ", ".join(_string_list(entry.get("phases")))
        validation_command = _require_str(entry, "validation_command")
        evidence = ", ".join(_string_list(entry.get("evidence_artifacts")))
        owner = _require_str(entry, "owner")
        gate = _require_str(entry, "gate")

        if gate not in {"fail", "warn"}:
            raise ValueError(f"control {control_id} has unsupported gate: {gate}")

        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(control_id),
                    _escape_cell(normative),
                    _escape_cell(phases),
                    _escape_cell(validation_command),
                    _escape_cell(evidence),
                    _escape_cell(owner),
                    _escape_cell(gate),
                ]
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def _sync(*, repo_root: Path, input_path: Path, output_path: Path, check: bool) -> int:
    payload = _load_catalog(input_path)
    rendered = _render_markdown(payload)

    if output_path.is_file():
        current = output_path.read_text(encoding="utf-8", errors="surrogateescape")
        if current == rendered:
            print(f"control catalog already up to date: {output_path}")
            return 0
        if check:
            print(
                "control catalog markdown drift detected; run: "
                "python3 scripts/lib/spec_kit/render_control_catalog.py",
                file=sys.stderr,
            )
            return 1

    if check:
        print(
            "control catalog markdown missing; run: "
            "python3 scripts/lib/spec_kit/render_control_catalog.py",
            file=sys.stderr,
        )
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"rendered control catalog markdown: {output_path.relative_to(repo_root)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--input", type=Path, default=Path(".spec-kit/control-catalog.yaml"))
    parser.add_argument("--output", type=Path, default=Path(".spec-kit/control-catalog.md"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    input_path = args.input if args.input.is_absolute() else repo_root / args.input
    output_path = args.output if args.output.is_absolute() else repo_root / args.output
    return _sync(repo_root=repo_root, input_path=input_path, output_path=output_path, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
