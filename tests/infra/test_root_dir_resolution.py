from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT, run


ROOT_DIR_HELPER = REPO_ROOT / "scripts/lib/shell/root_dir.sh"
QUALITY_ROOT_DIR_PRELUDE_CHECK = REPO_ROOT / "scripts/bin/quality/check_root_dir_prelude.py"
TEMP_REPO_PATHS = ("Makefile", "make", "scripts")
DEFAULT_MODULE_ENV = {
    "OBSERVABILITY_ENABLED": "false",
    "WORKFLOWS_ENABLED": "false",
    "LANGFUSE_ENABLED": "false",
    "POSTGRES_ENABLED": "false",
    "NEO4J_ENABLED": "false",
    "OBJECT_STORAGE_ENABLED": "false",
    "RABBITMQ_ENABLED": "false",
    "DNS_ENABLED": "false",
    "PUBLIC_ENDPOINTS_ENABLED": "false",
    "SECRETS_MANAGER_ENABLED": "false",
    "KMS_ENABLED": "false",
    "IDENTITY_AWARE_PROXY_ENABLED": "false",
}


def _write_repo_markers(repo_root: Path) -> None:
    (repo_root / "scripts/lib").mkdir(parents=True, exist_ok=True)
    (repo_root / "Makefile").write_text("help:\n\t@echo ok\n", encoding="utf-8")


def _resolve_root_dir(start_dir: Path, *, env: dict[str, str] | None = None, cwd: Path | None = None):
    command = (
        f"source {shlex.quote(str(ROOT_DIR_HELPER))}; "
        f"resolve_root_dir {shlex.quote(str(start_dir))}"
    )
    return run(["bash", "-lc", command], env or {}, cwd=cwd or REPO_ROOT)


def _copy_tree(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _normalized_path(value: str) -> Path:
    return Path(value.strip()).resolve()


class RootDirResolutionTests(unittest.TestCase):
    def test_resolve_root_dir_prefers_valid_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            _write_repo_markers(repo_root)
            start_dir = repo_root / "nested" / "inside"
            start_dir.mkdir(parents=True, exist_ok=True)

            result = _resolve_root_dir(start_dir, env={"ROOT_DIR": str(repo_root)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_normalized_path(result.stdout), repo_root.resolve())

    def test_resolve_root_dir_ignores_invalid_env_and_falls_back_to_marker_walk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            _write_repo_markers(repo_root)
            start_dir = repo_root / "nested" / "deep"
            start_dir.mkdir(parents=True, exist_ok=True)

            invalid_root = Path(tmpdir) / "invalid"
            invalid_root.mkdir(parents=True, exist_ok=True)

            result = _resolve_root_dir(start_dir, env={"ROOT_DIR": str(invalid_root)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_normalized_path(result.stdout), repo_root.resolve())
            self.assertIn("ROOT_DIR is set but invalid", result.stderr)

    def test_resolve_root_dir_ignores_nonexistent_env_path_and_falls_back_to_marker_walk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            _write_repo_markers(repo_root)
            start_dir = repo_root / "nested" / "deep"
            start_dir.mkdir(parents=True, exist_ok=True)

            missing_root = Path(tmpdir) / "missing-root"

            result = _resolve_root_dir(start_dir, env={"ROOT_DIR": str(missing_root)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_normalized_path(result.stdout), repo_root.resolve())
            self.assertIn("ROOT_DIR is set but invalid", result.stderr)

    def test_resolve_root_dir_ignores_valid_env_when_start_dir_is_outside_env_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_root = Path(tmpdir) / "env-root"
            _write_repo_markers(env_root)

            target_root = Path(tmpdir) / "target-root"
            _write_repo_markers(target_root)
            start_dir = target_root / "nested"
            start_dir.mkdir(parents=True, exist_ok=True)

            result = _resolve_root_dir(start_dir, env={"ROOT_DIR": str(env_root)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_normalized_path(result.stdout), target_root.resolve())
            self.assertIn("ROOT_DIR is valid but ignored because start_dir is outside that root", result.stderr)

    def test_resolve_root_dir_uses_git_toplevel_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            _write_repo_markers(repo_root)
            start_dir = repo_root / "nested"
            start_dir.mkdir(parents=True, exist_ok=True)

            git_init = subprocess.run(
                ["git", "init", "-q"],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(git_init.returncode, 0, msg=git_init.stdout + git_init.stderr)

            result = _resolve_root_dir(start_dir, env={"ROOT_DIR": ""})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_normalized_path(result.stdout), repo_root.resolve())

    def test_resolve_root_dir_fails_when_unresolvable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            unresolved = Path(tmpdir) / "unresolved"
            unresolved.mkdir(parents=True, exist_ok=True)

            result = _resolve_root_dir(unresolved, env={"ROOT_DIR": ""})
            self.assertEqual(result.returncode, 1)
            self.assertIn("unable to resolve repository root", result.stderr)
            self.assertIn("checked ROOT_DIR env, git root, and marker walk-up", result.stderr)

    def test_render_makefile_works_from_non_git_temp_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_repo = Path(tmpdir) / "repo"
            for relative_path in TEMP_REPO_PATHS:
                _copy_tree(REPO_ROOT / relative_path, temp_repo / relative_path)

            self.assertFalse((temp_repo / ".git").exists())

            result = run(
                ["scripts/bin/blueprint/render_makefile.sh"],
                DEFAULT_MODULE_ENV,
                cwd=temp_repo,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            rendered_makefile = temp_repo / "make/blueprint.generated.mk"
            self.assertTrue(rendered_makefile.exists())
            self.assertIn(
                "quality-root-dir-prelude-check",
                rendered_makefile.read_text(encoding="utf-8"),
            )

    def test_quality_root_dir_prelude_check_passes_on_repository(self) -> None:
        result = run([sys.executable, str(QUALITY_ROOT_DIR_PRELUDE_CHECK)], cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_bootstrap_resolves_root_from_shell_lib_when_script_dir_is_unset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = Path(tmpdir) / "outside"
            outside.mkdir(parents=True, exist_ok=True)
            bootstrap_path = REPO_ROOT / "scripts/lib/shell/bootstrap.sh"
            command = (
                "unset SCRIPT_DIR; "
                f"source {shlex.quote(str(bootstrap_path))}; "
                "printf '%s\\n' \"$ROOT_DIR\""
            )
            result = run(["bash", "-lc", command], cwd=outside)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_normalized_path(result.stdout), REPO_ROOT.resolve())

    def test_quality_root_dir_prelude_check_blocks_inline_resolver_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            check_script = repo_root / "scripts/bin/quality/check_root_dir_prelude.py"
            check_script.parent.mkdir(parents=True, exist_ok=True)
            check_script.write_text(QUALITY_ROOT_DIR_PRELUDE_CHECK.read_text(encoding="utf-8"), encoding="utf-8")

            bad_script = repo_root / "scripts/bin/infra/bad.sh"
            bad_script.parent.mkdir(parents=True, exist_ok=True)
            bad_script.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
                "ROOT_DIR=\"$(cd \"$SCRIPT_DIR/../../..\" && pwd)\"\n"
                "source \"$ROOT_DIR/scripts/lib/shell/bootstrap.sh\"\n",
                encoding="utf-8",
            )

            result = run([sys.executable, str(check_script)], cwd=repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("inline ROOT_DIR resolver detected", result.stderr)
            self.assertIn("bootstrap sourced via $ROOT_DIR", result.stderr)


if __name__ == "__main__":
    unittest.main()
