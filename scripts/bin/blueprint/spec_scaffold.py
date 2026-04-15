#!/usr/bin/env python3
"""Scaffold a Spec-Driven Development work-item directory from canonical templates."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


def _as_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    raise ValueError(f"{field} must be a mapping")


def _as_list_of_str(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{idx}] must be a non-empty string")
        result.append(item.strip())
    return result


def _sanitize_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized:
        raise ValueError("slug must contain at least one alphanumeric character")
    return normalized


def _resolve_template_root(artifacts: dict[str, Any], track: str) -> Path:
    if track == "blueprint":
        template_root = str(artifacts.get("blueprint_template_root", "")).strip()
        if not template_root:
            raise ValueError("spec.spec_driven_development_contract.artifacts.blueprint_template_root must be set")
        return Path(template_root)
    if track == "consumer":
        template_root = str(artifacts.get("consumer_template_root", "")).strip()
        if not template_root:
            raise ValueError("spec.spec_driven_development_contract.artifacts.consumer_template_root must be set")
        return Path(template_root)
    raise ValueError(f"unsupported track: {track}")


def _copy_document(source: Path, target: Path) -> None:
    content = source.read_text(encoding="utf-8", errors="surrogateescape")
    target.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--slug", required=True, help="Work-item slug, e.g. runtime-identity-doctor")
    parser.add_argument("--track", choices=("blueprint", "consumer"), default="blueprint")
    parser.add_argument("--date", dest="work_date", default=date.today().isoformat())
    parser.add_argument("--force", action="store_true", help="Overwrite an existing scaffold directory")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    slug = _sanitize_slug(args.slug)

    try:
        work_date = date.fromisoformat(args.work_date)
    except ValueError as exc:
        raise ValueError("--date must be in YYYY-MM-DD format") from exc

    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    contract_raw = contract.raw
    spec_raw = _as_mapping(contract_raw.get("spec"), field="spec")
    sdd_raw = _as_mapping(
        spec_raw.get("spec_driven_development_contract"),
        field="spec.spec_driven_development_contract",
    )
    artifacts = _as_mapping(
        sdd_raw.get("artifacts"),
        field="spec.spec_driven_development_contract.artifacts",
    )
    required_documents = _as_list_of_str(
        artifacts.get("required_work_item_documents", []),
        field="spec.spec_driven_development_contract.artifacts.required_work_item_documents",
    )
    if not required_documents:
        raise ValueError(
            "spec.spec_driven_development_contract.artifacts.required_work_item_documents must not be empty"
        )

    template_root = repo_root / _resolve_template_root(artifacts, args.track)

    destination = repo_root / "specs" / f"{work_date.isoformat()}-{slug}"
    if destination.exists() and not args.force:
        raise ValueError(f"destination already exists: {destination.relative_to(repo_root)} (use --force to overwrite)")

    destination.mkdir(parents=True, exist_ok=True)
    for document in required_documents:
        source_path = template_root / document
        if not source_path.is_file():
            raise ValueError(f"missing template document: {source_path.relative_to(repo_root)}")
        _copy_document(source_path, destination / document)

    print(f"scaffolded SDD work item: {destination.relative_to(repo_root)}")
    for document in required_documents:
        print(f"  - {document}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
