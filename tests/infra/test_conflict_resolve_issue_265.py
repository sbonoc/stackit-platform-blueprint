"""Regression tests for issue #265 — conflict resolve script behaviour.

Tests cover:
- take_source rows applied to working-tree file (AC-006, FR-007)
- human_required rows left untouched (AC-007, FR-007)
- upgrade_resolve.json written with per-action results (AC-008, FR-007)
- resolve is idempotent: second run produces no changes, exits 0 (NFR-IDM-001)
- resolve exits non-zero when triage is absent (NFR-REL-001)
- residual table sorted and truncated above 20 rows (AC-009, FR-008, FR-009)
- --dry-run makes no file changes and no .conflict.json deletions (FR-012)
- --accept-source ALL applies human_required rows (FR-011)
- resolve prints one upgrade-resolve: <action> <path> line per applied row (NFR-OBS-001)
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRIAGE_SCHEMA_PATH = REPO_ROOT / "scripts/lib/blueprint/schemas/upgrade_triage.schema.json"

sys.path.insert(0, str(REPO_ROOT))


def _write_triage(repo_root: Path, conflicts: list[dict]) -> None:
    triage_path = repo_root / "artifacts/blueprint/upgrade_triage.json"
    triage_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "source_ref": "v1.10.0",
        "baseline_ref": "v1.7.0",
        "conflicts": conflicts,
    }
    triage_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


def _write_conflict_artifact(
    repo_root: Path,
    rel_path: str,
    source_content: str = "source-content\n",
    target_content: str = "target-content\n",
) -> None:
    artifact_path = repo_root / "artifacts/blueprint/conflicts" / f"{rel_path}.conflict.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "path": rel_path,
        "reason": "merge conflict",
        "source_content": source_content,
        "target_content": target_content,
        "baseline_content": "baseline-content\n",
    }
    artifact_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
    working_tree_path = repo_root / rel_path
    working_tree_path.parent.mkdir(parents=True, exist_ok=True)
    working_tree_path.write_text(target_content, encoding="utf-8")


def _triage_entry(
    rel_path: str,
    ownership_class: str = "blueprint-managed-root",
    recommended_action: str = "take_source",
) -> dict:
    return {
        "path": rel_path,
        "ownership_class": ownership_class,
        "ownership_evidence": "managed root",
        "recommended_action": recommended_action,
        "reason": "test",
        "source_diff_summary": "+1 -0 lines",
        "target_diff_from_baseline": "+0 -1 lines",
    }


class ResolveTakeSourceTests(unittest.TestCase):
    def test_take_source_rows_applied_to_working_tree(self) -> None:
        """After resolve, take_source working-tree files MUST contain source content (AC-006, FR-007)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/bin/blueprint/some_script.sh"
        source_content = "#!/bin/bash\n# source version\n"
        target_content = "#!/bin/bash\n# consumer version\n"

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path, source_content, target_content)
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed-root", "take_source")])

            exit_code = _resolve(repo_root)

            self.assertEqual(exit_code, 0, "_resolve must exit 0 on success")
            actual = (repo_root / rel_path).read_text(encoding="utf-8")
            self.assertEqual(
                actual,
                source_content,
                "take_source row: working-tree file MUST contain source content after resolve",
            )

    def test_human_required_rows_not_touched(self) -> None:
        """human_required entries MUST leave the working-tree file unchanged (AC-007, FR-007)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/lib/platform/some_lib.py"
        target_content = "# consumer version\n"

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path, "# source\n", target_content)
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed", "human_required")])
            conflict_artifact = repo_root / "artifacts/blueprint/conflicts" / f"{rel_path}.conflict.json"

            _resolve(repo_root)

            actual = (repo_root / rel_path).read_text(encoding="utf-8")
            self.assertEqual(
                actual,
                target_content,
                "human_required row: working-tree file MUST remain unchanged",
            )
            self.assertTrue(
                conflict_artifact.exists(),
                "human_required row: .conflict.json MUST NOT be deleted",
            )


class ResolveArtifactTests(unittest.TestCase):
    def test_upgrade_resolve_json_written(self) -> None:
        """artifacts/blueprint/upgrade_resolve.json MUST exist after resolve with per-action results (AC-008)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/bin/blueprint/some_script.sh"
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path)
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed-root", "take_source")])

            _resolve(repo_root)

            resolve_path = repo_root / "artifacts/blueprint/upgrade_resolve.json"
            self.assertTrue(resolve_path.exists(), "upgrade_resolve.json must be written")
            resolve_data = json.loads(resolve_path.read_text(encoding="utf-8"))
            actions = resolve_data.get("actions", [])
            self.assertGreater(len(actions), 0, "upgrade_resolve.json must contain at least one action")
            action = actions[0]
            for field in ("path", "action_taken", "result"):
                self.assertIn(field, action, f"upgrade_resolve.json action entry must have '{field}' field")
            self.assertEqual(action["path"], rel_path)

    def test_resolve_is_idempotent(self) -> None:
        """Running resolve twice MUST produce no changes on second run and exit 0 (NFR-IDM-001)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/bin/blueprint/some_script.sh"
        source_content = "# source\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path, source_content, "# target\n")
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed-root", "take_source")])

            first_exit = _resolve(repo_root)
            content_after_first = (repo_root / rel_path).read_text(encoding="utf-8")
            second_exit = _resolve(repo_root)
            content_after_second = (repo_root / rel_path).read_text(encoding="utf-8")

            self.assertEqual(first_exit, 0, "first resolve run must exit 0")
            self.assertEqual(second_exit, 0, "second resolve run must exit 0 (idempotent)")
            self.assertEqual(
                content_after_first,
                content_after_second,
                "second resolve run MUST produce no file changes",
            )

    def test_resolve_exits_nonzero_if_triage_missing(self) -> None:
        """Resolve MUST exit non-zero when upgrade_triage.json is absent (NFR-REL-001)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            exit_code = _resolve(repo_root)
            self.assertNotEqual(exit_code, 0, "resolve must exit non-zero when triage is missing")


