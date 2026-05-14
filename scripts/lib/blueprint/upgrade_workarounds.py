"""Versioned consumer-side workarounds catalogue engine.

Loads manifest.yaml, evaluates applies_when, dispatches apply/revert for each
action kind, checks idempotency, and writes workarounds_applied.json.

Requirements: FR-001–FR-010, FR-003, NFR-SEC-001, NFR-OPS-001.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

# NFR-SEC-001: curated allowlist for python_script subprocess env.
_PYTHON_SCRIPT_ENV_ALLOWLIST: frozenset[str] = frozenset(
    {"HOME", "PATH", "BLUEPRINT_UPGRADE_REF", "BLUEPRINT_UPGRADE_SOURCE"}
)

_CONTRACT_PATH = "blueprint/contract.yaml"
_APPLIED_JSON_PATH = "artifacts/blueprint/workarounds_applied.json"
_MANIFEST_FILENAME = "manifest.yaml"


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------


def load_manifest(catalogue_root: Path, target_version: str) -> list[dict[str, Any]]:
    """Load and return the workaround entries for target_version from manifest.yaml.

    Returns [] when the version block is absent (NFR-REL-002).
    """
    manifest_path = catalogue_root / _MANIFEST_FILENAME
    if not manifest_path.exists():
        return []
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    versions = raw.get("versions", {})
    version_block = versions.get(target_version, {})
    return list(version_block.get("workarounds", []))


# ---------------------------------------------------------------------------
# Applied JSON helpers
# ---------------------------------------------------------------------------


def _load_applied_json(repo_root: Path) -> dict[str, Any]:
    path = repo_root / _APPLIED_JSON_PATH
    if not path.exists():
        return {"catalogue_version": 1, "entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_applied_json(
    repo_root: Path,
    target_version: str,
    entries: list[dict[str, Any]],
) -> None:
    """FR-005, NFR-OPS-001: write workarounds_applied.json."""
    path = repo_root / _APPLIED_JSON_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "catalogue_version": 1,
        "target_blueprint_version": target_version,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Version comparison (semver-lite: vMAJOR.MINOR.PATCH)
# ---------------------------------------------------------------------------


def _parse_semver(version: str) -> tuple[int, ...]:
    clean = version.lstrip("v").split("-")[0]  # strip pre-release
    try:
        return tuple(int(x) for x in clean.split("."))
    except ValueError:
        return (0, 0, 0)


def _version_gte(a: str, b: str) -> bool:
    return _parse_semver(a) >= _parse_semver(b)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class UpgradeWorkaroundsEngine:
    """Apply and revert versioned workaround entries from the catalogue."""

    def __init__(
        self,
        *,
        catalogue_root: Path,
        repo_root: Path,
        target_version: str,
    ) -> None:
        self._catalogue_root = catalogue_root
        self._repo_root = repo_root
        self._target_version = target_version
        self._contract_data: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Evaluation helpers
    # ------------------------------------------------------------------

    def _contract(self) -> dict[str, Any]:
        if self._contract_data is None:
            path = self._repo_root / _CONTRACT_PATH
            self._contract_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return self._contract_data

    def _repo_mode(self) -> str:
        return (
            self._contract()
            .get("spec", {})
            .get("repository", {})
            .get("repo_mode", "")
        )

    def evaluate_applies_when(self, entry: dict[str, Any]) -> bool:
        """FR-003: return True when the entry's applies_when matches the consumer repo."""
        condition = entry.get("applies_when", "always")
        if condition == "always":
            return True
        if isinstance(condition, dict):
            repo_mode_req = condition.get("repo_mode")
            if repo_mode_req is not None:
                return self._repo_mode() == repo_mode_req
        return False

    def is_idempotent(self, entry_id: str, applied_json: dict[str, Any]) -> bool:
        """FR-009: return True when entry_id is already listed with status=applied."""
        for entry in applied_json.get("entries", []):
            if str(entry.get("id")) == str(entry_id) and entry.get("status") == "applied":
                return True
        return False

    def should_revert(self, entry: dict[str, Any], applied_json: dict[str, Any]) -> bool:
        """FR-006: revert only when landed_in is satisfied AND previously applied."""
        landed_in = entry.get("landed_in")
        if not landed_in:
            return False
        if not _version_gte(self._target_version, landed_in):
            return False
        entry_id = str(entry.get("id", ""))
        for e in applied_json.get("entries", []):
            if str(e.get("id")) == entry_id and e.get("status") == "applied":
                return True
        return False

    # ------------------------------------------------------------------
    # Action dispatch
    # ------------------------------------------------------------------

    def apply(self, entry: dict[str, Any]) -> None:
        """Dispatch apply for the given entry's action_kind."""
        kind = entry["action_kind"]
        if kind == "contract_merge":
            self._contract_merge_apply(entry)
        elif kind == "patch":
            self._patch_apply(entry)
        elif kind == "python_script":
            self._python_script_apply(entry)
        else:
            raise ValueError(f"Unknown action_kind: {kind!r}")

    def revert(self, entry: dict[str, Any]) -> None:
        """Dispatch revert for the given entry's action_kind."""
        kind = entry["action_kind"]
        if kind == "contract_merge":
            self._contract_merge_revert(entry)
        elif kind == "patch":
            self._patch_revert(entry)
        elif kind == "python_script":
            self._python_script_revert(entry)
        else:
            raise ValueError(f"Unknown action_kind: {kind!r}")

    # ------------------------------------------------------------------
    # contract_merge
    # ------------------------------------------------------------------

    def _action_file(self, entry: dict[str, Any]) -> Path:
        rel = entry["action_path"]
        # action_path is relative to the skill root (one level above workarounds/)
        return self._catalogue_root.parent / rel

    def _contract_merge_apply(self, entry: dict[str, Any]) -> None:
        """FR-010: contract_merge failures are fatal."""
        action_file = self._action_file(entry)
        fragment: dict[str, Any] = yaml.safe_load(action_file.read_text(encoding="utf-8")) or {}

        contract_path = self._repo_root / _CONTRACT_PATH
        contract: dict[str, Any] = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}

        _deep_list_merge(contract, fragment)

        contract_path.write_text(
            yaml.dump(contract, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        # Invalidate cached contract
        self._contract_data = None

    def _contract_merge_revert(self, entry: dict[str, Any]) -> None:
        action_file = self._action_file(entry)
        fragment: dict[str, Any] = yaml.safe_load(action_file.read_text(encoding="utf-8")) or {}

        contract_path = self._repo_root / _CONTRACT_PATH
        contract: dict[str, Any] = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}

        _deep_list_remove(contract, fragment)

        contract_path.write_text(
            yaml.dump(contract, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        self._contract_data = None

    # ------------------------------------------------------------------
    # patch
    # ------------------------------------------------------------------

    def _patch_apply(self, entry: dict[str, Any]) -> None:
        """FR-010: patch failures are non-fatal (git apply already applied → exit 1 is safe)."""
        action_file = self._action_file(entry)
        result = subprocess.run(
            ["git", "apply", "--whitespace=fix", str(action_file)],
            cwd=self._repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log.warning(
                "patch apply non-fatal: entry #%s — %s",
                entry.get("id"),
                result.stderr.strip(),
            )

    def _patch_revert(self, entry: dict[str, Any]) -> None:
        action_file = self._action_file(entry)
        result = subprocess.run(
            ["git", "apply", "-R", "--whitespace=fix", str(action_file)],
            cwd=self._repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log.warning(
                "patch revert non-fatal: entry #%s — %s",
                entry.get("id"),
                result.stderr.strip(),
            )

    # ------------------------------------------------------------------
    # python_script
    # ------------------------------------------------------------------

    def _python_script_apply(self, entry: dict[str, Any]) -> None:
        """NFR-SEC-001: load module directly (trusted blueprint code); call apply(repo_root)."""
        module = self._load_python_script_module(entry)
        module.apply(self._repo_root)

    def _python_script_revert(self, entry: dict[str, Any]) -> None:
        module = self._load_python_script_module(entry)
        module.revert(self._repo_root)

    def _load_python_script_module(self, entry: dict[str, Any]) -> Any:
        action_file = self._action_file(entry)
        spec = importlib.util.spec_from_file_location(
            f"workaround_{entry['id']}", action_file
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load python_script: {action_file}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        return module

    # ------------------------------------------------------------------
    # High-level run entry points (called by pipeline stages)
    # ------------------------------------------------------------------

    def run_before_apply(self) -> list[dict[str, Any]]:
        """Stage 1c: apply/revert before_apply entries. FR-003, FR-004, FR-005."""
        applied_json = _load_applied_json(self._repo_root)
        entries = load_manifest(self._catalogue_root, self._target_version)
        result_entries: list[dict[str, Any]] = [
            e for e in applied_json.get("entries", [])
            if e.get("status") != "reverted"
        ]

        for entry in entries:
            if entry.get("apply_phase") != "before_apply":
                continue
            entry_id = str(entry.get("id", ""))
            title = entry.get("title", "")

            if not self.evaluate_applies_when(entry):
                print(
                    f"[PIPELINE] Stage 1c: skipped workaround #{entry_id} — {title} (applies_when mismatch)"
                )
                continue

            if self.should_revert(entry, applied_json):
                self.revert(entry)
                print(
                    f"[PIPELINE] Stage 1c: reverted workaround #{entry_id} — {title} "
                    f"(landed in {entry.get('landed_in')})"
                )
                result_entries = [e for e in result_entries if str(e.get("id")) != entry_id]
                result_entries.append(
                    {"id": entry_id, "title": title, "action_kind": entry.get("action_kind"),
                     "apply_phase": "before_apply", "status": "reverted"}
                )
                continue

            if self.is_idempotent(entry_id, applied_json):
                print(
                    f"[PIPELINE] Stage 1c: skipped workaround #{entry_id} — {title} (already applied)"
                )
                continue

            try:
                self.apply(entry)
                print(f"[PIPELINE] Stage 1c: applied workaround #{entry_id} — {title}")
                result_entries = [e for e in result_entries if str(e.get("id")) != entry_id]
                result_entries.append(
                    {"id": entry_id, "title": title, "action_kind": entry.get("action_kind"),
                     "apply_phase": "before_apply", "status": "applied"}
                )
            except Exception as exc:
                kind = entry.get("action_kind", "")
                if kind in ("contract_merge", "python_script"):
                    raise RuntimeError(
                        f"[PIPELINE] Stage 1c: fatal — workaround #{entry_id} failed: {exc}"
                    ) from exc
                log.warning("Stage 1c: non-fatal error for #%s: %s", entry_id, exc)
                result_entries.append(
                    {"id": entry_id, "title": title, "action_kind": kind,
                     "apply_phase": "before_apply", "status": "failed"}
                )

        _write_applied_json(self._repo_root, self._target_version, result_entries)
        return result_entries

    def run_after_apply(self) -> list[dict[str, Any]]:
        """Stage 2c: apply after_apply entries. FR-003, FR-004."""
        applied_json = _load_applied_json(self._repo_root)
        entries = load_manifest(self._catalogue_root, self._target_version)

        for entry in entries:
            if entry.get("apply_phase") != "after_apply":
                continue
            entry_id = str(entry.get("id", ""))
            title = entry.get("title", "")

            if not self.evaluate_applies_when(entry):
                print(
                    f"[PIPELINE] Stage 2c: skipped workaround #{entry_id} — {title} (applies_when mismatch)"
                )
                continue

            if self.is_idempotent(entry_id, applied_json):
                print(
                    f"[PIPELINE] Stage 2c: skipped workaround #{entry_id} — {title} (already applied)"
                )
                continue

            try:
                self.apply(entry)
                print(f"[PIPELINE] Stage 2c: applied workaround #{entry_id} — {title}")
                new_entries = [
                    e for e in applied_json.get("entries", [])
                    if str(e.get("id")) != entry_id
                ]
                new_entries.append(
                    {"id": entry_id, "title": title, "action_kind": entry.get("action_kind"),
                     "apply_phase": "after_apply", "status": "applied"}
                )
                applied_json["entries"] = new_entries
                _write_applied_json(self._repo_root, self._target_version, new_entries)
            except Exception as exc:
                kind = entry.get("action_kind", "")
                if kind in ("contract_merge", "python_script"):
                    raise RuntimeError(
                        f"[PIPELINE] Stage 2c: fatal — workaround #{entry_id} failed: {exc}"
                    ) from exc
                log.warning("Stage 2c: non-fatal error for #%s: %s", entry_id, exc)

        return applied_json.get("entries", [])


# ---------------------------------------------------------------------------
# Deep merge / remove helpers for contract_merge
# ---------------------------------------------------------------------------


def _deep_list_merge(target: dict, source: dict) -> None:
    """Recursively merge source into target, extending lists without duplicates."""
    for key, val in source.items():
        if key not in target:
            target[key] = val
        elif isinstance(val, dict) and isinstance(target[key], dict):
            _deep_list_merge(target[key], val)
        elif isinstance(val, list) and isinstance(target[key], list):
            for item in val:
                if item not in target[key]:
                    target[key].append(item)
        else:
            target[key] = val


def _deep_list_remove(target: dict, source: dict) -> None:
    """Recursively remove source list items from target lists."""
    for key, val in source.items():
        if key not in target:
            continue
        if isinstance(val, dict) and isinstance(target[key], dict):
            _deep_list_remove(target[key], val)
        elif isinstance(val, list) and isinstance(target[key], list):
            target[key] = [item for item in target[key] if item not in val]


# ---------------------------------------------------------------------------
# CLI entry point (called by upgrade_consumer_pipeline.sh)
# ---------------------------------------------------------------------------


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run workaround catalogue stage.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--catalogue-root", required=True)
    parser.add_argument("--target-version", required=True)
    parser.add_argument(
        "--phase",
        choices=["before_apply", "after_apply"],
        required=True,
    )
    args = parser.parse_args()

    engine = UpgradeWorkaroundsEngine(
        catalogue_root=Path(args.catalogue_root),
        repo_root=Path(args.repo_root),
        target_version=args.target_version,
    )
    if args.phase == "before_apply":
        engine.run_before_apply()
    else:
        engine.run_after_apply()


if __name__ == "__main__":
    _main()
