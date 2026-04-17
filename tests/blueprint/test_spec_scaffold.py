from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


SPEC_SCAFFOLD_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/spec_scaffold.py"


def _run_checked(cmd: list[str], *, cwd: Path) -> None:
    result = run_command(cmd, cwd=cwd)
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)


class SpecScaffoldBranchingTests(unittest.TestCase):
    def _prepare_repo(self, repo_root: Path) -> None:
        (repo_root / "blueprint").mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "blueprint/contract.yaml", repo_root / "blueprint/contract.yaml")
        shutil.copytree(
            REPO_ROOT / ".spec-kit/templates/blueprint",
            repo_root / ".spec-kit/templates/blueprint",
            dirs_exist_ok=True,
        )
        (repo_root / "specs").mkdir(parents=True, exist_ok=True)

        _run_checked(["git", "init", "-b", "main"], cwd=repo_root)
        _run_checked(["git", "config", "user.name", "spec-scaffold-test"], cwd=repo_root)
        _run_checked(["git", "config", "user.email", "spec-scaffold-test@example.com"], cwd=repo_root)
        (repo_root / ".gitkeep").write_text("fixture\n", encoding="utf-8")
        _run_checked(["git", "add", "."], cwd=repo_root)
        _run_checked(["git", "commit", "-m", "init fixture"], cwd=repo_root)

    def _current_branch(self, repo_root: Path) -> str:
        result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result.stdout.strip()

    def test_scaffold_creates_dedicated_branch_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._prepare_repo(repo_root)

            result = run_command(
                [
                    "python3",
                    str(SPEC_SCAFFOLD_SCRIPT),
                    "--repo-root",
                    str(repo_root),
                    "--slug",
                    "runtime-identity-contract",
                    "--track",
                    "blueprint",
                    "--date",
                    "2026-04-17",
                ],
                cwd=repo_root,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(
                self._current_branch(repo_root),
                "codex/2026-04-17-runtime-identity-contract",
            )
            self.assertTrue(
                (repo_root / "specs/2026-04-17-runtime-identity-contract/spec.md").is_file(),
                msg=result.stdout + result.stderr,
            )
            self.assertIn(
                "active SDD branch: codex/2026-04-17-runtime-identity-contract",
                result.stdout,
            )

    def test_scaffold_no_create_branch_explicit_opt_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._prepare_repo(repo_root)

            result = run_command(
                [
                    "python3",
                    str(SPEC_SCAFFOLD_SCRIPT),
                    "--repo-root",
                    str(repo_root),
                    "--slug",
                    "quality-controls",
                    "--track",
                    "blueprint",
                    "--date",
                    "2026-04-17",
                    "--no-create-branch",
                ],
                cwd=repo_root,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(self._current_branch(repo_root), "main")
            self.assertIn(
                "branch auto-creation skipped (--no-create-branch); current branch: main",
                result.stdout,
            )

    def test_scaffold_allows_explicit_branch_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._prepare_repo(repo_root)

            result = run_command(
                [
                    "python3",
                    str(SPEC_SCAFFOLD_SCRIPT),
                    "--repo-root",
                    str(repo_root),
                    "--slug",
                    "contract-audit",
                    "--track",
                    "blueprint",
                    "--date",
                    "2026-04-17",
                    "--branch",
                    "feature/explicit-branch-contract-audit",
                ],
                cwd=repo_root,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(self._current_branch(repo_root), "feature/explicit-branch-contract-audit")


if __name__ == "__main__":
    unittest.main()
