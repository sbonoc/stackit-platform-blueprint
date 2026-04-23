from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


GATE_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/upgrade_fresh_env_gate.sh"
GATE_MODULE = REPO_ROOT / "scripts/lib/blueprint/upgrade_fresh_env_gate.py"
GATE_REPORT_NAME = "artifacts/blueprint/fresh_env_gate.json"

REQUIRED_REPORT_FIELDS = {"status", "worktree_path", "targets_run", "divergences", "error", "exit_code"}


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return run_command(cmd, cwd=cwd, env=env)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo)


def _require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({label}) exit={result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _require_success(_git(repo, "init"), "git init")
    _require_success(_git(repo, "config", "user.email", "tests@example.com"), "git config email")
    _require_success(_git(repo, "config", "user.name", "Blueprint Tests"), "git config name")
    _require_success(_git(repo, "commit", "--allow-empty", "-m", "init"), "git commit init")


def _write_makefile(repo: Path, *, infra_validate_exit: int = 0, postcheck_exit: int = 0) -> None:
    """Write a minimal Makefile with the required targets into the repo and commit it."""
    content = (
        ".PHONY: infra-validate blueprint-upgrade-consumer-postcheck\n\n"
        f"infra-validate:\n\t@exit {infra_validate_exit}\n\n"
        f"blueprint-upgrade-consumer-postcheck:\n\t@exit {postcheck_exit}\n"
    )
    _write(repo / "Makefile", content)
    _require_success(_git(repo, "add", "Makefile"), "git add Makefile")
    _require_success(_git(repo, "commit", "-m", "add Makefile"), "git commit Makefile")


def _run_gate(repo: Path, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the fresh-env gate shell script from the consumer repo root."""
    env = {"HOME": str(Path.home())}
    if env_overrides:
        env.update(env_overrides)
    return _run([str(GATE_SCRIPT)], cwd=repo, env=env)


# ---------------------------------------------------------------------------
# Unit tests — Python module (no subprocess, no git)
# ---------------------------------------------------------------------------

class TestFreshEnvGatePythonModule(unittest.TestCase):
    """Tests for upgrade_fresh_env_gate.py in isolation."""

    def test_result_as_dict_has_all_required_fields(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import FreshEnvGateResult

        result = FreshEnvGateResult(
            status="pass",
            worktree_path="/tmp/wt",
            targets_run=["make infra-validate"],
            divergences=[],
            error=None,
            exit_code=0,
        )
        d = result.as_dict()
        self.assertEqual(set(d.keys()), REQUIRED_REPORT_FIELDS)
        self.assertEqual(d["status"], "pass")
        self.assertEqual(d["exit_code"], 0)
        self.assertIsNone(d["error"])

    def test_write_report_creates_json_file(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import FreshEnvGateResult, write_report

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "artifacts" / "fresh_env_gate.json"
            result = FreshEnvGateResult(
                status="pass",
                worktree_path="/tmp/wt",
                targets_run=["make infra-validate", "make blueprint-upgrade-consumer-postcheck"],
                divergences=[],
                error=None,
                exit_code=0,
            )
            write_report(result, output)

            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(set(payload.keys()), REQUIRED_REPORT_FIELDS)
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["targets_run"], ["make infra-validate", "make blueprint-upgrade-consumer-postcheck"])

    def test_write_report_creates_parent_directories(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import FreshEnvGateResult, write_report

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "deep" / "nested" / "path" / "report.json"
            result = FreshEnvGateResult(
                status="error",
                worktree_path="",
                targets_run=[],
                divergences=[],
                error="worktree creation failed",
                exit_code=1,
            )
            write_report(result, output)
            self.assertTrue(output.exists())

    def test_compute_divergences_returns_missing_in_fresh_env(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import compute_divergences

        with tempfile.TemporaryDirectory() as tmpdir:
            wt = Path(tmpdir) / "working_tree"
            wk = Path(tmpdir) / "worktree"
            wt.mkdir()
            wk.mkdir()

            # File present in working tree but absent in worktree
            (wt / "scripts" / "bootstrap.sh").mkdir(parents=True)
            (wt / "scripts" / "bootstrap.sh").rmdir()
            (wt / "scripts").mkdir(parents=True, exist_ok=True)
            (wt / "scripts" / "bootstrap.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

            divergences = compute_divergences(wk, wt)

            self.assertEqual(len(divergences), 1)
            self.assertEqual(divergences[0]["file"], "scripts/bootstrap.sh")
            self.assertEqual(divergences[0]["reason"], "missing_in_fresh_env")

    def test_compute_divergences_returns_unexpected_in_fresh_env(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import compute_divergences

        with tempfile.TemporaryDirectory() as tmpdir:
            wt = Path(tmpdir) / "working_tree"
            wk = Path(tmpdir) / "worktree"
            wt.mkdir()
            wk.mkdir()

            # File present in worktree but absent in working tree
            (wk / "generated.txt").write_text("generated\n", encoding="utf-8")

            divergences = compute_divergences(wk, wt)

            self.assertEqual(len(divergences), 1)
            self.assertEqual(divergences[0]["file"], "generated.txt")
            self.assertEqual(divergences[0]["reason"], "unexpected_in_fresh_env")

    def test_compute_divergences_returns_empty_when_identical(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import compute_divergences

        with tempfile.TemporaryDirectory() as tmpdir:
            wt = Path(tmpdir) / "working_tree"
            wk = Path(tmpdir) / "worktree"
            for d in (wt, wk):
                d.mkdir()
                (d / "Makefile").write_text("all:\n\t@echo ok\n", encoding="utf-8")

            divergences = compute_divergences(wk, wt)
            self.assertEqual(divergences, [])

    def test_compute_divergences_excludes_git_dir(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import compute_divergences

        with tempfile.TemporaryDirectory() as tmpdir:
            wt = Path(tmpdir) / "working_tree"
            wk = Path(tmpdir) / "worktree"
            wt.mkdir()
            wk.mkdir()

            # .git file in working tree — must not appear in divergences
            (wt / ".git").mkdir()
            (wt / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

            divergences = compute_divergences(wk, wt)
            self.assertEqual(divergences, [])

    def test_compute_divergences_excludes_artifacts_dir(self) -> None:
        from scripts.lib.blueprint.upgrade_fresh_env_gate import compute_divergences

        with tempfile.TemporaryDirectory() as tmpdir:
            wt = Path(tmpdir) / "working_tree"
            wk = Path(tmpdir) / "worktree"
            wt.mkdir()
            wk.mkdir()

            # artifacts/ in working tree — must not appear in divergences
            (wt / "artifacts" / "blueprint").mkdir(parents=True)
            (wt / "artifacts" / "blueprint" / "upgrade_postcheck.json").write_text("{}\n", encoding="utf-8")

            divergences = compute_divergences(wk, wt)
            self.assertEqual(divergences, [])


# ---------------------------------------------------------------------------
# Integration tests — shell wrapper (requires git + bash)
# ---------------------------------------------------------------------------

class TestFreshEnvGateShellWrapper(unittest.TestCase):
    """End-to-end tests for upgrade_fresh_env_gate.sh via subprocess."""

    def test_gate_passes_when_both_targets_succeed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=0, postcheck_exit=0)

            result = _run_gate(repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / GATE_REPORT_NAME)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["exit_code"], 0)
            self.assertEqual(report["divergences"], [])

    def test_gate_fails_when_infra_validate_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=1, postcheck_exit=0)

            result = _run_gate(repo)

            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / GATE_REPORT_NAME)
            self.assertEqual(report["status"], "fail")
            self.assertGreater(report["exit_code"], 0)

    def test_gate_fails_when_postcheck_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=0, postcheck_exit=1)

            result = _run_gate(repo)

            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / GATE_REPORT_NAME)
            self.assertEqual(report["status"], "fail")
            self.assertGreater(report["exit_code"], 0)

    def test_gate_errors_when_not_in_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            non_git = Path(tmpdir) / "not_a_repo"
            non_git.mkdir()

            result = _run_gate(non_git)

            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report_path = non_git / GATE_REPORT_NAME
            if report_path.exists():
                report = _load_json(report_path)
                self.assertEqual(report["status"], "error")

    def test_worktree_is_removed_after_successful_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=0, postcheck_exit=0)

            result = _run_gate(repo)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            # Verify no stray worktrees remain
            wt_list = _run(["git", "worktree", "list", "--porcelain"], cwd=repo)
            worktree_paths = [
                line.split(" ", 1)[1]
                for line in wt_list.stdout.splitlines()
                if line.startswith("worktree ")
            ]
            # Only the main worktree should remain
            self.assertEqual(len(worktree_paths), 1, msg=f"stray worktrees: {worktree_paths}")
            self.assertEqual(Path(worktree_paths[0]).resolve(), repo.resolve())

    def test_worktree_is_removed_after_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=1, postcheck_exit=0)

            _run_gate(repo)  # expected to fail

            wt_list = _run(["git", "worktree", "list", "--porcelain"], cwd=repo)
            worktree_paths = [
                line.split(" ", 1)[1]
                for line in wt_list.stdout.splitlines()
                if line.startswith("worktree ")
            ]
            self.assertEqual(len(worktree_paths), 1, msg=f"stray worktrees: {worktree_paths}")
            self.assertEqual(Path(worktree_paths[0]).resolve(), repo.resolve())

    def test_json_report_has_all_required_fields_on_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=0, postcheck_exit=0)

            result = _run_gate(repo)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            report = _load_json(repo / GATE_REPORT_NAME)
            self.assertEqual(set(report.keys()), REQUIRED_REPORT_FIELDS)
            self.assertEqual(report["status"], "pass")
            self.assertIsInstance(report["worktree_path"], str)
            self.assertIsInstance(report["targets_run"], list)
            self.assertIsInstance(report["divergences"], list)
            self.assertIsNone(report["error"])
            self.assertIsInstance(report["exit_code"], int)

    def test_divergence_diff_included_in_report_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "consumer"
            _init_git_repo(repo)
            _write_makefile(repo, infra_validate_exit=0, postcheck_exit=1)

            # Add an untracked file to the working tree to simulate a bootstrap-created file
            # that is present locally but absent in a fresh worktree checkout.
            (repo / "scripts").mkdir(exist_ok=True)
            (repo / "scripts" / "bootstrap_output.sh").write_text(
                "#!/usr/bin/env bash\n# created by bootstrap\n",
                encoding="utf-8",
            )

            result = _run_gate(repo)
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            report = _load_json(repo / GATE_REPORT_NAME)
            self.assertEqual(report["status"], "fail")
            # The untracked bootstrap file should appear in divergences as missing_in_fresh_env
            divergences = report["divergences"]
            missing_files = {d["file"] for d in divergences if d["reason"] == "missing_in_fresh_env"}
            self.assertIn("scripts/bootstrap_output.sh", missing_files)


if __name__ == "__main__":
    unittest.main()
