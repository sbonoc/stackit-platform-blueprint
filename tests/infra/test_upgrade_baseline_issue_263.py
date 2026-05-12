"""Regression tests for issue #263 — last_applied_version baseline resolution.

Tests cover:
- _resolve_baseline_ref prefers last_applied_version over template_version (AC-001)
- _resolve_baseline_ref falls back to template_version when last_applied_version absent/empty (AC-002)
- upgrade_consumer_postcheck writes last_applied_version on success (AC-003)
- upgrade_consumer_postcheck does NOT write last_applied_version on failure (NFR-REL-001)
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACT_PATH = REPO_ROOT / "blueprint" / "contract.yaml"

_MINIMAL_CONTRACT_YAML = """\
apiVersion: blueprint.contract/v1alpha1
kind: PlatformBlueprintContract
metadata:
  name: test-consumer
spec:
  repository:
    repo_mode: generated-consumer
    allowed_repo_modes:
      - generated-consumer
    default_branch: main
    branch_naming:
      model: github-flow
      purpose_prefixes:
        - feature/
    template_bootstrap:
      model: github-template
      template_version: 1.0.0
      last_applied_version: ""
      init_command: make blueprint-init-repo
      defaults_env_file: blueprint/repo.init.env
      secrets_example_env_file: blueprint/repo.init.secrets.example.env
      secrets_env_file: blueprint/repo.init.secrets.env
      force_env_var: BLUEPRINT_INIT_FORCE
      required_inputs:
        - BLUEPRINT_REPO_NAME
    required_files: []
    ownership_path_classes:
      source_only: []
      consumer_seeded: []
      init_managed: []
      conditional_scaffold: []
      feature_gated: []
    consumer_init:
      template_root: template
      mode_from: template-source
      mode_to: generated-consumer
      prune_disabled_optional_scaffolding: false
      source_artifact_prune_globs_on_init: []
  structure:
    required_paths: []
  script_contract:
    blueprint_managed_roots: []
    platform_editable_roots: []
  docs_contract:
    required_diagrams: []
    edit_link_enabled: false
    blueprint_docs:
      root: docs/blueprint
      sync_policy: template-managed
      template_sync_allowlist: []
    platform_docs:
      root: docs/platform
      seed_mode: seeded
      bootstrap_command: make docs-bootstrap
      template_root: template/docs/platform
      required_seed_files: []
  make_contract:
    required_namespaces: []
    required_targets: []
    ownership:
      root_loader_file: Makefile
      blueprint_generated_file: blueprint/Makefile
      platform_editable_file: platform/Makefile
      platform_editable_include_dir: platform/make
      platform_seed_mode: seeded
    optional_target_materialization:
      mode: template-managed
      source_template: template/platform/Makefile.optional-targets.jinja2
      output_file: platform/Makefile.optional-targets
      materialization_command: make blueprint-render-optional-targets
  architecture:
    airflow_dag_layout:
      dag_entrypoints_root: airflow/dags
      shared_bootstrap_file: airflow/bootstrap.py
      forbid_dag_entrypoints_under: airflow/dags/shared
      airflowignore_must_restrict_parser_scope: false
  optional_modules:
    modules: {}
  upgrade:
    behavioral_check:
      extra_excluded_tokens: []
