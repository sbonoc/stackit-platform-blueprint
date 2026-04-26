"""Tests for upgrade_version_pin_diff.py (Issue #164).

Slice 1: parse / diff / scan / resolve (unit, no git)
  TestParseVersionsSh         — FR-002
  TestDiffPins                — FR-002
  TestScanTemplateReferences  — FR-003
  TestResolveBaselineRef      — FR-001

Slice 2: run_version_pin_diff integration boundary (mocked git)
  TestRunVersionPinDiff       — FR-001, FR-004, FR-005, NFR-OPS-001

Error path:
  TestGitErrorIsolation       — FR-005, AC-005
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.lib.blueprint.upgrade_version_pin_diff import (
    _resolve_baseline_ref,
    diff_pins,
    parse_versions_sh,
    run_version_pin_diff,
    scan_template_references,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_BASELINE_VERSIONS_SH = """\
TERRAFORM_VERSION="1.12.0"
HELM_VERSION="4.1.3"
KUBECTL_VERSION="1.34.1"
OLD_TOOL_VERSION="0.9.0"
# a comment
SHARED_VERSION=stable
"""

_TARGET_VERSIONS_SH = """\
TERRAFORM_VERSION="1.13.3"
HELM_VERSION="4.1.3"
KUBECTL_VERSION="1.34.1"
NEW_TOOL_VERSION="2.0.0"
# a comment
SHARED_VERSION=stable
"""


# ===========================================================================
# Slice 1 — parse_versions_sh
# ===========================================================================


class TestParseVersionsSh(unittest.TestCase):
    """FR-002: parse VAR="value" and VAR=value forms; skip comments and blanks."""

    def test_quoted_values_parsed(self) -> None:
        result = parse_versions_sh('TERRAFORM_VERSION="1.13.3"\n')
        self.assertEqual(result["TERRAFORM_VERSION"], "1.13.3")

    def test_unquoted_values_parsed(self) -> None:
        result = parse_versions_sh("SHARED_VERSION=stable\n")
        self.assertEqual(result["SHARED_VERSION"], "stable")

    def test_comments_skipped(self) -> None:
        result = parse_versions_sh("# this is a comment\nFOO=bar\n")
        self.assertNotIn("# this is a comment", result)
        self.assertIn("FOO", result)

    def test_blank_lines_skipped(self) -> None:
        result = parse_versions_sh("\n\nFOO=bar\n\n")
        self.assertEqual(list(result.keys()), ["FOO"])

    def test_full_fixture_parsed(self) -> None:
        result = parse_versions_sh(_BASELINE_VERSIONS_SH)
        self.assertEqual(result["TERRAFORM_VERSION"], "1.12.0")
        self.assertEqual(result["HELM_VERSION"], "4.1.3")
        self.assertEqual(result["KUBECTL_VERSION"], "1.34.1")
        self.assertEqual(result["OLD_TOOL_VERSION"], "0.9.0")
        self.assertEqual(result["SHARED_VERSION"], "stable")
        self.assertEqual(len(result), 5)


# ===========================================================================
# Slice 1 — diff_pins
# ===========================================================================


class TestDiffPins(unittest.TestCase):
    """FR-002: classify variables as changed / new / removed / unchanged."""

    def setUp(self) -> None:
        self.baseline = parse_versions_sh(_BASELINE_VERSIONS_SH)
        self.target = parse_versions_sh(_TARGET_VERSIONS_SH)

    def test_changed_pin_detected(self) -> None:
        result = diff_pins(self.baseline, self.target)
        changed_vars = [p["variable"] for p in result["changed_pins"]]
        self.assertIn("TERRAFORM_VERSION", changed_vars)

    def test_changed_pin_old_and_new_value(self) -> None:
        result = diff_pins(self.baseline, self.target)
        tf = next(p for p in result["changed_pins"] if p["variable"] == "TERRAFORM_VERSION")
        self.assertEqual(tf["old_value"], "1.12.0")
        self.assertEqual(tf["new_value"], "1.13.3")

    def test_new_pin_detected(self) -> None:
        result = diff_pins(self.baseline, self.target)
        new_vars = [p["variable"] for p in result["new_pins"]]
        self.assertIn("NEW_TOOL_VERSION", new_vars)

    def test_new_pin_old_value_is_none(self) -> None:
        result = diff_pins(self.baseline, self.target)
        new = next(p for p in result["new_pins"] if p["variable"] == "NEW_TOOL_VERSION")
        self.assertIsNone(new["old_value"])
        self.assertEqual(new["new_value"], "2.0.0")

    def test_removed_pin_detected(self) -> None:
        result = diff_pins(self.baseline, self.target)
        removed_vars = [p["variable"] for p in result["removed_pins"]]
        self.assertIn("OLD_TOOL_VERSION", removed_vars)

    def test_removed_pin_new_value_is_none(self) -> None:
        result = diff_pins(self.baseline, self.target)
        removed = next(p for p in result["removed_pins"] if p["variable"] == "OLD_TOOL_VERSION")
        self.assertEqual(removed["old_value"], "0.9.0")
        self.assertIsNone(removed["new_value"])

    def test_unchanged_count(self) -> None:
        result = diff_pins(self.baseline, self.target)
        # HELM_VERSION, KUBECTL_VERSION, SHARED_VERSION are unchanged
        self.assertEqual(result["unchanged_count"], 3)

    def test_unchanged_vars_not_in_changed_list(self) -> None:
        result = diff_pins(self.baseline, self.target)
        changed_vars = [p["variable"] for p in result["changed_pins"]]
        self.assertNotIn("HELM_VERSION", changed_vars)

    def test_template_references_initialised_empty(self) -> None:
        result = diff_pins(self.baseline, self.target)
        for entry in result["changed_pins"] + result["new_pins"] + result["removed_pins"]:
            self.assertIn("template_references", entry)
            self.assertIsInstance(entry["template_references"], list)


# ===========================================================================
# Slice 1 — scan_template_references
# ===========================================================================


class TestScanTemplateReferences(unittest.TestCase):
    """FR-003: scan scripts/templates/infra/bootstrap/ for variable name references."""

    def test_variable_reference_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            template_dir = repo_root / "scripts/templates/infra/bootstrap"
            template_dir.mkdir(parents=True)
            (template_dir / "main.yaml").write_text(
                "image: ${TERRAFORM_VERSION}\n", encoding="utf-8"
            )

            result = scan_template_references(repo_root, ["TERRAFORM_VERSION"])

            self.assertIn("TERRAFORM_VERSION", result)
            refs = result["TERRAFORM_VERSION"]
            self.assertEqual(len(refs), 1)
            self.assertIn("main.yaml", refs[0])

    def test_variable_not_referenced_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            template_dir = repo_root / "scripts/templates/infra/bootstrap"
            template_dir.mkdir(parents=True)
            (template_dir / "other.yaml").write_text("image: alpine\n", encoding="utf-8")

            result = scan_template_references(repo_root, ["TERRAFORM_VERSION"])

            self.assertEqual(result["TERRAFORM_VERSION"], [])

    def test_absent_template_dir_returns_empty_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            result = scan_template_references(repo_root, ["TERRAFORM_VERSION", "HELM_VERSION"])

            self.assertEqual(result["TERRAFORM_VERSION"], [])
            self.assertEqual(result["HELM_VERSION"], [])

    def test_multiple_files_referencing_same_variable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            template_dir = repo_root / "scripts/templates/infra/bootstrap"
            template_dir.mkdir(parents=True)
            (template_dir / "a.yaml").write_text("TERRAFORM_VERSION: x\n", encoding="utf-8")
            (template_dir / "b.yaml").write_text("TERRAFORM_VERSION: y\n", encoding="utf-8")

            result = scan_template_references(repo_root, ["TERRAFORM_VERSION"])

            self.assertEqual(len(result["TERRAFORM_VERSION"]), 2)


# ===========================================================================
# Slice 1 — _resolve_baseline_ref
# ===========================================================================


class TestResolveBaselineRef(unittest.TestCase):
    """FR-001: resolve template_version string → git tag (try v{ver} then {ver})."""

    def test_v_prefixed_tag_resolved(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0)
            with tempfile.TemporaryDirectory() as tmpdir:
                result = _resolve_baseline_ref(tmpdir, "1.0.0")
            self.assertEqual(result, "v1.0.0")
            mock_run.assert_called_once()

    def test_bare_tag_resolved_when_v_prefix_fails(self) -> None:
        def _side_effect(cmd, **kwargs):
            if "v1.0.0" in cmd:
                return mock.Mock(returncode=1)
            return mock.Mock(returncode=0)

        with mock.patch("subprocess.run", side_effect=_side_effect):
            with tempfile.TemporaryDirectory() as tmpdir:
                result = _resolve_baseline_ref(tmpdir, "1.0.0")
        self.assertEqual(result, "1.0.0")

    def test_returns_none_when_both_candidates_fail(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=1)
            with tempfile.TemporaryDirectory() as tmpdir:
                result = _resolve_baseline_ref(tmpdir, "1.0.0")
        self.assertIsNone(result)


# ===========================================================================
# Slice 2 — run_version_pin_diff (integration boundary, mocked git)
# ===========================================================================


class TestRunVersionPinDiff(unittest.TestCase):
    """FR-001, FR-004, NFR-OPS-001: mocked git → correct JSON artifact written."""

    def _make_contract(self, repo_root: Path, template_version: str = "1.0.0") -> None:
        contract_dir = repo_root / "blueprint"
        contract_dir.mkdir(parents=True, exist_ok=True)
        (contract_dir / "contract.yaml").write_text(
            f"spec:\n  repository:\n    template_bootstrap:\n      template_version: \"{template_version}\"\n",
            encoding="utf-8",
        )

    def test_json_artifact_written_with_expected_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._make_contract(repo_root)
            (repo_root / "artifacts/blueprint").mkdir(parents=True)

            def _git_show(cmd, **kwargs):
                if "v1.0.0" in cmd or "1.0.0" in cmd:
                    return mock.Mock(returncode=0, stdout=_BASELINE_VERSIONS_SH)
                return mock.Mock(returncode=0, stdout=_TARGET_VERSIONS_SH)

            with mock.patch("subprocess.run") as mock_run:
                mock_run.side_effect = _git_show
                run_version_pin_diff(repo_root, upgrade_source=tmpdir, upgrade_ref="v1.7.0")

            artifact = repo_root / "artifacts/blueprint/version_pin_diff.json"
            self.assertTrue(artifact.exists(), "artifact not written")
            data = json.loads(artifact.read_text(encoding="utf-8"))
            for key in ("baseline_ref", "target_ref", "changed_pins", "new_pins", "removed_pins", "unchanged_count"):
                self.assertIn(key, data)

    def test_artifact_contains_target_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._make_contract(repo_root)
            (repo_root / "artifacts/blueprint").mkdir(parents=True)

            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(returncode=0, stdout=_BASELINE_VERSIONS_SH)
                run_version_pin_diff(repo_root, upgrade_source=tmpdir, upgrade_ref="v1.7.0")

            data = json.loads((repo_root / "artifacts/blueprint/version_pin_diff.json").read_text(encoding="utf-8"))
            self.assertEqual(data["target_ref"], "v1.7.0")

    def test_function_always_returns_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._make_contract(repo_root)
            (repo_root / "artifacts/blueprint").mkdir(parents=True)

            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(returncode=0, stdout=_BASELINE_VERSIONS_SH)
                result = run_version_pin_diff(repo_root, upgrade_source=tmpdir, upgrade_ref="v1.7.0")

            self.assertTrue(result)

    def test_changed_pin_in_artifact_with_template_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._make_contract(repo_root)
            (repo_root / "artifacts/blueprint").mkdir(parents=True)
            template_dir = repo_root / "scripts/templates/infra/bootstrap"
            template_dir.mkdir(parents=True)
            (template_dir / "main.yaml").write_text(
                "TERRAFORM_VERSION: placeholder\n", encoding="utf-8"
            )

            call_count = [0]

            def _git_show(cmd, **kwargs):
                call_count[0] += 1
                if call_count[0] <= 2:
                    return mock.Mock(returncode=0, stdout=_BASELINE_VERSIONS_SH)
                return mock.Mock(returncode=0, stdout=_TARGET_VERSIONS_SH)

            with mock.patch("subprocess.run", side_effect=_git_show):
                run_version_pin_diff(repo_root, upgrade_source=tmpdir, upgrade_ref="v1.7.0")

            data = json.loads((repo_root / "artifacts/blueprint/version_pin_diff.json").read_text(encoding="utf-8"))
            changed = {p["variable"]: p for p in data["changed_pins"]}
            self.assertIn("TERRAFORM_VERSION", changed)
            self.assertTrue(
                len(changed["TERRAFORM_VERSION"]["template_references"]) >= 1,
                "expected at least one template reference for TERRAFORM_VERSION",
            )


# ===========================================================================
# Error path — FR-005, AC-005
# ===========================================================================


class TestGitErrorIsolation(unittest.TestCase):
    """FR-005: git CalledProcessError → error artifact written, function returns True."""

    def _make_contract(self, repo_root: Path) -> None:
        contract_dir = repo_root / "blueprint"
        contract_dir.mkdir(parents=True, exist_ok=True)
        (contract_dir / "contract.yaml").write_text(
            'spec:\n  repository:\n    template_bootstrap:\n      template_version: "1.0.0"\n',
            encoding="utf-8",
        )

    def test_git_error_yields_error_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._make_contract(repo_root)
            (repo_root / "artifacts/blueprint").mkdir(parents=True)

            with mock.patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    128, ["git", "show"], stderr="fatal: not a git repo"
                )
                result = run_version_pin_diff(repo_root, upgrade_source=tmpdir, upgrade_ref="v1.7.0")

            artifact = repo_root / "artifacts/blueprint/version_pin_diff.json"
            self.assertTrue(artifact.exists(), "error artifact must be written")
            data = json.loads(artifact.read_text(encoding="utf-8"))
            self.assertIn("error", data, "error field must be present")
            self.assertTrue(bool(data["error"]), "error field must be non-empty")

    def test_git_error_function_returns_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._make_contract(repo_root)
            (repo_root / "artifacts/blueprint").mkdir(parents=True)

            with mock.patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    128, ["git", "show"], stderr="fatal"
                )
                result = run_version_pin_diff(repo_root, upgrade_source=tmpdir, upgrade_ref="v1.7.0")

            self.assertTrue(result, "function must return True even on git error")
