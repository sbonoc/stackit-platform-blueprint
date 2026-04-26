"""Stage 1b: Version pin diff for the scripted upgrade pipeline (Issue #164).

Compares scripts/lib/infra/versions.sh between the baseline blueprint tag and
the target tag, emitting artifacts/blueprint/version_pin_diff.json.

All git operations are local (no HTTP). Errors are isolated — the script always
exits zero so the pipeline continues (FR-005).

Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006,
              NFR-PERF-001, NFR-SEC-001, NFR-OBS-001, NFR-OPS-001.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


_VERSIONS_SH_PATH = "scripts/lib/infra/versions.sh"
_CONTRACT_PATH = "blueprint/contract.yaml"
_ARTIFACT_PATH = "artifacts/blueprint/version_pin_diff.json"
_TEMPLATE_DIR = "scripts/templates/infra/bootstrap"

_VAR_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=["\']?([^"\'#\n]*)["\']?\s*$')


def parse_versions_sh(content: str) -> dict[str, str]:
    """Parse VAR="value" and VAR=value assignments from a versions.sh string."""
    result: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _VAR_RE.match(stripped)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def diff_pins(baseline: dict[str, str], target: dict[str, str]) -> dict:
    """Classify variables as changed / new / removed / unchanged.

    Returns a dict with keys: changed_pins, new_pins, removed_pins, unchanged_count.
    Each pin entry has: variable, old_value, new_value, template_references (empty list).
    """
    changed_pins: list[dict] = []
    new_pins: list[dict] = []
    removed_pins: list[dict] = []
    unchanged_count = 0

    all_vars = set(baseline) | set(target)
    for var in sorted(all_vars):
        old = baseline.get(var)
        new = target.get(var)
        if old is None:
            new_pins.append({"variable": var, "old_value": None, "new_value": new, "template_references": []})
        elif new is None:
            removed_pins.append({"variable": var, "old_value": old, "new_value": None, "template_references": []})
        elif old != new:
            changed_pins.append({"variable": var, "old_value": old, "new_value": new, "template_references": []})
        else:
            unchanged_count += 1

    return {
        "changed_pins": changed_pins,
        "new_pins": new_pins,
        "removed_pins": removed_pins,
        "unchanged_count": unchanged_count,
    }


def scan_template_references(repo_root: Path, variable_names: list[str]) -> dict[str, list[str]]:
    """Return a mapping of variable_name → [file paths] for files referencing each variable."""
    result: dict[str, list[str]] = {var: [] for var in variable_names}
    template_dir = repo_root / _TEMPLATE_DIR
    if not template_dir.exists():
        return result

    for file_path in sorted(template_dir.rglob("*")):
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(file_path.relative_to(repo_root))
        for var in variable_names:
            if var in content:
                result[var].append(rel)

    return result


def _resolve_baseline_ref(source_path: str, template_version: str) -> str | None:
    """Try v{template_version} then {template_version} as git tag candidates.

    Returns the first resolvable candidate, or None if neither works.
    Mirrors upgrade_consumer.py:_resolve_baseline_ref.
    """
    for candidate in (f"v{template_version}", template_version):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            capture_output=True,
            cwd=source_path,
        )
        if result.returncode == 0:
            return candidate
    return None


def run_version_pin_diff(repo_root: Path, upgrade_source: str, upgrade_ref: str) -> bool:
    """Run the version pin diff and write artifacts/blueprint/version_pin_diff.json.

    Always returns True so the pipeline continues regardless of errors (FR-005).
    """
    artifact_path = repo_root / _ARTIFACT_PATH
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_error(msg: str) -> None:
        artifact_path.write_text(
            json.dumps({"error": msg}, indent=2), encoding="utf-8"
        )
        print(f"[PIPELINE] Stage 1b: WARNING — {msg}", file=sys.stderr)

    try:
        contract_path = repo_root / _CONTRACT_PATH
        contract_data = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
        template_version = (
            (contract_data.get("spec") or {})
            .get("repository", {})
            .get("template_bootstrap", {})
            .get("template_version", "")
        )
        if not template_version:
            _write_error("template_version not found in blueprint/contract.yaml")
            return True

        baseline_ref = _resolve_baseline_ref(upgrade_source, str(template_version))
        if baseline_ref is None:
            _write_error(
                f"baseline ref for template_version={template_version!r} could not be resolved "
                f"in {upgrade_source!r}"
            )
            return True

        print(f"[PIPELINE] Stage 1b: diffing {baseline_ref}..{upgrade_ref} for {_VERSIONS_SH_PATH}")

        baseline_content = subprocess.run(
            ["git", "show", f"{baseline_ref}:{_VERSIONS_SH_PATH}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=upgrade_source,
        ).stdout

        target_content = subprocess.run(
            ["git", "show", f"{upgrade_ref}:{_VERSIONS_SH_PATH}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=upgrade_source,
        ).stdout

        baseline_pins = parse_versions_sh(baseline_content)
        target_pins = parse_versions_sh(target_content)
        diff = diff_pins(baseline_pins, target_pins)

        changed_and_new_vars = (
            [p["variable"] for p in diff["changed_pins"]]
            + [p["variable"] for p in diff["new_pins"]]
        )
        refs = scan_template_references(repo_root, changed_and_new_vars)
        for entry in diff["changed_pins"] + diff["new_pins"]:
            entry["template_references"] = refs.get(entry["variable"], [])

        artifact = {
            "baseline_ref": baseline_ref,
            "target_ref": upgrade_ref,
            "changed_pins": diff["changed_pins"],
            "new_pins": diff["new_pins"],
            "removed_pins": diff["removed_pins"],
            "unchanged_count": diff["unchanged_count"],
        }
        artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        print(
            f"[PIPELINE] Stage 1b: {len(diff['changed_pins'])} changed, "
            f"{len(diff['new_pins'])} new, {len(diff['removed_pins'])} removed, "
            f"{diff['unchanged_count']} unchanged"
        )

    except Exception as exc:
        _write_error(str(exc))

    return True


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Stage 1b: version pin diff between baseline and target blueprint tags.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    upgrade_source = os.environ.get("BLUEPRINT_UPGRADE_SOURCE", "")
    upgrade_ref = os.environ.get("BLUEPRINT_UPGRADE_REF", "")

    if not upgrade_source or not upgrade_ref:
        print(
            "[PIPELINE] Stage 1b: FAILED — BLUEPRINT_UPGRADE_SOURCE and BLUEPRINT_UPGRADE_REF are required",
            file=sys.stderr,
        )
        return 1

    run_version_pin_diff(args.repo_root, upgrade_source=upgrade_source, upgrade_ref=upgrade_ref)
    return 0


if __name__ == "__main__":
    sys.exit(main())