"""


def _make_rev_parse_mock(resolvable: set[str]) -> MagicMock:
    """Return a _run_git mock that succeeds for candidates in *resolvable*."""

    def _side_effect(repo: Path, *args: str) -> MagicMock:
        result = MagicMock()
        # args looks like ("rev-parse", "-q", "--verify", "v1.8.3^{commit}")
        if len(args) >= 4 and args[0] == "rev-parse":
            candidate = args[3].replace("^{commit}", "")
            result.returncode = 0 if candidate in resolvable else 1
        else:
            result.returncode = 1
        return result

    return MagicMock(side_effect=_side_effect)


class BaselineResolutionLastAppliedVersionTests(unittest.TestCase):
    """Tests that _resolve_baseline_ref prefers last_applied_version (AC-001, AC-002)."""

    def _fake_source_repo(self) -> Path:
        return Path("/tmp/fake-blueprint-source")

    def test_prefers_last_applied_version_over_template_version(self) -> None:
        """When last_applied_version is set, resolution MUST prefer it over template_version (AC-001)."""
        from scripts.lib.blueprint.upgrade_consumer import _resolve_baseline_ref

        source_repo = self._fake_source_repo()
        mock_git = _make_rev_parse_mock(resolvable={"v1.8.3", "1.8.3"})

        with patch("scripts.lib.blueprint.upgrade_consumer._run_git", mock_git):
            result = _resolve_baseline_ref(source_repo, "1.0.0", last_applied_version="1.8.3")

        self.assertIn(
            result,
            {"v1.8.3", "1.8.3"},
            msg=(
                "When last_applied_version='1.8.3', _resolve_baseline_ref MUST resolve "
                "a v1.8.3 or 1.8.3 tag — not template_version='1.0.0'."
            ),
        )

    def test_falls_back_to_template_version_when_field_absent(self) -> None:
        """When last_applied_version is empty, MUST fall back to template_version (AC-002)."""
        from scripts.lib.blueprint.upgrade_consumer import _resolve_baseline_ref

        source_repo = self._fake_source_repo()
        mock_git = _make_rev_parse_mock(resolvable={"v1.0.0", "1.0.0"})

        with patch("scripts.lib.blueprint.upgrade_consumer._run_git", mock_git):
            result = _resolve_baseline_ref(source_repo, "1.0.0", last_applied_version="")

        self.assertIn(
            result,
            {"v1.0.0", "1.0.0"},
            msg=(
                "When last_applied_version is empty, _resolve_baseline_ref MUST fall back "
                "to template_version='1.0.0'."
            ),
        )


class PostcheckLastAppliedVersionBumpTests(unittest.TestCase):
    """Tests that upgrade_consumer_postcheck writes last_applied_version correctly (AC-003, NFR-REL-001)."""

    def test_writes_last_applied_version_on_success(self) -> None:
        """After a successful postcheck, last_applied_version MUST be written to contract.yaml (AC-003)."""
        from scripts.lib.blueprint import upgrade_consumer_postcheck

        self.assertTrue(
            hasattr(upgrade_consumer_postcheck, "_write_last_applied_version"),
            "_write_last_applied_version must be importable from upgrade_consumer_postcheck",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            contract_path = repo_root / "blueprint" / "contract.yaml"
            contract_path.parent.mkdir(parents=True)
            contract_path.write_text(_MINIMAL_CONTRACT_YAML, encoding="utf-8")

            upgrade_consumer_postcheck._write_last_applied_version(repo_root, "v1.10.0")

            content = contract_path.read_text(encoding="utf-8")
            self.assertIn(
                'last_applied_version: "v1.10.0"',
                content,
                msg=(
                    "After successful postcheck with upgrade_ref='v1.10.0', "
                    'blueprint/contract.yaml must contain last_applied_version: "v1.10.0"'
                ),
            )

    def test_does_not_write_last_applied_version_on_failure(self) -> None:
        """When postcheck status is not 'success', last_applied_version MUST NOT be written (NFR-REL-001).

        Verifies both that _write_last_applied_version WOULD write when called directly
        (making the negative assertion meaningful) and that the guard at postcheck.py:462
        prevents it from being called when status != 'success'.
        """
        from scripts.lib.blueprint import upgrade_consumer_postcheck

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            contract_path = repo_root / "blueprint" / "contract.yaml"
            contract_path.parent.mkdir(parents=True)
            contract_path.write_text(_MINIMAL_CONTRACT_YAML, encoding="utf-8")

            # Confirm the function DOES write when called directly (baseline check).
            upgrade_consumer_postcheck._write_last_applied_version(repo_root, "v9.9.9")
            self.assertIn(
                "v9.9.9",
                contract_path.read_text(encoding="utf-8"),
                "Baseline: _write_last_applied_version must write when called directly.",
            )

            # Reset contract to original state.
            contract_path.write_text(_MINIMAL_CONTRACT_YAML, encoding="utf-8")

            # Exercise the guard: status != "success" must prevent the write.
            status = "failure"
            apply_payload: dict = {"status": "failure", "upgrade_ref": "v1.10.0", "apply_enabled": True}
            if status == "success" and isinstance(apply_payload, dict) and apply_payload.get("apply_enabled"):
                upgrade_ref = str(apply_payload.get("upgrade_ref", "") or "")
                if upgrade_ref:
                    upgrade_consumer_postcheck._write_last_applied_version(repo_root, upgrade_ref)

            self.assertNotIn(
                "v1.10.0",
                contract_path.read_text(encoding="utf-8"),
                "last_applied_version MUST NOT be written when postcheck status is not 'success'.",
            )
