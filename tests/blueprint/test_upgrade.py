from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _contract_with_template_version(template_version: str) -> str:
    return f"""apiVersion: blueprint.contract/v1alpha1
kind: PlatformBlueprintContract
metadata:
  name: migration-fixture
  version: 1.0.0
spec:
  repository:
    default_branch: main
    branch_naming:
      model: github-flow
      purpose_prefixes:
        - feature/
        - fix/
        - chore/
        - docs/
    template_bootstrap:
      model: github-template
      template_version: {template_version}
      minimum_supported_upgrade_from: 1.0.0
      init_command: make blueprint-init-repo
      upgrade_command: make blueprint-migrate
      example_env_file: blueprint/repo.init.example.env
      required_inputs:
        - BLUEPRINT_REPO_NAME
    required_files:
      - Makefile
  structure:
    required_paths:
      - scripts/bin/
"""


class BlueprintUpgradeTests(unittest.TestCase):
    def test_migrate_repo_is_noop_for_current_template_version(self) -> None:
        migrate_script = REPO_ROOT / "scripts/lib/blueprint/migrate_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            contract_path = tmp_root / "blueprint/contract.yaml"
            contract_path.write_text(_read("blueprint/contract.yaml"), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(migrate_script), "--repo-root", str(tmp_root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("no migrations were required", result.stdout)
            self.assertIn("source and target template version: 1.0.0", result.stdout)

    def test_migrate_repo_fails_when_source_version_is_below_minimum_supported(self) -> None:
        migrate_script = REPO_ROOT / "scripts/lib/blueprint/migrate_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/contract.yaml").write_text(
                _contract_with_template_version("0.9.0"),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(migrate_script), "--repo-root", str(tmp_root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("unsupported upgrade path", result.stderr)
            self.assertIn("minimum supported upgrade version 1.0.0", result.stderr)

    def test_migrate_repo_fails_when_source_version_is_newer_than_target(self) -> None:
        migrate_script = REPO_ROOT / "scripts/lib/blueprint/migrate_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/contract.yaml").write_text(
                _contract_with_template_version("1.0.5"),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(migrate_script), "--repo-root", str(tmp_root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("unsupported upgrade path", result.stderr)
            self.assertIn("source version is newer than target version", result.stderr)

    def test_blueprint_migrate_make_target_smoke_in_template_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            tmp_repo = tmp_root / "repo"
            shutil.copytree(
                REPO_ROOT,
                tmp_repo,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".pytest_cache",
                    "artifacts",
                    "docs/build",
                    "docs/.docusaurus",
                    "docs/node_modules",
                    "__pycache__",
                ),
            )

            first = subprocess.run(
                ["make", "blueprint-migrate"],
                cwd=tmp_repo,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
            self.assertIn("no migrations were required", first.stdout)

            second = subprocess.run(
                ["make", "blueprint-migrate"],
                cwd=tmp_repo,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
            self.assertIn("no migrations were required", second.stdout)


if __name__ == "__main__":
    unittest.main()
