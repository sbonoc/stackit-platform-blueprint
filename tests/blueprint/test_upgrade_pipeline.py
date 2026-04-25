"""Tests for the scripted upgrade pipeline (2026-04-25-scripted-upgrade-pipeline).

Slice 1: Pre-flight validation helper
  TestPreflightDirtyTree   — FR-001
  TestPreflightInvalidRef  — FR-002
  TestPreflightBadContract — FR-003
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.blueprint.upgrade_pipeline_preflight import (
    check_clean_working_tree,
    check_contract,
    check_upgrade_ref,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Shared git helpers
# ---------------------------------------------------------------------------


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@test.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test"],
        capture_output=True,
        check=True,
    )


def _commit_all(path: Path, message: str = "initial") -> str:
    """Stage all files and create a commit; return the commit SHA."""
    subprocess.run(["git", "-C", str(path), "add", "-A"], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", message, "--allow-empty"],
        capture_output=True,
        check=True,
    )
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_valid_consumer_contract(repo_root: Path) -> None:
    """Write a minimal valid generated-consumer blueprint/contract.yaml."""
    (repo_root / "blueprint").mkdir(parents=True, exist_ok=True)
    (repo_root / "blueprint/contract.yaml").write_text(
        "metadata:\n  name: test-consumer\nspec:\n  repository:\n    repo_mode: generated-consumer\n",
        encoding="utf-8",
    )


# ===========================================================================
# Slice 1 — Pre-flight validation helper
# ===========================================================================


class TestPreflightDirtyTree(unittest.TestCase):
    """FR-001: Pipeline aborts with non-zero result and human-readable message when working tree is dirty."""

    def test_untracked_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            _commit_all(repo)
            # Introduce an untracked file
            (repo / "untracked.txt").write_text("new", encoding="utf-8")

            result = check_clean_working_tree(repo)

            self.assertFalse(result.success)
            self.assertIn("clean", result.message.lower())

    def test_unstaged_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            (repo / "existing.txt").write_text("original", encoding="utf-8")
            _commit_all(repo)
            # Modify a tracked file without staging it
            (repo / "existing.txt").write_text("modified", encoding="utf-8")

            result = check_clean_working_tree(repo)

            self.assertFalse(result.success)
            self.assertIn("clean", result.message.lower())

    def test_staged_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            _commit_all(repo)
            # Stage a new file without committing it
            (repo / "staged.txt").write_text("staged", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "staged.txt"], capture_output=True, check=True)

            result = check_clean_working_tree(repo)

            self.assertFalse(result.success)
            self.assertIn("clean", result.message.lower())

    def test_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            _commit_all(repo)

            result = check_clean_working_tree(repo)

            self.assertTrue(result.success)


class TestPreflightInvalidRef(unittest.TestCase):
    """FR-002: Pipeline aborts when BLUEPRINT_UPGRADE_REF is unset or doesn't resolve in BLUEPRINT_UPGRADE_SOURCE."""

    def test_empty_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_upgrade_ref(upgrade_ref="", upgrade_source=tmpdir)

            self.assertFalse(result.success)
            self.assertIn("BLUEPRINT_UPGRADE_REF", result.message)

    def test_empty_source_fails(self) -> None:
        result = check_upgrade_ref(upgrade_ref="v1.0.0", upgrade_source="")

        self.assertFalse(result.success)
        self.assertIn("BLUEPRINT_UPGRADE_SOURCE", result.message)

    def test_nonexistent_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            _init_git_repo(source)
            _commit_all(source)

            result = check_upgrade_ref(upgrade_ref="v99.99.99", upgrade_source=str(source))

            self.assertFalse(result.success)
            self.assertIn("v99.99.99", result.message)

    def test_nonexistent_source_path_fails(self) -> None:
        result = check_upgrade_ref(upgrade_ref="HEAD", upgrade_source="/nonexistent/path/xyz")

        self.assertFalse(result.success)

    def test_valid_commit_sha_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            _init_git_repo(source)
            sha = _commit_all(source)

            result = check_upgrade_ref(upgrade_ref=sha, upgrade_source=str(source))

            self.assertTrue(result.success)

    def test_valid_branch_ref_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            _init_git_repo(source)
            _commit_all(source)

            result = check_upgrade_ref(upgrade_ref="HEAD", upgrade_source=str(source))

            self.assertTrue(result.success)


class TestPreflightBadContract(unittest.TestCase):
    """FR-003: Pipeline aborts when blueprint/contract.yaml is absent, unparseable, or has wrong repo_mode."""

    def test_missing_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("absent", result.message.lower())

    def test_invalid_yaml_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "blueprint").mkdir()
            (repo / "blueprint/contract.yaml").write_text("{{{{ not valid yaml", encoding="utf-8")

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("parseable", result.message.lower())

    def test_wrong_repo_mode_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "blueprint").mkdir()
            (repo / "blueprint/contract.yaml").write_text(
                "metadata:\n  name: blueprint\nspec:\n  repository:\n    repo_mode: template-source\n",
                encoding="utf-8",
            )

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("generated-consumer", result.message)

    def test_missing_spec_section_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "blueprint").mkdir()
            (repo / "blueprint/contract.yaml").write_text(
                "metadata:\n  name: test\n",
                encoding="utf-8",
            )

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("generated-consumer", result.message)

    def test_valid_generated_consumer_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _write_valid_consumer_contract(repo)

            result = check_contract(repo)

            self.assertTrue(result.success)
