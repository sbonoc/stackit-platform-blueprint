"""Unit tests for upgrade_reconcile_report.py — conflicts_unresolved state tracking.

Covers FR-001–FR-004 / AC-001–AC-004:
  FR-001 — conflicts_unresolved populated from active working-tree markers only.
  FR-002 — auto-merged files (apply result == "merged") excluded.
  FR-003 — manually-resolved files (markers cleared) excluded.
  FR-004 — no double-counting of the same path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.lib.blueprint.upgrade_reconcile_report import (
    build_upgrade_reconcile_report,
    find_merge_markers,
)


class TestFindMergeMarkers(unittest.TestCase):
    """Unit tests for find_merge_markers helper."""

    def _make_repo(self, files: dict[str, str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for rel, content in files.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        return tmp

    def test_file_with_markers_detected(self) -> None:
        """File containing <<<<<<< must be returned."""
        conflict = "<<<<<<< HEAD\nlocal\n=======\nupstream\n>>>>>>> ref\n"
        repo = self._make_repo({"scripts/setup.sh": conflict})
        result = find_merge_markers(repo)
        self.assertIn("scripts/setup.sh", result)

    def test_clean_file_not_detected(self) -> None:
        """File without markers must not be returned."""
        repo = self._make_repo({"scripts/setup.sh": "#!/bin/bash\necho ok\n"})
        result = find_merge_markers(repo)
        self.assertNotIn("scripts/setup.sh", result)

    def test_empty_repo_returns_empty_set(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        result = find_merge_markers(tmp)
        self.assertEqual(result, set())


class TestConflictsUnresolvedStateTracking(unittest.TestCase):
    """FR-001–FR-004 / AC-001–AC-004: conflicts_unresolved reflects active markers only."""

    def _make_repo(self, files: dict[str, str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for rel, content in files.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        return tmp

    def _plan(self, entries: list[dict]) -> dict:
        return {"entries": entries, "required_manual_actions": []}

    def _apply(self, results: list[dict]) -> dict:
        return {"results": results, "merge_markers": []}

    def _conflict_paths(self, report: dict) -> list[str]:
        return [e["path"] for e in report["buckets"]["conflicts_unresolved"]]

    def test_auto_merged_file_excluded_from_conflicts(self) -> None:
        """FR-002 / AC-002: apply result == 'merged' (auto-merged) → not in conflicts_unresolved.

        The file has no active markers in the working tree (auto-merge succeeded),
        so it must not appear in conflicts_unresolved even though the plan entry
        action is 'conflict'.
        """
        repo = self._make_repo({"scripts/setup.sh": "#!/bin/bash\necho ok\n"})
        plan = self._plan([
            {
                "path": "scripts/setup.sh",
                "action": "conflict",
                "reason": "3-way merge conflict",
                "ownership": "blueprint-managed",
            }
        ])
        apply = self._apply([
            {"path": "scripts/setup.sh", "result": "merged", "reason": "auto-merged"},
        ])
        report = build_upgrade_reconcile_report(repo_root=repo, plan_payload=plan, apply_payload=apply)
        self.assertNotIn(
            "scripts/setup.sh",
            self._conflict_paths(report),
            msg="auto-merged file (no active markers) must not be in conflicts_unresolved",
        )

    def test_manually_resolved_conflict_excluded(self) -> None:
        """FR-003 / AC-001: markers cleared → not in conflicts_unresolved.

        The file was a conflict in both plan and apply but the operator manually
        resolved it; working tree has no active markers.
        """
        repo = self._make_repo({"scripts/setup.sh": "#!/bin/bash\necho resolved\n"})
        plan = self._plan([
            {
                "path": "scripts/setup.sh",
                "action": "conflict",
                "reason": "plan conflict",
                "ownership": "blueprint-managed",
            }
        ])
        apply = self._apply([
            {"path": "scripts/setup.sh", "result": "conflict", "reason": "apply conflict"},
        ])
        report = build_upgrade_reconcile_report(repo_root=repo, plan_payload=plan, apply_payload=apply)
        self.assertNotIn(
            "scripts/setup.sh",
            self._conflict_paths(report),
            msg="manually-resolved conflict (no active markers) must not block postcheck",
        )

    def test_active_marker_file_included(self) -> None:
        """FR-001 / AC-004: file with <<<<<<< markers → included in conflicts_unresolved."""
        conflict_content = (
            "<<<<<<< HEAD\nlocal version\n=======\nupstream version\n>>>>>>> upstream\n"
        )
        repo = self._make_repo({"scripts/setup.sh": conflict_content})
        plan = self._plan([
            {
                "path": "scripts/setup.sh",
                "action": "conflict",
                "reason": "conflict",
                "ownership": "blueprint-managed",
            }
        ])
        apply = self._apply([
            {"path": "scripts/setup.sh", "result": "conflict", "reason": "conflict"},
        ])
        report = build_upgrade_reconcile_report(repo_root=repo, plan_payload=plan, apply_payload=apply)
        self.assertIn(
            "scripts/setup.sh",
            self._conflict_paths(report),
            msg="file with active <<<<<<< markers must be in conflicts_unresolved",
        )

    def test_no_double_counting(self) -> None:
        """FR-004: path in both plan entries AND apply results → counted exactly once."""
        conflict_content = "<<<<<<< HEAD\nA\n=======\nB\n>>>>>>> ref\n"
        repo = self._make_repo({"scripts/setup.sh": conflict_content})
        plan = self._plan([
            {
                "path": "scripts/setup.sh",
                "action": "conflict",
                "reason": "plan conflict",
                "ownership": "blueprint-managed",
            }
        ])
        apply = self._apply([
            {"path": "scripts/setup.sh", "result": "conflict", "reason": "apply conflict"},
        ])
        report = build_upgrade_reconcile_report(repo_root=repo, plan_payload=plan, apply_payload=apply)
        paths = self._conflict_paths(report)
        self.assertEqual(
            paths.count("scripts/setup.sh"),
            1,
            msg="same path must appear at most once in conflicts_unresolved",
        )

    def test_unrelated_active_marker_file_included(self) -> None:
        """FR-001: file with active markers not in plan/apply → still included in conflicts_unresolved."""
        conflict_content = "<<<<<<< HEAD\nA\n=======\nB\n>>>>>>> ref\n"
        repo = self._make_repo({"scripts/setup.sh": conflict_content})
        # plan and apply reference a different file entirely
        plan = self._plan([
            {"path": "Makefile", "action": "update", "reason": "update", "ownership": "blueprint-managed"},
        ])
        apply = self._apply([
            {"path": "Makefile", "result": "updated", "reason": "applied"},
        ])
        report = build_upgrade_reconcile_report(repo_root=repo, plan_payload=plan, apply_payload=apply)
        self.assertIn(
            "scripts/setup.sh",
            self._conflict_paths(report),
            msg="file with active markers must be included even when not in plan/apply",
        )
