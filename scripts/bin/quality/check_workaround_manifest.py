#!/usr/bin/env python3
"""Validate all action_path entries in the workaround catalogue manifest."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / ".agents/skills/blueprint-consumer-upgrade"
MANIFEST_PATH = SKILL_ROOT / "workarounds/manifest.yaml"


_PREFIX = "[quality-workaround-manifest-check]"


def check_manifest(manifest_path: Path, skill_root: Path) -> list[str]:
    if not manifest_path.exists():
        return [f"{_PREFIX} manifest not found: {manifest_path}"]
    content = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    violations = []
    skill_root_resolved = skill_root.resolve()
    for version, version_data in content.get("versions", {}).items():
        for entry in version_data.get("workarounds", []):
            action_path = entry.get("action_path") or ""
            entry_id = entry.get("id", "?")
            tag = f"(id={entry_id!r}, version={version})"
            if not action_path:
                violations.append(f"{_PREFIX} missing or empty action_path {tag}")
                continue
            if Path(action_path).is_absolute():
                violations.append(f"{_PREFIX} action_path must be relative: {action_path!r} {tag}")
                continue
            resolved = (skill_root / action_path).resolve()
            if not resolved.is_relative_to(skill_root_resolved):
                violations.append(f"{_PREFIX} action_path escapes skill root: {action_path!r} {tag}")
                continue
            if not resolved.exists():
                violations.append(f"{_PREFIX} missing action_path: {action_path} {tag}")
    return violations


def main() -> int:
    violations = check_manifest(MANIFEST_PATH, SKILL_ROOT)
    if not violations:
        print(f"{_PREFIX} all action_path entries resolve to existing files")
        return 0
    for v in violations:
        print(v, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