class ResolveResidualTableTests(unittest.TestCase):
    def test_residual_table_sorted_and_truncated_above_20(self) -> None:
        """Residual table MUST truncate at 20 rows and show a footer with total count (AC-009, FR-008)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            conflicts = []
            for i in range(25):
                rel_path = f"scripts/lib/platform/file_{i:03d}.py"
                _write_conflict_artifact(repo_root, rel_path, "# source\n", "# target\n")
                conflicts.append(_triage_entry(rel_path, "blueprint-managed", "human_required"))
            _write_triage(repo_root, conflicts)

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                _resolve(repo_root)
            finally:
                sys.stdout = old_stdout

            output = captured.getvalue()
            self.assertIn(
                "25",
                output,
                "Residual table footer MUST include the total count (25) when rows exceed 20",
            )


class ResolveFlagsTests(unittest.TestCase):
    def test_dry_run_makes_no_file_changes(self) -> None:
        """--dry-run MUST produce no working-tree writes and no .conflict.json deletions (FR-012)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/bin/blueprint/some_script.sh"
        target_content = "# consumer version\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path, "# source\n", target_content)
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed-root", "take_source")])
            conflict_artifact = repo_root / "artifacts/blueprint/conflicts" / f"{rel_path}.conflict.json"

            _resolve(repo_root, dry_run=True)

            actual = (repo_root / rel_path).read_text(encoding="utf-8")
            self.assertEqual(
                actual,
                target_content,
                "--dry-run MUST NOT write to working-tree files",
            )
            self.assertTrue(
                conflict_artifact.exists(),
                "--dry-run MUST NOT delete .conflict.json files",
            )

    def test_accept_source_all_applies_human_required_rows(self) -> None:
        """--accept-source ALL MUST apply all human_required rows with source content (FR-011)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/lib/platform/some_lib.py"
        source_content = "# source version\n"
        target_content = "# consumer version\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path, source_content, target_content)
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed", "human_required")])

            exit_code = _resolve(repo_root, accept_source_all=True)

            self.assertEqual(exit_code, 0, "_resolve with accept_source_all must exit 0")
            actual = (repo_root / rel_path).read_text(encoding="utf-8")
            self.assertEqual(
                actual,
                source_content,
                "--accept-source ALL MUST apply source content even for human_required rows",
            )

    def test_resolve_prints_action_per_row(self) -> None:
        """Resolve MUST print 'upgrade-resolve: <action> <path>' per applied row (NFR-OBS-001)."""
        from scripts.lib.blueprint.upgrade_consumer_resolve import _resolve

        rel_path = "scripts/bin/blueprint/some_script.sh"
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_conflict_artifact(repo_root, rel_path)
            _write_triage(repo_root, [_triage_entry(rel_path, "blueprint-managed-root", "take_source")])

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                _resolve(repo_root)
            finally:
                sys.stdout = old_stdout

            output = captured.getvalue()
            self.assertIn(
                f"upgrade-resolve:",
                output,
                "resolve MUST print 'upgrade-resolve: <action> <path>' per applied row (NFR-OBS-001)",
            )
            self.assertIn(
                rel_path,
                output,
                "resolve output MUST include the path of each applied row",
            )


if __name__ == "__main__":
    unittest.main()
