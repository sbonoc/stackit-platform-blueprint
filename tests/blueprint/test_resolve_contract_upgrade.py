"""Regression tests for resolve_contract_upgrade.py — FR-009 source_only filtering.

Slice 1 — Failing regression tests (red):
  TestSourceOnlyPhase1Drop       — AC-001: source entries existing on disk are dropped
  TestSourceOnlyPhase1ClaudeMd   — AC-002: CLAUDE.md existing on disk is dropped
  TestSourceOnlyPhase2CarryForward — AC-003: consumer-added entries on disk are kept
  TestSourceOnlyNoConflict       — AC-005: regression guard when no conflict exists

These tests reproduce bug #216: resolve_contract_conflict Stage 3 copies source_only
wholesale from the source contract, overwriting consumer's source_only.  Consumers
with specs/, CLAUDE.md, etc. then fail infra-validate with "file must be absent" errors.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFLICT_REL = "artifacts/blueprint/conflicts/blueprint/contract.yaml.conflict.json"


def _build_conflict_json(
    source_source_only: list[str],
    target_source_only: list[str],
    source_name: str = "stackit-k8s-reusable-blueprint",
    target_name: str = "my-consumer",
) -> dict:
    """Build a minimal conflict JSON payload for contract resolution tests."""
    source_contract = {
        "metadata": {"name": source_name},
        "spec": {
            "repository": {
                "repo_mode": "template-source",
                "description": "Platform blueprint template",
                "ownership_path_classes": {
                    "source_only": source_source_only,
                    "required_files": [],
                    "consumer_seeded": [],
                    "init_managed": [],
                },
                "required_files": [],
                "consumer_init": {
                    "source_artifact_prune_globs_on_init": [],
                },
            }
        },
    }
    target_contract = {
        "metadata": {"name": target_name},
        "spec": {
            "repository": {
                "repo_mode": "generated-consumer",
                "description": "My consumer repo",
                "ownership_path_classes": {
                    "source_only": target_source_only,
                    "required_files": [],
                    "consumer_seeded": [],
                    "init_managed": [],
                },
                "required_files": [],
                "consumer_init": {
                    "source_artifact_prune_globs_on_init": [],
                },
            }
        },
    }
    return {
        "path": "blueprint/contract.yaml",
        "reason": "3-way merge produced conflicts",
        "source_content": yaml.dump(source_contract, default_flow_style=False),
        "target_content": yaml.dump(target_contract, default_flow_style=False),
        "merged_content": "",
    }


def _setup_conflict(repo_root: Path, payload: dict) -> None:
    """Write the conflict JSON to the canonical path."""
    conflict_path = repo_root / _CONFLICT_REL
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    conflict_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _resolved_source_only(repo_root: Path) -> list[str]:
    """Read the resolved contract and return its source_only list."""
    resolved = yaml.safe_load(
        (repo_root / "blueprint/contract.yaml").read_text(encoding="utf-8")
    )
    return (
        resolved.get("spec", {})
        .get("repository", {})
        .get("ownership_path_classes", {})
        .get("source_only", [])
    )


# ---------------------------------------------------------------------------
# Slice 1 — Failing regression tests (red)
# ---------------------------------------------------------------------------


class TestSourceOnlyPhase1Drop(unittest.TestCase):
    """AC-001: Phase 1 drops source_only entries whose paths exist in the consumer."""

    def test_resolve_contract_conflict_source_only_phase1_drop(self) -> None:
        """specs/ exists on disk → source entry 'specs' must NOT appear in resolved source_only."""
        from scripts.lib.blueprint.resolve_contract_upgrade import resolve_contract_conflict

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)

            # Consumer has a real specs/ directory with content.
            specs_dir = repo / "specs"
            specs_dir.mkdir(parents=True, exist_ok=True)
            (specs_dir / "2026-01-01-example" ).mkdir(parents=True, exist_ok=True)
            (specs_dir / "2026-01-01-example" / "spec.md").write_text(
                "# Real consumer spec", encoding="utf-8"
            )

            # Source contract lists 'specs' in source_only; target (consumer) mirrors it.
            payload = _build_conflict_json(
                source_source_only=["specs", "CLAUDE.md"],
                target_source_only=["specs", "CLAUDE.md"],
            )
            _setup_conflict(repo, payload)

            result = resolve_contract_conflict(repo)

            self.assertTrue(result.success, msg=result.message)
            source_only = _resolved_source_only(repo)

            # Phase 1 must drop 'specs' because the directory exists in the consumer.
            self.assertNotIn(
                "specs",
                source_only,
                msg=(
                    "Bug #216 reproduced: 'specs' was copied wholesale from source and "
                    "was NOT filtered even though the path exists in the consumer."
                ),
            )


class TestSourceOnlyPhase1ClaudeMdDrop(unittest.TestCase):
    """AC-002: Phase 1 drops CLAUDE.md from source_only when the file exists in the consumer."""

    def test_resolve_contract_conflict_source_only_claude_md_drop(self) -> None:
        """CLAUDE.md exists on disk → source entry 'CLAUDE.md' must NOT appear in resolved source_only."""
        from scripts.lib.blueprint.resolve_contract_upgrade import resolve_contract_conflict

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)

            # Consumer has a real CLAUDE.md file.
            (repo / "CLAUDE.md").write_text(
                "# Consumer-specific CLAUDE config", encoding="utf-8"
            )

            payload = _build_conflict_json(
                source_source_only=["CLAUDE.md"],
                target_source_only=["CLAUDE.md"],
            )
            _setup_conflict(repo, payload)

            result = resolve_contract_conflict(repo)

            self.assertTrue(result.success, msg=result.message)
            source_only = _resolved_source_only(repo)

            self.assertNotIn(
                "CLAUDE.md",
                source_only,
                msg=(
                    "Bug #216 reproduced: 'CLAUDE.md' was copied wholesale from source "
                    "and was NOT filtered even though the file exists in the consumer."
                ),
            )


class TestSourceOnlyPhase2CarryForward(unittest.TestCase):
    """AC-003: Phase 2 carries forward consumer-added source_only entries whose files exist on disk."""

    def test_resolve_contract_conflict_source_only_phase2_carry_forward(self) -> None:
        """Consumer-added 'my-custom-file.txt' on disk must be kept in resolved source_only."""
        from scripts.lib.blueprint.resolve_contract_upgrade import resolve_contract_conflict

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)

            # Consumer has the file on disk.
            (repo / "my-custom-file.txt").write_text("consumer content", encoding="utf-8")

            # Source does NOT have 'my-custom-file.txt'; consumer added it.
            payload = _build_conflict_json(
                source_source_only=["some-blueprint-only-path"],
                target_source_only=["some-blueprint-only-path", "my-custom-file.txt"],
            )
            _setup_conflict(repo, payload)

            result = resolve_contract_conflict(repo)

            self.assertTrue(result.success, msg=result.message)
            source_only = _resolved_source_only(repo)

            self.assertIn(
                "my-custom-file.txt",
                source_only,
                msg=(
                    "Bug #216 reproduced: consumer-added 'my-custom-file.txt' was lost "
                    "because source_only was taken wholesale from source (which doesn't "
                    "include consumer additions)."
                ),
            )


class TestSourceOnlyNoConflict(unittest.TestCase):
    """AC-005: Regression guard — when no consumer paths match source entries and there are no
    consumer additions, the resolved source_only is identical to the source list."""

    def test_resolve_contract_conflict_source_only_no_conflict(self) -> None:
        """No on-disk path matches source entries → source_only passes through unchanged."""
        from scripts.lib.blueprint.resolve_contract_upgrade import resolve_contract_conflict

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)

            # Neither 'absent-dir' nor 'another-absent-path' exists on disk.
            payload = _build_conflict_json(
                source_source_only=["absent-dir", "another-absent-path"],
                target_source_only=["absent-dir", "another-absent-path"],
            )
            _setup_conflict(repo, payload)

            result = resolve_contract_conflict(repo)

            self.assertTrue(result.success, msg=result.message)
            source_only = _resolved_source_only(repo)

            # Both source entries must survive since their paths don't exist.
            self.assertIn("absent-dir", source_only)
            self.assertIn("another-absent-path", source_only)
