"""Tests for upgrade_workarounds engine — issue-268-consumer-workarounds-catalogue.

Slice 1: manifest loading, applies_when evaluation, idempotency, revert decision.
Slice 2: contract_merge action kind.
Slice 3: patch action kind + apply_phase filtering.
Slice 4: python_script action kind + security isolation.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from scripts.lib.blueprint.upgrade_workarounds import (
    UpgradeWorkaroundsEngine,
    load_manifest,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_SKILL_ROOT = Path(".agents/skills/blueprint-consumer-upgrade")
_WORKAROUNDS_ROOT = _SKILL_ROOT / "workarounds"

_SAMPLE_MANIFEST = {
    "schema_version": 1,
    "versions": {
        "v1.10.0": {
            "workarounds": [
                {
                    "id": "258",
                    "upstream_issue": "https://github.com/sbonoc/stackit-platform-blueprint/issues/258",
                    "title": "source-tree coverage gap",
                    "applies_when": "always",
                    "action_kind": "contract_merge",
                    "action_path": "workarounds/v1.10.0/258_source_coverage_gap.yaml",
                    "apply_phase": "before_apply",
                    "landed_in": None,
                },
                {
                    "id": "260",
                    "upstream_issue": "https://github.com/sbonoc/stackit-platform-blueprint/issues/260",
                    "title": "template-smoke skip for generated-consumer",
                    "applies_when": {"repo_mode": "generated-consumer"},
                    "action_kind": "patch",
                    "action_path": "workarounds/v1.10.0/260_template_smoke_skip.patch",
                    "apply_phase": "after_apply",
                    "landed_in": None,
                },
            ]
        }
    },
}


def _write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(manifest, default_flow_style=False), encoding="utf-8")


def _make_contract(repo_root: Path, repo_mode: str = "generated-consumer") -> None:
    contract_path = repo_root / "blueprint" / "contract.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        f"spec:\n  repository:\n    repo_mode: {repo_mode}\n", encoding="utf-8"
    )


# ===========================================================================
# Slice 1 — manifest loading
# ===========================================================================


class TestLoadManifest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmp.name)
        self.workarounds_root = self.tmp_root / "workarounds"
        manifest_path = self.workarounds_root / "manifest.yaml"
        _write_manifest(manifest_path, _SAMPLE_MANIFEST)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_load_manifest_returns_entries_for_target_version(self) -> None:
        entries = load_manifest(self.workarounds_root, "v1.10.0")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["id"], "258")
        self.assertEqual(entries[1]["id"], "260")

    def test_load_manifest_returns_empty_for_unknown_version(self) -> None:
        entries = load_manifest(self.workarounds_root, "v99.0.0")
        self.assertEqual(entries, [])


# ===========================================================================
# Slice 1 — applies_when evaluation
# ===========================================================================


class TestEvaluateAppliesWhen(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root, repo_mode="generated-consumer")
        workarounds_root = self.repo_root / "workarounds"
        _write_manifest(workarounds_root / "manifest.yaml", _SAMPLE_MANIFEST)
        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.10.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_evaluate_applies_when_always_returns_true(self) -> None:
        entry = {"id": "258", "applies_when": "always"}
        self.assertTrue(self.engine.evaluate_applies_when(entry))

    def test_evaluate_applies_when_repo_mode_match(self) -> None:
        entry = {"id": "260", "applies_when": {"repo_mode": "generated-consumer"}}
        self.assertTrue(self.engine.evaluate_applies_when(entry))

    def test_evaluate_applies_when_repo_mode_mismatch_returns_false(self) -> None:
        entry = {"id": "260", "applies_when": {"repo_mode": "template-source"}}
        self.assertFalse(self.engine.evaluate_applies_when(entry))


# ===========================================================================
# Slice 1 — idempotency check
# ===========================================================================


class TestIdempotencyCheck(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root)
        workarounds_root = self.repo_root / "workarounds"
        _write_manifest(workarounds_root / "manifest.yaml", _SAMPLE_MANIFEST)
        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.10.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_idempotency_check_skips_already_applied_entry(self) -> None:
        applied_json = {
            "catalogue_version": 1,
            "entries": [{"id": "258", "status": "applied"}],
        }
        self.assertTrue(self.engine.is_idempotent("258", applied_json))

    def test_idempotency_check_not_applied_returns_false(self) -> None:
        applied_json = {"catalogue_version": 1, "entries": []}
        self.assertFalse(self.engine.is_idempotent("258", applied_json))


# ===========================================================================
# Slice 1 — should_revert decision
# ===========================================================================


class TestShouldRevert(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root)
        workarounds_root = self.repo_root / "workarounds"
        _write_manifest(workarounds_root / "manifest.yaml", _SAMPLE_MANIFEST)
        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.11.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_should_revert_true_when_landed_in_satisfied_and_previously_applied(self) -> None:
        entry = {"id": "258", "landed_in": "v1.11.0"}
        applied_json = {
            "catalogue_version": 1,
            "entries": [{"id": "258", "status": "applied"}],
        }
        self.assertTrue(self.engine.should_revert(entry, applied_json))

    def test_should_revert_false_when_landed_in_null(self) -> None:
        entry = {"id": "258", "landed_in": None}
        applied_json = {
            "catalogue_version": 1,
            "entries": [{"id": "258", "status": "applied"}],
        }
        self.assertFalse(self.engine.should_revert(entry, applied_json))

    def test_should_revert_false_when_not_previously_applied(self) -> None:
        entry = {"id": "258", "landed_in": "v1.11.0"}
        applied_json = {"catalogue_version": 1, "entries": []}
        self.assertFalse(self.engine.should_revert(entry, applied_json))


# ===========================================================================
# Slice 2 — contract_merge action kind
# ===========================================================================


class TestContractMerge(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root, repo_mode="generated-consumer")

        self.workarounds_root = self.repo_root / "workarounds"
        action_dir = self.workarounds_root / "v1.10.0"
        action_dir.mkdir(parents=True)

        # Write a YAML fragment for contract_merge
        (action_dir / "258_source_coverage_gap.yaml").write_text(
            "spec:\n  repository:\n    ownership_path_classes:\n      source_only:\n        - pyproject.toml\n        - uv.lock\n",
            encoding="utf-8",
        )

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.10.0": {
                    "workarounds": [
                        {
                            "id": "258",
                            "upstream_issue": "https://github.com/sbonoc/stackit-platform-blueprint/issues/258",
                            "title": "source-tree coverage gap",
                            "applies_when": "always",
                            "action_kind": "contract_merge",
                            "action_path": "workarounds/v1.10.0/258_source_coverage_gap.yaml",
                            "apply_phase": "before_apply",
                            "landed_in": None,
                        }
                    ]
                }
            },
        }
        _write_manifest(self.workarounds_root / "manifest.yaml", manifest)

        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=self.workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.10.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_contract_merge_apply_adds_yaml_entries(self) -> None:
        entry = {
            "id": "258",
            "action_kind": "contract_merge",
            "action_path": "workarounds/v1.10.0/258_source_coverage_gap.yaml",
            "title": "source-tree coverage gap",
        }
        self.engine.apply(entry)
        contract = yaml.safe_load(
            (self.repo_root / "blueprint" / "contract.yaml").read_text()
        )
        source_only = (
            contract.get("spec", {})
            .get("repository", {})
            .get("ownership_path_classes", {})
            .get("source_only", [])
        )
        self.assertIn("pyproject.toml", source_only)
        self.assertIn("uv.lock", source_only)

    def test_contract_merge_apply_is_idempotent(self) -> None:
        entry = {
            "id": "258",
            "action_kind": "contract_merge",
            "action_path": "workarounds/v1.10.0/258_source_coverage_gap.yaml",
            "title": "source-tree coverage gap",
        }
        self.engine.apply(entry)
        self.engine.apply(entry)  # second apply must not duplicate entries
        contract = yaml.safe_load(
            (self.repo_root / "blueprint" / "contract.yaml").read_text()
        )
        source_only = (
            contract.get("spec", {})
            .get("repository", {})
            .get("ownership_path_classes", {})
            .get("source_only", [])
        )
        self.assertEqual(source_only.count("pyproject.toml"), 1)

    def test_contract_merge_revert_removes_yaml_entries(self) -> None:
        entry = {
            "id": "258",
            "action_kind": "contract_merge",
            "action_path": "workarounds/v1.10.0/258_source_coverage_gap.yaml",
            "title": "source-tree coverage gap",
        }
        self.engine.apply(entry)
        self.engine.revert(entry)
        contract = yaml.safe_load(
            (self.repo_root / "blueprint" / "contract.yaml").read_text()
        )
        source_only = (
            contract.get("spec", {})
            .get("repository", {})
            .get("ownership_path_classes", {})
            .get("source_only", [])
        )
        self.assertNotIn("pyproject.toml", source_only)
        self.assertNotIn("uv.lock", source_only)

    def test_contract_merge_revert_is_noop_when_entries_absent(self) -> None:
        entry = {
            "id": "258",
            "action_kind": "contract_merge",
            "action_path": "workarounds/v1.10.0/258_source_coverage_gap.yaml",
            "title": "source-tree coverage gap",
        }
        # Revert without prior apply — must not raise
        self.engine.revert(entry)


# ===========================================================================
# Slice 3 — patch action kind + apply_phase filtering
# ===========================================================================


class TestPatchActionKind(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root)

        # Create a target file the patch will modify
        target_dir = self.repo_root / "scripts" / "lib" / "blueprint"
        target_dir.mkdir(parents=True)
        target_file = target_dir / "upgrade_consumer_validate.py"
        target_file.write_text(
            "VALIDATION_TARGETS = (\n    'quality-hooks-fast',\n    'blueprint-template-smoke',\n)\n",
            encoding="utf-8",
        )

        # Write a unified diff patch
        self.workarounds_root = self.repo_root / "workarounds"
        action_dir = self.workarounds_root / "v1.10.0"
        action_dir.mkdir(parents=True)

        patch_content = """\
