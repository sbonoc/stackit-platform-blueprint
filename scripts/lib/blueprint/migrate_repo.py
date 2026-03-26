#!/usr/bin/env python3
"""Apply repository migrations for the current blueprint template version."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path
import re
import sys
from typing import Callable


TARGET_TEMPLATE_VERSION = "1.0.0"
MIN_SUPPORTED_UPGRADE_FROM = "1.0.0"
MigrationStep = Callable[[Path], list[str]]


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_yaml_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _parse_semver(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _find_section(lines: list[str], marker: str) -> tuple[int, int, int] | None:
    start = -1
    base_indent = -1
    for idx, line in enumerate(lines):
        if line.strip() == f"{marker}:":
            start = idx
            base_indent = _indent(line)
            break
    if start == -1:
        return None

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        if not line.strip():
            continue
        if _indent(line) <= base_indent:
            end = idx
            break
    return start, end, base_indent


def _extract_section_scalar(
    lines: list[str],
    section: tuple[int, int, int] | None,
    key: str,
) -> str:
    if not section:
        return ""
    start, end, _ = section
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$")
    for line in lines[start + 1 : end]:
        match = pattern.match(line)
        if match:
            return _strip_yaml_scalar(match.group(1))
    return ""


def _resolve_source_template_version(repo_root: Path) -> str:
    contract_path = repo_root / "blueprint/contract.yaml"
    if not contract_path.is_file():
        raise ValueError("missing contract file: blueprint/contract.yaml")

    lines = contract_path.read_text(encoding="utf-8").splitlines()
    template_bootstrap = _find_section(lines, "template_bootstrap")
    template_version = _extract_section_scalar(lines, template_bootstrap, "template_version")
    if template_version:
        return template_version

    metadata = _find_section(lines, "metadata")
    metadata_version = _extract_section_scalar(lines, metadata, "version")
    if metadata_version:
        return metadata_version

    raise ValueError(
        "unable to resolve source template version from blueprint/contract.yaml; "
        "expected repository.template_bootstrap.template_version or metadata.version"
    )


def _migration_registry() -> dict[tuple[str, str], MigrationStep]:
    # Current repository state is pre-release baseline v1.0.0.
    # Add explicit transitions here only after first published template version.
    return {}


def _plan_migration_path(source_version: str, target_version: str) -> list[tuple[str, str]]:
    source_semver = _parse_semver(source_version)
    target_semver = _parse_semver(target_version)
    minimum_semver = _parse_semver(MIN_SUPPORTED_UPGRADE_FROM)
    if not source_semver:
        raise ValueError(f"source template version is not semver: {source_version}")
    if not target_semver:
        raise ValueError(f"target template version is not semver: {target_version}")
    if not minimum_semver:
        raise ValueError(f"minimum supported upgrade version is not semver: {MIN_SUPPORTED_UPGRADE_FROM}")

    if source_semver < minimum_semver:
        raise ValueError(
            f"unsupported upgrade path from {source_version} to {target_version}: "
            f"source version is older than minimum supported upgrade version {MIN_SUPPORTED_UPGRADE_FROM}"
        )
    if source_semver > target_semver:
        raise ValueError(
            f"unsupported upgrade path from {source_version} to {target_version}: "
            "source version is newer than target version"
        )
    if source_version == target_version:
        return []

    transitions = list(_migration_registry().keys())
    adjacency: dict[str, list[str]] = {}
    for from_version, to_version in transitions:
        adjacency.setdefault(from_version, []).append(to_version)

    queue: deque[str] = deque([source_version])
    parent: dict[str, str | None] = {source_version: None}

    while queue:
        current = queue.popleft()
        if current == target_version:
            break
        for candidate in adjacency.get(current, []):
            if candidate in parent:
                continue
            parent[candidate] = current
            queue.append(candidate)

    if target_version not in parent:
        supported_paths = ", ".join(f"{start}->{end}" for start, end in sorted(transitions))
        if not supported_paths:
            supported_paths = "none"
        raise ValueError(
            f"unsupported upgrade path from {source_version} to {target_version}; "
            f"supported transitions: {supported_paths}"
        )

    chain: list[str] = [target_version]
    while chain[-1] != source_version:
        prev = parent.get(chain[-1])
        if prev is None:
            break
        chain.append(prev)
    chain.reverse()

    return [(chain[idx], chain[idx + 1]) for idx in range(len(chain) - 1)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Absolute repository root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    try:
        source_version = _resolve_source_template_version(repo_root)
        migration_path = _plan_migration_path(source_version, TARGET_TEMPLATE_VERSION)
    except ValueError as exc:
        print(f"[blueprint-migrate] error: {exc}", file=sys.stderr)
        return 1

    if not migration_path:
        print(
            f"[blueprint-migrate] no migrations were required "
            f"(source and target template version: {TARGET_TEMPLATE_VERSION})"
        )
        return 0

    all_changes: list[str] = []
    registry = _migration_registry()
    for from_version, to_version in migration_path:
        print(f"[blueprint-migrate] applying migration step {from_version} -> {to_version}")
        migration_step = registry.get((from_version, to_version))
        if migration_step is None:
            print(
                f"[blueprint-migrate] error: missing migration implementation for step {from_version} -> {to_version}",
                file=sys.stderr,
            )
            return 1
        step_changes = migration_step(repo_root)
        if not step_changes:
            print(f"[blueprint-migrate] step {from_version} -> {to_version} completed (no file changes needed)")
            continue
        for change in step_changes:
            print(f"[blueprint-migrate] {change}")
        all_changes.extend(step_changes)

    try:
        final_version = _resolve_source_template_version(repo_root)
    except ValueError as exc:
        print(f"[blueprint-migrate] error: {exc}", file=sys.stderr)
        return 1
    if final_version != TARGET_TEMPLATE_VERSION:
        print(
            "[blueprint-migrate] error: migration did not converge to target template version "
            f"{TARGET_TEMPLATE_VERSION} (resolved: {final_version})",
            file=sys.stderr,
        )
        return 1

    print(f"[blueprint-migrate] migration complete (target template version {TARGET_TEMPLATE_VERSION})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
