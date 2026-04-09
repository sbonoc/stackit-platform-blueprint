from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


UPGRADE_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/upgrade_consumer.py"
RESYNC_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/resync_consumer_seeds.py"
DRIFT_REPORT_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/runtime_contract_drift_report.py"
FIXTURE_ROOT = REPO_ROOT / "tests/blueprint/fixtures/upgrade_matrix"
SOURCE_BASELINE_FIXTURE = FIXTURE_ROOT / "source_baseline"
SOURCE_HEAD_FIXTURE = FIXTURE_ROOT / "source_head"
TARGET_LEGACY_FIXTURE = FIXTURE_ROOT / "target_legacy_consumer"

APP_RUNTIME_REQUIRED_PATHS = (
    "infra/gitops/platform/base/apps",
)
APP_RUNTIME_REQUIRED_FILES = (
    "infra/gitops/platform/base/apps/kustomization.yaml",
    "infra/gitops/platform/base/apps/backend-api-deployment.yaml",
    "infra/gitops/platform/base/apps/backend-api-service.yaml",
    "infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml",
    "infra/gitops/platform/base/apps/touchpoints-web-service.yaml",
)
LOCAL_POST_DEPLOY_REQUIRED_PATHS = (
    "scripts/bin/infra/provision_deploy.sh",
    "scripts/lib/infra/local_post_deploy_hook.sh",
    "scripts/lib/infra/schemas/local_post_deploy_hook_state.schema.json",
    "make/platform.mk",
)


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return run_command(cmd, cwd=cwd, env=env)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo)


def _require_success(result: subprocess.CompletedProcess[str], command: str) -> None:
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({command}) exit={result.returncode}\\nstdout:\\n{result.stdout}\\nstderr:\\n{result.stderr}"
        )


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _require_success(_git(repo, "init"), "git init")
    _require_success(_git(repo, "config", "user.email", "tests@example.com"), "git config user.email")
    _require_success(_git(repo, "config", "user.name", "Blueprint Tests"), "git config user.name")


def _commit_all(repo: Path, message: str) -> None:
    _require_success(_git(repo, "add", "."), "git add .")
    _require_success(_git(repo, "commit", "-m", message), f"git commit -m {message}")


def _copy_fixture_tree(source: Path, destination: Path) -> None:
    for entry in sorted(source.rglob("*")):
        if not entry.is_file():
            continue
        relative = entry.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry, target)


def _template_version() -> str:
    contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
    return contract.repository.template_bootstrap.template_version


def _generated_contract_text() -> str:
    return (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
        "repo_mode: template-source",
        "repo_mode: generated-consumer",
        1,
    )


def _materialize_consumer_templates(target_repo: Path) -> None:
    contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
    template_root = REPO_ROOT / "scripts/templates/consumer/init"
    for relative_path in contract.repository.consumer_seeded_paths:
        template_path = template_root / f"{relative_path}.tmpl"
        _write(
            target_repo / "scripts/templates/consumer/init" / f"{relative_path}.tmpl",
            template_path.read_text(encoding="utf-8"),
        )


def _create_source_repo(tmp_root: Path) -> Path:
    source_repo = tmp_root / "source"
    _init_git_repo(source_repo)

    _copy_fixture_tree(SOURCE_BASELINE_FIXTURE, source_repo)
    _commit_all(source_repo, "baseline")
    _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")

    _copy_fixture_tree(SOURCE_HEAD_FIXTURE, source_repo)
    _commit_all(source_repo, "head")
    return source_repo


def _create_target_repo(tmp_root: Path) -> Path:
    target_repo = tmp_root / "target"
    _init_git_repo(target_repo)

    _write(target_repo / "blueprint/contract.yaml", _generated_contract_text())
    _write(target_repo / ".gitignore", "artifacts/\\n")
    _copy_fixture_tree(TARGET_LEGACY_FIXTURE, target_repo)
    _materialize_consumer_templates(target_repo)
    _commit_all(target_repo, "legacy generated consumer snapshot")

    return target_repo


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_result(apply_report: dict[str, object], relative_path: str) -> dict[str, object]:
    results = apply_report.get("results", [])
    if not isinstance(results, list):
        raise AssertionError("apply results should be a list")
    for result in results:
        if isinstance(result, dict) and result.get("path") == relative_path:
            return result
    raise AssertionError(f"missing apply result for {relative_path}")