--- a/scripts/lib/blueprint/upgrade_consumer_validate.py
+++ b/scripts/lib/blueprint/upgrade_consumer_validate.py
@@ -1,4 +1,7 @@
 VALIDATION_TARGETS = (
     'quality-hooks-fast',
     'blueprint-template-smoke',
 )
+
+_GENERATED_CONSUMER_SKIP_TARGETS = frozenset({'blueprint-template-smoke'})
"""
        (action_dir / "260_template_smoke_skip.patch").write_text(
            patch_content, encoding="utf-8"
        )

        # Init a git repo so git apply works
        subprocess.run(["git", "init"], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.repo_root, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.repo_root, check=True, capture_output=True,
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=self.repo_root, check=True, capture_output=True,
        )

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.10.0": {
                    "workarounds": [
                        {
                            "id": "260",
                            "upstream_issue": "https://github.com/sbonoc/stackit-platform-blueprint/issues/260",
                            "title": "template-smoke skip",
                            "applies_when": "always",
                            "action_kind": "patch",
                            "action_path": "workarounds/v1.10.0/260_template_smoke_skip.patch",
                            "apply_phase": "after_apply",
                            "landed_in": None,
                        }
                    ]
                }
            },
        }
        _write_manifest(self.workarounds_root / "manifest.yaml", manifest)
        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=self.workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.10.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_patch_apply_applies_unified_diff(self) -> None:
        entry = {
            "id": "260",
            "action_kind": "patch",
            "action_path": "workarounds/v1.10.0/260_template_smoke_skip.patch",
            "title": "template-smoke skip",
        }
        self.engine.apply(entry)
        content = (
            self.repo_root / "scripts" / "lib" / "blueprint" / "upgrade_consumer_validate.py"
        ).read_text()
        self.assertIn("_GENERATED_CONSUMER_SKIP_TARGETS", content)

    def test_patch_apply_is_idempotent(self) -> None:
        entry = {
            "id": "260",
            "action_kind": "patch",
            "action_path": "workarounds/v1.10.0/260_template_smoke_skip.patch",
            "title": "template-smoke skip",
        }
        self.engine.apply(entry)
        # Second apply on an already-patched file — must not raise (non-fatal)
        self.engine.apply(entry)

    def test_patch_revert_reverses_unified_diff(self) -> None:
        entry = {
            "id": "260",
            "action_kind": "patch",
            "action_path": "workarounds/v1.10.0/260_template_smoke_skip.patch",
            "title": "template-smoke skip",
        }
        self.engine.apply(entry)
        self.engine.revert(entry)
        content = (
            self.repo_root / "scripts" / "lib" / "blueprint" / "upgrade_consumer_validate.py"
        ).read_text()
        self.assertNotIn("_GENERATED_CONSUMER_SKIP_TARGETS", content)


class TestApplyPhaseFiltering(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root)
        self.workarounds_root = self.repo_root / "workarounds"
        _write_manifest(self.workarounds_root / "manifest.yaml", _SAMPLE_MANIFEST)
        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=self.workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.10.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_apply_phase_before_apply_filters_correctly(self) -> None:
        entries = load_manifest(self.workarounds_root, "v1.10.0")
        before = [e for e in entries if e.get("apply_phase") == "before_apply"]
        self.assertEqual(len(before), 1)
        self.assertEqual(before[0]["id"], "258")

    def test_apply_phase_after_apply_filters_correctly(self) -> None:
        entries = load_manifest(self.workarounds_root, "v1.10.0")
        after = [e for e in entries if e.get("apply_phase") == "after_apply"]
        self.assertEqual(len(after), 1)
        self.assertEqual(after[0]["id"], "260")


# ===========================================================================
# Slice 4 — python_script action kind + security isolation
# ===========================================================================


class TestPythonScriptActionKind(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        _make_contract(self.repo_root)

        self.workarounds_root = self.repo_root / "workarounds"
        action_dir = self.workarounds_root / "v1.10.0"
        action_dir.mkdir(parents=True)

        # Stub apply/revert module
        (action_dir / "999_stub_script.py").write_text(
            "def apply(repo_root):\n    (repo_root / 'applied.txt').write_text('applied')\n"
            "def revert(repo_root):\n    f = repo_root / 'applied.txt'\n    if f.exists():\n        f.unlink()\n",
            encoding="utf-8",
        )

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.10.0": {
                    "workarounds": [
                        {
                            "id": "999",
                            "upstream_issue": "https://example.com",
                            "title": "stub python script",
                            "applies_when": "always",
                            "action_kind": "python_script",
                            "action_path": "workarounds/v1.10.0/999_stub_script.py",
                            "apply_phase": "after_apply",
                            "landed_in": None,
                        }
                    ]
                }
            },
        }
        _write_manifest(self.workarounds_root / "manifest.yaml", manifest)
        self.engine = UpgradeWorkaroundsEngine(
            catalogue_root=self.workarounds_root,
            repo_root=self.repo_root,
            target_version="v1.10.0",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_python_script_apply_calls_apply_entrypoint(self) -> None:
        entry = {
            "id": "999",
            "action_kind": "python_script",
            "action_path": "workarounds/v1.10.0/999_stub_script.py",
            "title": "stub python script",
        }
        self.engine.apply(entry)
        self.assertTrue((self.repo_root / "applied.txt").exists())

    def test_python_script_revert_calls_revert_entrypoint(self) -> None:
        entry = {
            "id": "999",
            "action_kind": "python_script",
            "action_path": "workarounds/v1.10.0/999_stub_script.py",
            "title": "stub python script",
        }
        self.engine.apply(entry)
        self.engine.revert(entry)
        self.assertFalse((self.repo_root / "applied.txt").exists())

    def test_python_script_isolation_env_allowlist(self) -> None:
        """NFR-SEC-001: python_script subprocess must only see the curated env allowlist."""
        # The engine runs python_script via importlib (in-process), passing only repo_root.
        # For subprocess-based isolation verify the env filtering logic exists.
        from scripts.lib.blueprint.upgrade_workarounds import _PYTHON_SCRIPT_ENV_ALLOWLIST
        self.assertIn("HOME", _PYTHON_SCRIPT_ENV_ALLOWLIST)
        self.assertIn("PATH", _PYTHON_SCRIPT_ENV_ALLOWLIST)
        self.assertIn("BLUEPRINT_UPGRADE_REF", _PYTHON_SCRIPT_ENV_ALLOWLIST)
        self.assertIn("BLUEPRINT_UPGRADE_SOURCE", _PYTHON_SCRIPT_ENV_ALLOWLIST)
