from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.lib.docs import orchestrate_sync


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git command failed: {' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


class DocsOrchestrateSyncTests(unittest.TestCase):
    def test_changed_paths_uses_base_ref_diff_when_worktree_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "docs-orchestrator@example.com")
            _run_git(repo_root, "config", "user.name", "Docs Orchestrator")

            docs_readme = repo_root / "docs" / "README.md"
            docs_readme.parent.mkdir(parents=True, exist_ok=True)
            docs_readme.write_text("# baseline\n", encoding="utf-8")
            _run_git(repo_root, "add", "docs/README.md")
            _run_git(repo_root, "commit", "-m", "baseline")
            _run_git(repo_root, "branch", "-M", "main")

            _run_git(repo_root, "checkout", "-b", "feature/sdd")
            docs_readme.write_text("# baseline\n\nupdated\n", encoding="utf-8")
            _run_git(repo_root, "add", "docs/README.md")
            _run_git(repo_root, "commit", "-m", "update docs readme")

            # Worktree is clean: changed-scope detection must use base-ref diff.
            status = _run_git(repo_root, "status", "--porcelain")
            self.assertEqual(status.strip(), "")

            changed_paths = orchestrate_sync._changed_paths(repo_root, base_ref="main")
            self.assertIn("docs/README.md", changed_paths)

    def test_main_ci_falls_back_to_all_steps_when_changed_only_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            with (
                patch.object(orchestrate_sync, "_changed_paths", return_value=[]),
                patch.object(orchestrate_sync, "_run_step", return_value=0) as run_step,
                patch.object(orchestrate_sync, "resolve_repo_root", return_value=repo_root),
                patch.dict(os.environ, {"CI": "true"}, clear=False),
                patch.object(sys, "argv", ["orchestrate_sync.py", "--mode", "check", "--changed-only"]),
            ):
                exit_code = orchestrate_sync.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(run_step.call_count, len(orchestrate_sync.STEPS))

    def test_main_local_changed_only_no_matches_runs_no_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            with (
                patch.object(orchestrate_sync, "_changed_paths", return_value=[]),
                patch.object(orchestrate_sync, "_run_step", return_value=0) as run_step,
                patch.object(orchestrate_sync, "resolve_repo_root", return_value=repo_root),
                patch.dict(os.environ, {"CI": ""}, clear=False),
                patch.object(sys, "argv", ["orchestrate_sync.py", "--mode", "check", "--changed-only"]),
            ):
                exit_code = orchestrate_sync.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(run_step.call_count, 0)


if __name__ == "__main__":
    unittest.main()
