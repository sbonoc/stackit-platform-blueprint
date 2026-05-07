#!/usr/bin/env python3
"""Seed consumer-seeded feature gate files into a consumer repository."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_yaml_subset  # noqa: E402
from scripts.lib.blueprint import upgrade_consumer as _uc  # noqa: E402

BLUEPRINT_UPGRADE_SOURCE_ENV = "BLUEPRINT_UPGRADE_SOURCE"
BLUEPRINT_UPGRADE_REF_ENV = "BLUEPRINT_UPGRADE_REF"
CONSUMER_TEMPLATE_ROOT = Path("scripts/templates/consumer/init")


def _load_gates(source_root: Path) -> list[dict]:
    contract_path = source_root / "blueprint/contract.yaml"
    if not contract_path.is_file():
        return []
    raw = load_yaml_subset(contract_path)
    spec = raw.get("spec") if isinstance(raw, dict) else None
    if not isinstance(spec, dict):
        return []
    gates = spec.get("consumer_seeded_feature_gates")
    return gates if isinstance(gates, list) else []


def _find_gate(source_root: Path, gate_id: str) -> dict | None:
    for gate in _load_gates(source_root):
        if isinstance(gate, dict) and gate.get("id") == gate_id:
            return gate
    return None


def _list_gate_ids(source_root: Path) -> list[str]:
    return [g["id"] for g in _load_gates(source_root) if isinstance(g, dict) and isinstance(g.get("id"), str)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed a consumer-seeded feature gate into a consumer repository."
    )
    parser.add_argument("--feature", required=True, help="Feature gate ID to seed.")
    parser.add_argument("--repo-root", default=".", help="Consumer repository root (default: .).")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    gate_id = args.feature

    defaults = _uc._read_repo_init_defaults(repo_root / "blueprint/repo.init.env")
    ref = os.environ.get(BLUEPRINT_UPGRADE_REF_ENV) or defaults.get("BLUEPRINT_UPGRADE_REF", "main")
    source = os.environ.get(BLUEPRINT_UPGRADE_SOURCE_ENV) or defaults.get("BLUEPRINT_UPGRADE_SOURCE", "")

    source_root, _source_repo, _commit = _uc._clone_source_repository(source, ref)

    gate = _find_gate(source_root, gate_id)
    if gate is None:
        known = _list_gate_ids(source_root)
        print(
            f"error: unknown feature gate '{gate_id}'; "
            f"known gates: {', '.join(known) or '(none)'}",
            file=sys.stderr,
        )
        sys.exit(1)

    gate_paths: list[str] = gate.get("consumer_seeded_paths_when_enabled") or []
    template_root = source_root / CONSUMER_TEMPLATE_ROOT

    for relative_path in gate_paths:
        tmpl_file = template_root / f"{relative_path}.tmpl"
        if not tmpl_file.is_file():
            print(f"error: template not found in source: {relative_path}.tmpl", file=sys.stderr)
            sys.exit(1)
        content = tmpl_file.read_text(encoding="utf-8")
        target = repo_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    print(f"seeded feature gate '{gate_id}': {len(gate_paths)} file(s) written.")


if __name__ == "__main__":
    main()
