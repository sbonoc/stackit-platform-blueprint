#!/usr/bin/env python3
"""Validate all action_path entries in the workaround catalogue manifest."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / ".agents/skills/blueprint-consumer-upgrade"
MANIFEST_PATH = SKILL_ROOT / "workarounds/manifest.yaml"


def check_manifest(manifest_path: Path, skill_root: Path) -> list[str]:
    if not manifest_path.exists():
        return [f"[quality-workaround-manifest-check] manifest not found: {manifest_path}"]
    content = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    violations = []
    for version, version_data in content.get("versions", {}).items():
        for entry in version_data.get("workarounds", []):
            action_path = entry.get("action_path", "")
            if not (skill_root / action_path).exists():
                violations.append(
                    f"[quality-workaround-manifest-check] missing action_path: {action_path}"
                    f" (id={entry.get('id', '?')!r}, version={version})"
                )
    return violations


def main() -> int:
    violations = check_manifest(MANIFEST_PATH, SKILL_ROOT)
    if not violations:
        print("[quality-workaround-manifest-check] all action_path entries resolve to existing files")
        return 0
    for v in violations:
        print(v, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
