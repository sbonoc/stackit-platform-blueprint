"""Regression test for issue #261 — volatile artifact names for fresh-env gate.

Ensures compute_artifact_checksum_divergences returns no divergences when
upgrade_validate.json and required_files_status.json differ only in embedded
absolute paths (which change between worktree and working-tree runs).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from scripts.lib.blueprint.upgrade_fresh_env_gate import (
    _VOLATILE_ARTIFACT_NAMES,
    compute_artifact_checksum_divergences,
)

_ARTIFACT_SUBDIR = "artifacts/blueprint"
_UPGRADE_VALIDATE_NAME = "upgrade_validate.json"
_REQUIRED_FILES_STATUS_NAME = "required_files_status.json"


def _write_artifact(root: Path, name: str, content: dict) -> None:
    path = root / _ARTIFACT_SUBDIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


class VolatileArtifactNamesIssue261Tests(unittest.TestCase):
    def test_upgrade_validate_json_is_in_volatile_set(self) -> None:
        """upgrade_validate.json must be in _VOLATILE_ARTIFACT_NAMES."""
        self.assertIn(
            _UPGRADE_VALIDATE_NAME,
            _VOLATILE_ARTIFACT_NAMES,
            msg=(
                f"'{_UPGRADE_VALIDATE_NAME}' must be in _VOLATILE_ARTIFACT_NAMES so that "
                "absolute-path divergences are excluded from the fresh-env gate."
            ),
        )

    def test_required_files_status_json_is_in_volatile_set(self) -> None:
        """required_files_status.json must be in _VOLATILE_ARTIFACT_NAMES."""
        self.assertIn(
            _REQUIRED_FILES_STATUS_NAME,
            _VOLATILE_ARTIFACT_NAMES,
            msg=(
                f"'{_REQUIRED_FILES_STATUS_NAME}' must be in _VOLATILE_ARTIFACT_NAMES so that "
                "absolute-path divergences are excluded from the fresh-env gate."
            ),
        )

    def test_upgrade_validate_json_path_divergence_not_reported(self) -> None:
        """Differing absolute repo_root in upgrade_validate.json must not produce a divergence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wt_path = Path(tmpdir) / "worktree"
            wk_path = Path(tmpdir) / "working"

            _write_artifact(
                wt_path,
                _UPGRADE_VALIDATE_NAME,
                {"repo_root": "/tmp/fresh-env-worktree-abc123", "status": "success"},
            )
            _write_artifact(
                wk_path,
                _UPGRADE_VALIDATE_NAME,
                {"repo_root": "/Users/dev/consumer-repo", "status": "success"},
            )

            divergences = compute_artifact_checksum_divergences(wt_path, wk_path)
            upgrade_validate_divergences = [
                d for d in divergences
                if d.get("path", "").endswith(_UPGRADE_VALIDATE_NAME)
            ]
            self.assertEqual(
                upgrade_validate_divergences,
                [],
                msg=(
                    f"upgrade_validate.json must not appear in divergences when it contains "
                    f"only absolute-path differences. Got: {upgrade_validate_divergences}"
                ),
            )

    def test_required_files_status_json_path_divergence_not_reported(self) -> None:
        """Differing absolute repo_root in required_files_status.json must not produce a divergence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wt_path = Path(tmpdir) / "worktree"
            wk_path = Path(tmpdir) / "working"

            _write_artifact(
                wt_path,
                _REQUIRED_FILES_STATUS_NAME,
                {"repo_root": "/tmp/fresh-env-worktree-abc123", "missing_count": 0},
            )
            _write_artifact(
                wk_path,
                _REQUIRED_FILES_STATUS_NAME,
                {"repo_root": "/Users/dev/consumer-repo", "missing_count": 0},
            )

            divergences = compute_artifact_checksum_divergences(wt_path, wk_path)
            status_divergences = [
                d for d in divergences
                if d.get("path", "").endswith(_REQUIRED_FILES_STATUS_NAME)
            ]
            self.assertEqual(
                status_divergences,
                [],
                msg=(
                    f"required_files_status.json must not appear in divergences when it contains "
                    f"only absolute-path differences. Got: {status_divergences}"
                ),
            )

    def test_both_volatile_files_no_divergence_with_stable_sibling(self) -> None:
        """Both volatile files excluded; stable sibling with identical content produces no divergence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wt_path = Path(tmpdir) / "worktree"
            wk_path = Path(tmpdir) / "working"

            for root in (wt_path, wk_path):
                _write_artifact(root, _UPGRADE_VALIDATE_NAME, {"repo_root": str(root)})
                _write_artifact(root, _REQUIRED_FILES_STATUS_NAME, {"repo_root": str(root)})
                _write_artifact(root, "upgrade_plan.json", {"status": "success"})

            divergences = compute_artifact_checksum_divergences(wt_path, wk_path)
            self.assertEqual(
                divergences,
                [],
                msg=f"No divergences expected when volatile files differ and stable file matches. Got: {divergences}",
            )

    def test_stable_artifact_with_real_content_difference_still_reported(self) -> None:
        """A non-volatile artifact with genuinely different content must still appear in divergences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wt_path = Path(tmpdir) / "worktree"
            wk_path = Path(tmpdir) / "working"

            _write_artifact(wt_path, "upgrade_plan.json", {"status": "success"})
            _write_artifact(wk_path, "upgrade_plan.json", {"status": "failure"})

            divergences = compute_artifact_checksum_divergences(wt_path, wk_path)
            plan_divergences = [
                d for d in divergences
                if d.get("path", "").endswith("upgrade_plan.json")
            ]
            self.assertEqual(
                len(plan_divergences),
                1,
                msg=f"upgrade_plan.json with different content must appear in divergences. Got: {divergences}",
            )
