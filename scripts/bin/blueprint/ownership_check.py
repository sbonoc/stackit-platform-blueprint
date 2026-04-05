#!/usr/bin/env python3
"""Resolve repository path ownership from blueprint contract metadata."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import BlueprintContract, load_blueprint_contract  # noqa: E402


ENV_PLACEHOLDER = "${ENV}"
KNOWN_ENV_NAMES = ("dev", "stage", "prod", "local")


@dataclass(frozen=True)
class OwnershipRule:
    owner: str
    source: str
    pattern: str
    regex: re.Pattern[str]


def _normalize_contract_pattern(pattern: str) -> str:
    normalized = pattern.strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _pattern_to_regex(pattern: str, *, is_directory: bool) -> re.Pattern[str]:
    normalized = _normalize_contract_pattern(pattern)
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    escaped = re.escape(normalized)
    escaped = escaped.replace(re.escape(ENV_PLACEHOLDER), r"[^/]+")
    if is_directory:
        return re.compile(rf"^{escaped}(?:/.*)?$")
    return re.compile(rf"^{escaped}$")


def _normalize_relative_path(raw_path: str, repo_root: Path) -> tuple[str, bool]:
    candidate = Path(raw_path).expanduser()
    repo_resolved = repo_root.resolve()
    if not candidate.is_absolute():
        candidate = repo_resolved / candidate
    resolved_candidate = candidate.resolve()
    try:
        relative = resolved_candidate.relative_to(repo_resolved)
    except ValueError:
        return PurePosixPath(resolved_candidate.as_posix()).as_posix(), False
    return PurePosixPath(relative.as_posix()).as_posix(), True


def _pattern_is_directory(pattern: str, repo_root: Path) -> bool:
    normalized = _normalize_contract_pattern(pattern)
    if normalized.endswith("/"):
        return True

    def _resolved_kind(candidate: str) -> bool | None:
        resolved_path = repo_root / candidate
        if resolved_path.is_dir():
            return True
        if resolved_path.is_file():
            return False
        return None

    if ENV_PLACEHOLDER in normalized:
        for env_name in KNOWN_ENV_NAMES:
            resolved = _resolved_kind(normalized.replace(ENV_PLACEHOLDER, env_name))
            if resolved is not None:
                return resolved

    resolved = _resolved_kind(normalized)
    if resolved is not None:
        return resolved

    return False


def _build_rules(contract: BlueprintContract, *, repo_root: Path) -> list[OwnershipRule]:
    repository = contract.repository
    make_ownership = contract.make_contract.ownership

    rule_specs: list[tuple[str, str, str]] = []

    for entry in repository.source_only_paths:
        rule_specs.append(("source-only", "repository.ownership_path_classes.source_only", entry))
    for entry in repository.consumer_seeded_paths:
        rule_specs.append(("consumer-seeded", "repository.ownership_path_classes.consumer_seeded", entry))
    for entry in repository.init_managed_paths:
        rule_specs.append(("init-managed", "repository.ownership_path_classes.init_managed", entry))
    for entry in repository.conditional_scaffold_paths:
        rule_specs.append(("conditional-scaffold", "repository.ownership_path_classes.conditional_scaffold", entry))

    for entry in contract.script_contract.platform_editable_roots:
        rule_specs.append(("platform-owned", "script_contract.platform_editable_roots", entry))
    rule_specs.append(("platform-owned", "make_contract.ownership.platform_editable_file", make_ownership.platform_editable_file))
    rule_specs.append(
        (
            "platform-owned",
            "make_contract.ownership.platform_editable_include_dir",
            f"{make_ownership.platform_editable_include_dir.rstrip('/')}/",
        )
    )
    rule_specs.append(("platform-owned", "docs_contract.platform_docs.root", f"{contract.docs_contract.platform_docs.root.rstrip('/')}/"))

    for entry in contract.script_contract.blueprint_managed_roots:
        rule_specs.append(("blueprint-managed", "script_contract.blueprint_managed_roots", entry))
    rule_specs.append(("blueprint-managed", "make_contract.ownership.root_loader_file", make_ownership.root_loader_file))
    rule_specs.append(
        ("blueprint-managed", "make_contract.ownership.blueprint_generated_file", make_ownership.blueprint_generated_file)
    )
    rule_specs.append(
        ("blueprint-managed", "docs_contract.blueprint_docs.root", f"{contract.docs_contract.blueprint_docs.root.rstrip('/')}/")
    )

    for entry in repository.required_files:
        rule_specs.append(("required-file", "repository.required_files", entry))

    rules: list[OwnershipRule] = []
    for owner, source, pattern in rule_specs:
        rules.append(
            OwnershipRule(
                owner=owner,
                source=source,
                pattern=pattern,
                regex=_pattern_to_regex(pattern, is_directory=_pattern_is_directory(pattern, repo_root)),
            )
        )
    return rules


def _resolve_path(path: str, *, repo_root: Path, rules: list[OwnershipRule]) -> dict[str, str]:
    normalized_path, in_repo = _normalize_relative_path(path, repo_root)
    if not in_repo:
        return {
            "input_path": path,
            "normalized_path": normalized_path,
            "owner": "outside-repository",
            "source": "n/a",
            "matched_pattern": "n/a",
        }

    for rule in rules:
        if rule.regex.fullmatch(normalized_path):
            return {
                "input_path": path,
                "normalized_path": normalized_path,
                "owner": rule.owner,
                "source": rule.source,
                "matched_pattern": rule.pattern,
            }
    return {
        "input_path": path,
        "normalized_path": normalized_path,
        "owner": "unknown",
        "source": "n/a",
        "matched_pattern": "n/a",
    }


def _metadata_payload(rules: list[OwnershipRule]) -> dict[str, object]:
    return {
        "rules": [
            {
                "owner": rule.owner,
                "source": rule.source,
                "pattern": rule.pattern,
            }
            for rule in rules
        ]
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve ownership class for repository paths.")
    parser.add_argument("paths", nargs="*", help="Paths to classify (relative or absolute).")
    parser.add_argument(
        "--contract-path",
        default=str(REPO_ROOT / "blueprint" / "contract.yaml"),
        help="Path to blueprint contract file (default: blueprint/contract.yaml).",
    )
    parser.add_argument("--json", action="store_true", help="Emit classified path results as JSON.")
    parser.add_argument(
        "--metadata-json",
        action="store_true",
        help="Emit machine-readable ownership metadata (rule patterns -> owner) as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.metadata_json and args.paths:
        print("--metadata-json cannot be combined with path arguments", file=sys.stderr)
        return 2

    contract_path = Path(args.contract_path)
    if not contract_path.is_absolute():
        contract_path = (REPO_ROOT / contract_path).resolve()
    contract = load_blueprint_contract(contract_path)
    rules = _build_rules(contract, repo_root=REPO_ROOT)

    if args.metadata_json:
        print(json.dumps(_metadata_payload(rules), indent=2, sort_keys=True))
        return 0

    if not args.paths:
        print("at least one path is required (or use --metadata-json)", file=sys.stderr)
        return 2

    results = [_resolve_path(path, repo_root=REPO_ROOT, rules=rules) for path in args.paths]
    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
        return 0

    for result in results:
        print(
            f"path={result['normalized_path']} "
            f"owner={result['owner']} "
            f"source={result['source']} "
            f"pattern={result['matched_pattern']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
