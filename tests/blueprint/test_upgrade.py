from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests._shared.helpers import module_flags_env


REPO_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE_SMOKE_INIT_ENV = {
    "BLUEPRINT_REPO_NAME": "test-smoke-blueprint",
    "BLUEPRINT_GITHUB_ORG": "test-smoke-org",
    "BLUEPRINT_GITHUB_REPO": "test-smoke-blueprint",
    "BLUEPRINT_DEFAULT_BRANCH": "main",
}

TEMPLATE_SMOKE_SCENARIOS = (
    ("local-lite-baseline", module_flags_env(profile="local-lite")),
    (
        "local-full-observability-data",
        module_flags_env(profile="local-full", observability="true", postgres="true", object_storage="true"),
    ),
    (
        "local-full-runtime-edge",
        module_flags_env(
            profile="local-full",
            rabbitmq="true",
            public_endpoints="true",
            identity_aware_proxy="true",
        ),
    ),
    (
        "stackit-dev-managed-services",
        module_flags_env(
            profile="stackit-dev",
            observability="true",
            postgres="true",
            object_storage="true",
            rabbitmq="true",
            dns="true",
            secrets_manager="true",
            kms="true",
        ),
    ),
    (
        "stackit-dev-runtime-fallbacks",
        module_flags_env(
            profile="stackit-dev",
            langfuse="true",
            neo4j="true",
            public_endpoints="true",
            identity_aware_proxy="true",
        ),
    ),
    (
        "stackit-dev-workflows",
        module_flags_env(profile="stackit-dev", observability="true", workflows="true"),
    ),
)


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


def _template_smoke_env(scenario_name: str, env_overrides: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(TEMPLATE_SMOKE_INIT_ENV)
    env.update(env_overrides)
    env["BLUEPRINT_TEMPLATE_SMOKE_SCENARIO"] = scenario_name
    env["DRY_RUN"] = "true"
    return env


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

    def test_blueprint_template_smoke_supports_representative_profile_module_matrix(self) -> None:
        for scenario_name, env_overrides in TEMPLATE_SMOKE_SCENARIOS:
            with self.subTest(scenario=scenario_name):
                result = subprocess.run(
                    ["make", "blueprint-template-smoke"],
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                    env=_template_smoke_env(scenario_name, env_overrides),
                )
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertIn(f"scenario={scenario_name}", result.stdout)


if __name__ == "__main__":
    unittest.main()