def _run_upgrade_and_resync(source_repo: Path, target_repo: Path) -> dict[str, object]:
    resync_dry_run = _run(
        [
            sys.executable,
            str(RESYNC_SCRIPT),
            "--repo-root",
            str(target_repo),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
    )
    _require_success(resync_dry_run, "resync dry-run")

    resync_apply_safe = _run(
        [
            sys.executable,
            str(RESYNC_SCRIPT),
            "--repo-root",
            str(target_repo),
            "--apply-safe",
        ],
        cwd=REPO_ROOT,
    )
    _require_success(resync_apply_safe, "resync apply-safe")
    _commit_all(target_repo, "resync consumer seeds before upgrade")

    plan = _run(
        [
            sys.executable,
            str(UPGRADE_SCRIPT),
            "--repo-root",
            str(target_repo),
            "--source",
            str(source_repo),
            "--ref",
            "HEAD",
        ],
        cwd=REPO_ROOT,
    )
    _require_success(plan, "upgrade plan")

    apply = _run(
        [
            sys.executable,
            str(UPGRADE_SCRIPT),
            "--repo-root",
            str(target_repo),
            "--source",
            str(source_repo),
            "--ref",
            "HEAD",
            "--apply",
            "--allow-dirty",
        ],
        cwd=REPO_ROOT,
    )
    _require_success(apply, "upgrade apply")

    return _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")


def _run_drift_report(target_repo: Path, *, env_overrides: dict[str, str]) -> dict[str, object]:
    report_path = target_repo / "artifacts/blueprint/runtime_contract_drift_report.json"
    env = os.environ.copy()
    env.update(env_overrides)

    result = _run(
        [
            sys.executable,
            str(DRIFT_REPORT_SCRIPT),
            "--repo-root",
            str(target_repo),
            "--output",
            str(report_path),
            "--strict",
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    _require_success(result, f"runtime contract drift report strict ({env_overrides})")
    return _load_json(report_path)


class UpgradeFixtureMatrixTests(unittest.TestCase):
    def test_upgrade_matrix_legacy_snapshots_cover_disabled_and_enabled_runtime_contracts(self) -> None:
        scenarios = (
            (
                "features-disabled",
                {
                    "APP_RUNTIME_GITOPS_ENABLED": "false",
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED": "false",
                    "EVENT_MESSAGING_BASELINE_ENABLED": "false",
                    "ZERO_DOWNTIME_EVOLUTION_ENABLED": "false",
                    "TENANT_CONTEXT_PROPAGATION_ENABLED": "false",
                },
            ),
            (
                "features-enabled",
                {
                    "APP_RUNTIME_GITOPS_ENABLED": "true",
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED": "true",
                    "EVENT_MESSAGING_BASELINE_ENABLED": "true",
                    "ZERO_DOWNTIME_EVOLUTION_ENABLED": "true",
                    "TENANT_CONTEXT_PROPAGATION_ENABLED": "true",
                },
            ),
        )

        for name, env_overrides in scenarios:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_root = Path(tmpdir)
                    source_repo = _create_source_repo(tmp_root)
                    target_repo = _create_target_repo(tmp_root)

                    apply_report = _run_upgrade_and_resync(source_repo, target_repo)
                    required_manual_actions = apply_report.get("required_manual_actions", [])
                    self.assertEqual(required_manual_actions, [])
                    self.assertEqual(apply_report.get("summary", {}).get("required_manual_action_count"), 0)

                    for required_path in APP_RUNTIME_REQUIRED_FILES + LOCAL_POST_DEPLOY_REQUIRED_PATHS:
                        result = _apply_result(apply_report, required_path)
                        self.assertIn(
                            result.get("result"),
                            {"applied", "updated", "merged", "skipped"},
                            msg=f"unexpected upgrade apply result for {required_path}: {result}",
                        )
                    for required_path in APP_RUNTIME_REQUIRED_PATHS + APP_RUNTIME_REQUIRED_FILES + LOCAL_POST_DEPLOY_REQUIRED_PATHS:
                        self.assertTrue(
                            (target_repo / required_path).exists(),
                            msg=f"expected upgraded path missing from target repo: {required_path}",
                        )

                    drift_report = _run_drift_report(target_repo, env_overrides=env_overrides)
                    self.assertEqual(drift_report.get("status"), "in-sync")
                    self.assertEqual(drift_report.get("totalDriftCount"), 0)

                    runtime_contracts = drift_report.get("runtimeContracts", {})
                    self.assertIsInstance(runtime_contracts, dict)
                    app_runtime_contract = runtime_contracts.get("app_runtime_gitops_contract", {})
                    local_post_contract = runtime_contracts.get("local_post_deploy_hook_contract", {})
                    self.assertEqual(
                        bool(app_runtime_contract.get("enabled")),
                        env_overrides["APP_RUNTIME_GITOPS_ENABLED"].lower() == "true",
                    )
                    self.assertEqual(
                        bool(local_post_contract.get("enabled")),
                        env_overrides["LOCAL_POST_DEPLOY_HOOK_ENABLED"].lower() == "true",
                    )
                    self.assertEqual(app_runtime_contract.get("missingDocsPaths"), [])
                    self.assertEqual(local_post_contract.get("missingDocsPaths"), [])
                    self.assertEqual(app_runtime_contract.get("missingRequiredPaths"), [])
                    self.assertEqual(local_post_contract.get("missingRequiredPaths"), [])


if __name__ == "__main__":
    unittest.main()
