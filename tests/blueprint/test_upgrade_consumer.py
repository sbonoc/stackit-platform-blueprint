from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.lib.blueprint import upgrade_consumer
from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.exec import run_command
from tests._shared.json_schema import assert_json_matches_schema, load_json_schema
from tests._shared.helpers import REPO_ROOT


UPGRADE_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/upgrade_consumer.py"
VALIDATE_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/upgrade_consumer_validate.py"
PLAN_SCHEMA = REPO_ROOT / "scripts/lib/blueprint/schemas/upgrade_plan.schema.json"
APPLY_SCHEMA = REPO_ROOT / "scripts/lib/blueprint/schemas/upgrade_apply.schema.json"
VALIDATE_SCHEMA = REPO_ROOT / "scripts/lib/blueprint/schemas/upgrade_validate.schema.json"
MANAGED_TEST_PATH = "scripts/bin/blueprint/bootstrap.sh"
PROTECTED_TEST_PATH = "docs/platform/consumer/quickstart.md"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return run_command(cmd, cwd=cwd)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo)


def _require_success(result: subprocess.CompletedProcess[str], command: str) -> None:
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({command}) exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _require_success(_git(repo, "init"), "git init")
    _require_success(_git(repo, "config", "user.email", "tests@example.com"), "git config user.email")
    _require_success(_git(repo, "config", "user.name", "Blueprint Tests"), "git config user.name")


def _commit_all(repo: Path, message: str) -> None:
    _require_success(_git(repo, "add", "."), "git add .")
    _require_success(_git(repo, "commit", "-m", message), f"git commit -m {message}")


def _contract_text_for_repo_mode(repo_mode: str, *, drop_paths: tuple[str, ...] = ()) -> str:
    content = (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
        "repo_mode: template-source",
        f"repo_mode: {repo_mode}",
        1,
    )
    drop_set = set(drop_paths)
    filtered_lines: list[str] = []
    in_required_files = False
    for line in content.splitlines(keepends=True):
        if line.startswith("    required_files:"):
            in_required_files = True
            filtered_lines.append(line)
            continue

        if in_required_files and line.startswith("    ") and not line.startswith("      - "):
            in_required_files = False

        if in_required_files and line.startswith("      - "):
            candidate = line.strip()[2:].strip()
            if candidate in drop_set:
                continue

        filtered_lines.append(line)
    return "".join(filtered_lines)


def _generated_contract_text(*, drop_paths: tuple[str, ...] = ()) -> str:
    return _contract_text_for_repo_mode("generated-consumer", drop_paths=drop_paths)


def _template_version() -> str:
    contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
    return contract.repository.template_bootstrap.template_version


def _create_source_repo(root: Path, relative_path: str, base_content: str, head_content: str) -> Path:
    source_repo = root / "source"
    _init_git_repo(source_repo)
    _write(source_repo / relative_path, base_content)
    _commit_all(source_repo, "baseline")
    _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")

    _write(source_repo / relative_path, head_content)
    _commit_all(source_repo, "head")
    return source_repo


def _create_generated_repo(root: Path, relative_path: str, content: str, *, contract_text: str | None = None) -> Path:
    target_repo = root / "target"
    _init_git_repo(target_repo)
    _write(target_repo / "blueprint/contract.yaml", contract_text or _generated_contract_text())
    _write(target_repo / ".gitignore", "artifacts/\n")
    _write(target_repo / relative_path, content)
    _commit_all(target_repo, "initial generated")
    return target_repo


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_json_schema(payload: dict[str, object], schema_path: Path) -> None:
    schema = load_json_schema(schema_path)
    assert_json_matches_schema(payload, schema)


def _plan_entry(plan: dict[str, object], relative_path: str) -> dict[str, object]:
    entries = plan.get("entries", [])
    if not isinstance(entries, list):
        raise AssertionError("plan entries should be a list")
    for entry in entries:
        if isinstance(entry, dict) and entry.get("path") == relative_path:
            return entry
    raise AssertionError(f"missing plan entry for {relative_path}")


def _apply_result(apply_report: dict[str, object], relative_path: str) -> dict[str, object]:
    results = apply_report.get("results", [])
    if not isinstance(results, list):
        raise AssertionError("apply results should be a list")
    for result in results:
        if isinstance(result, dict) and result.get("path") == relative_path:
            return result
    raise AssertionError(f"missing apply result for {relative_path}")


class UpgradeConsumerTests(unittest.TestCase):
    def test_dry_run_is_deterministic_and_preserves_target_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = _create_source_repo(
                tmp_root,
                MANAGED_TEST_PATH,
                "baseline\n",
                "baseline\nupstream-change\n",
            )
            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")

            cmd = [
                sys.executable,
                str(UPGRADE_SCRIPT),
                "--repo-root",
                str(target_repo),
                "--source",
                str(source_repo),
                "--ref",
                "HEAD",
            ]
            first = _run(cmd, cwd=REPO_ROOT)
            first_plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            second = _run(cmd, cwd=REPO_ROOT)
            second_plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")

            self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
            self.assertEqual((target_repo / MANAGED_TEST_PATH).read_text(encoding="utf-8"), "baseline\n")
            self.assertEqual(first_plan, second_plan)
            self.assertEqual(first_plan.get("summary", {}).get("total"), second_plan.get("summary", {}).get("total"))
            self.assertEqual(first_plan.get("required_manual_actions"), [])
            self.assertEqual(first_plan.get("summary", {}).get("required_manual_action_count"), 0)
            _assert_json_schema(first_plan, PLAN_SCHEMA)
            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            self.assertEqual(apply_report.get("required_manual_actions"), [])
            self.assertEqual(apply_report.get("summary", {}).get("required_manual_action_count"), 0)
            _assert_json_schema(apply_report, APPLY_SCHEMA)

    def test_dirty_worktree_requires_allow_dirty_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = _create_source_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n", "head\n")
            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(target_repo / MANAGED_TEST_PATH, "dirty local change\n")

            deny = _run(
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
            allow = _run(
                [
                    sys.executable,
                    str(UPGRADE_SCRIPT),
                    "--repo-root",
                    str(target_repo),
                    "--source",
                    str(source_repo),
                    "--ref",
                    "HEAD",
                    "--allow-dirty",
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(deny.returncode, 1)
            self.assertIn("refusing upgrade on dirty worktree", deny.stderr)
            self.assertEqual(allow.returncode, 0, msg=allow.stdout + allow.stderr)

    def test_platform_owned_paths_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = _create_source_repo(
                tmp_root,
                PROTECTED_TEST_PATH,
                "baseline\n",
                "baseline\nupstream\n",
            )
            target_repo = _create_generated_repo(tmp_root, PROTECTED_TEST_PATH, "baseline\nlocal\n")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            entry = _plan_entry(plan, PROTECTED_TEST_PATH)
            self.assertEqual(entry.get("action"), "skip")
            self.assertIn("platform-owned", str(entry.get("reason", "")))

    def test_upgrade_fails_when_baseline_ref_collides_with_target_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            version_tag = f"v{_template_version()}"
            _require_success(_git(source_repo, "tag", version_tag), "git tag template version")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\nlocal-change\n")
            result = _run(
                [
                    sys.executable,
                    str(UPGRADE_SCRIPT),
                    "--repo-root",
                    str(target_repo),
                    "--source",
                    str(source_repo),
                    "--ref",
                    version_tag,
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("upgrade baseline collision", result.stderr)
            self.assertIn(f"baseline ref {version_tag}", result.stderr)
            self.assertFalse((target_repo / "artifacts/blueprint/upgrade_plan.json").exists())
            self.assertFalse((target_repo / "artifacts/blueprint/upgrade_apply.json").exists())

    def test_upgrade_plan_flags_manual_action_for_missing_protected_runtime_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(
                source_repo / "scripts/bin/infra/smoke.sh",
                "run_cmd \"$ROOT_DIR/scripts/bin/platform/auth/reconcile_runtime_identity.sh\"\n",
            )
            _write(
                source_repo / "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
                "#!/usr/bin/env bash\necho ok\n",
            )
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(
                source_repo / "scripts/bin/infra/smoke.sh",
                "echo warmup\nrun_cmd \"$ROOT_DIR/scripts/bin/platform/auth/reconcile_runtime_identity.sh\"\n",
            )
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, "scripts/bin/infra/smoke.sh", "echo warmup\n")
            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            dependency_entry = _plan_entry(
                plan,
                "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
            )
            self.assertEqual(dependency_entry.get("action"), "skip")
            self.assertIn("required-manual-action", str(dependency_entry.get("reason", "")))
            self.assertIn("scripts/bin/infra/smoke.sh", str(dependency_entry.get("reason", "")))
            required_manual_actions = plan.get("required_manual_actions", [])
            self.assertEqual(len(required_manual_actions), 1)
            self.assertEqual(
                required_manual_actions[0].get("dependency_path"),
                "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
            )
            self.assertEqual(
                required_manual_actions[0].get("dependency_of"),
                "scripts/bin/infra/smoke.sh",
            )
            self.assertIn(
                "make blueprint-upgrade-consumer-validate",
                required_manual_actions[0].get("required_follow_up_commands", []),
            )
            self.assertEqual(plan.get("summary", {}).get("required_manual_action_count"), 1)

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            self.assertEqual(len(apply_report.get("required_manual_actions", [])), 1)
            self.assertEqual(apply_report.get("summary", {}).get("required_manual_action_count"), 1)

            summary_path = target_repo / "artifacts/blueprint/upgrade_summary.md"
            self.assertTrue(summary_path.is_file())
            summary_content = summary_path.read_text(encoding="utf-8")
            self.assertIn("## Required Manual Actions", summary_content)
            self.assertIn("scripts/bin/infra/smoke.sh", summary_content)
            self.assertIn("scripts/bin/platform/auth/reconcile_runtime_identity.sh", summary_content)
            self.assertIn("- Applied paths: `0`", summary_content)
            self.assertNotIn("| applied_count |", summary_content)
            self.assertNotIn("| required_manual_action_count |", summary_content)

    def test_upgrade_plan_skips_manual_action_when_source_depender_no_longer_references_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(
                source_repo / "scripts/bin/infra/smoke.sh",
                "echo warmup\n",
            )
            _write(
                source_repo / "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
                "#!/usr/bin/env bash\necho ok\n",
            )
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / "README.md", "head update\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, "scripts/bin/infra/smoke.sh", "echo warmup\n")
            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            dependency_entry = _plan_entry(
                plan,
                "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
            )
            self.assertEqual(dependency_entry.get("action"), "skip")
            self.assertNotIn("required-manual-action", str(dependency_entry.get("reason", "")))
            self.assertEqual(plan.get("required_manual_actions"), [])
            self.assertEqual(plan.get("summary", {}).get("required_manual_action_count"), 0)

    def test_upgrade_plan_flags_manual_action_for_missing_platform_ci_bootstrap_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(
                source_repo / "blueprint/contract.yaml",
                (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"),
            )
            _write(
                source_repo / ".github/actions/prepare-blueprint-ci/action.yml",
                (REPO_ROOT / ".github/actions/prepare-blueprint-ci/action.yml").read_text(encoding="utf-8"),
            )
            _write(
                source_repo / "make/platform.mk",
                (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"),
            )
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(
                target_repo / "make/platform.mk",
                (
                    "# Platform-owned Make targets.\n"
                    "\n"
                    ".PHONY: apps-bootstrap\n"
                    "\n"
                    "apps-bootstrap:\n"
                    "\t@echo bootstrap\n"
                ),
            )
            _commit_all(target_repo, "legacy platform make target set")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            required_manual_actions = plan.get("required_manual_actions", [])
            ci_bootstrap_action = None
            for action in required_manual_actions:
                if not isinstance(action, dict):
                    continue
                if action.get("dependency_path") != "make/platform.mk":
                    continue
                if "apps-ci-bootstrap" not in str(action.get("dependency_of", "")):
                    continue
                ci_bootstrap_action = action
                break

            self.assertIsNotNone(ci_bootstrap_action, msg=f"missing apps-ci-bootstrap manual action: {required_manual_actions}")
            self.assertIn(
                ".github/actions/prepare-blueprint-ci/action.yml",
                str(ci_bootstrap_action.get("dependency_of", "")),
            )
            self.assertIn(
                "required make target `apps-ci-bootstrap` is missing",
                str(ci_bootstrap_action.get("reason", "")),
            )
            self.assertIn(
                "make blueprint-upgrade-consumer-validate",
                ci_bootstrap_action.get("required_follow_up_commands", []),
            )
            self.assertGreaterEqual(plan.get("summary", {}).get("required_manual_action_count", 0), 1)
            self.assertEqual(
                plan.get("summary", {}).get("required_manual_action_count"),
                len(required_manual_actions),
            )

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            apply_manual_actions = apply_report.get("required_manual_actions", [])
            self.assertGreaterEqual(len(apply_manual_actions), 1)
            self.assertEqual(
                apply_report.get("summary", {}).get("required_manual_action_count"),
                len(apply_manual_actions),
            )

    def test_upgrade_plan_flags_manual_action_for_missing_required_consumer_make_target_from_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)

            source_contract = (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
                "      - quality-hardening-review\n",
                "      - quality-hardening-review\n      - consumer-upgrade-prereq\n",
                1,
            )
            _write(source_repo / "blueprint/contract.yaml", source_contract)
            _write(source_repo / "make/platform.mk", (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"))
            _write(
                source_repo / "make/platform/consumer_upgrade.mk",
                (
                    ".PHONY: consumer-upgrade-prereq\n"
                    "\n"
                    "consumer-upgrade-prereq:\n"
                    "\t@echo consumer upgrade prerequisite target\n"
                ),
            )
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(target_repo / "make/platform.mk", (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"))
            _commit_all(target_repo, "target missing new consumer required target")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            required_manual_actions = plan.get("required_manual_actions", [])
            missing_target_action = None
            for action in required_manual_actions:
                if not isinstance(action, dict):
                    continue
                if "consumer-upgrade-prereq" not in str(action.get("reason", "")):
                    continue
                missing_target_action = action
                break

            self.assertIsNotNone(
                missing_target_action,
                msg=f"missing contract-required consumer make target action: {required_manual_actions}",
            )
            self.assertEqual(missing_target_action.get("dependency_path"), "make/platform.mk")
            self.assertIn(
                "blueprint/contract.yaml: spec.make_contract.required_targets",
                str(missing_target_action.get("dependency_of", "")),
            )
            self.assertIn(
                "required make target `consumer-upgrade-prereq` is missing",
                str(missing_target_action.get("reason", "")),
            )
            self.assertIn(
                "`make/platform.mk` or linked includes under `make/platform/*.mk`",
                str(missing_target_action.get("reason", "")),
            )

    def test_upgrade_plan_treats_nested_platform_make_includes_as_missing_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)

            source_contract = (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
                "      - quality-hardening-review\n",
                "      - quality-hardening-review\n      - nested-only-target\n",
                1,
            )
            _write(source_repo / "blueprint/contract.yaml", source_contract)
            _write(source_repo / "make/platform.mk", (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"))
            _write(
                source_repo / "make/platform/base.mk",
                ".PHONY: nested-only-target\nnested-only-target:\n\t@echo nested source target\n",
            )
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(target_repo / "make/platform.mk", (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"))
            _write(
                target_repo / "make/platform/nested/custom.mk",
                ".PHONY: nested-only-target\nnested-only-target:\n\t@echo nested target only\n",
            )
            _commit_all(target_repo, "target defines nested-only-target in nested include only")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            required_manual_actions = plan.get("required_manual_actions", [])
            nested_target_action = None
            for action in required_manual_actions:
                if not isinstance(action, dict):
                    continue
                if "nested-only-target" not in str(action.get("reason", "")):
                    continue
                nested_target_action = action
                break

            self.assertIsNotNone(
                nested_target_action,
                msg=f"missing manual action for nested-only-target: {required_manual_actions}",
            )
            self.assertEqual(nested_target_action.get("dependency_path"), "make/platform.mk")
            self.assertIn(
                "define `nested-only-target` in `make/platform.mk` or linked includes under `make/platform/*.mk`",
                str(nested_target_action.get("reason", "")),
            )

    def test_upgrade_plan_flags_manual_action_for_placeholder_platform_ci_bootstrap_consumer_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(
                source_repo / "blueprint/contract.yaml",
                (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"),
            )
            _write(
                source_repo / ".github/actions/prepare-blueprint-ci/action.yml",
                (REPO_ROOT / ".github/actions/prepare-blueprint-ci/action.yml").read_text(encoding="utf-8"),
            )
            _write(
                source_repo / "make/platform.mk",
                (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"),
            )
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(
                target_repo / "make/platform.mk",
                (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"),
            )
            _commit_all(target_repo, "consumer makefile still uses placeholder ci bootstrap target")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            required_manual_actions = plan.get("required_manual_actions", [])
            ci_bootstrap_consumer_action = None
            for action in required_manual_actions:
                if not isinstance(action, dict):
                    continue
                if action.get("dependency_path") != "make/platform.mk":
                    continue
                if "apps-ci-bootstrap-consumer" not in str(action.get("reason", "")):
                    continue
                ci_bootstrap_consumer_action = action
                break

            self.assertIsNotNone(
                ci_bootstrap_consumer_action,
                msg=f"missing apps-ci-bootstrap-consumer manual action: {required_manual_actions}",
            )
            self.assertIn(
                "make apps-ci-bootstrap",
                str(ci_bootstrap_consumer_action.get("dependency_of", "")),
            )
            self.assertIn(
                "required consumer-owned make target `apps-ci-bootstrap-consumer` is still placeholder",
                str(ci_bootstrap_consumer_action.get("reason", "")),
            )
            self.assertIn(
                "make blueprint-upgrade-consumer-validate",
                ci_bootstrap_consumer_action.get("required_follow_up_commands", []),
            )
            self.assertEqual(plan.get("summary", {}).get("required_manual_action_count"), 1)

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            apply_manual_actions = apply_report.get("required_manual_actions", [])
            self.assertEqual(len(apply_manual_actions), 1)
            self.assertEqual(apply_report.get("summary", {}).get("required_manual_action_count"), 1)

    def test_upgrade_plan_flags_manual_action_for_placeholder_local_post_deploy_consumer_target_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(
                source_repo / "blueprint/contract.yaml",
                (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"),
            )
            _write(
                source_repo / "scripts/bin/infra/provision_deploy.sh",
                (REPO_ROOT / "scripts/bin/infra/provision_deploy.sh").read_text(encoding="utf-8"),
            )
            _write(source_repo / "make/platform.mk", (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"))
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(
                target_repo / "make/platform.mk",
                (
                    "# Platform-owned Make targets.\n"
                    "\n"
                    ".PHONY: apps-ci-bootstrap apps-ci-bootstrap-consumer infra-post-deploy-consumer\n"
                    "\n"
                    "apps-ci-bootstrap:\n"
                    "\t@$(MAKE) apps-ci-bootstrap-consumer\n"
                    "\n"
                    "apps-ci-bootstrap-consumer:\n"
                    "\t@echo consumer-ci-bootstrap-implemented\n"
                    "\n"
                    "infra-post-deploy-consumer:\n"
                    "\t@echo \"[blueprint] infra-post-deploy-consumer placeholder active; implement deterministic local post-deploy reconciliation commands in make/platform.mk and set LOCAL_POST_DEPLOY_HOOK_ENABLED=true when ready\" >&2\n"
                    "\t@exit 1\n"
                ),
            )
            _write(
                target_repo / "blueprint/repo.init.env",
                (REPO_ROOT / "blueprint/repo.init.env").read_text(encoding="utf-8").replace(
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED=false",
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED=true",
                    1,
                ),
            )
            _commit_all(target_repo, "consumer post-deploy hook still placeholder while enabled")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            required_manual_actions = plan.get("required_manual_actions", [])
            post_deploy_action = None
            for action in required_manual_actions:
                if not isinstance(action, dict):
                    continue
                if action.get("dependency_path") != "make/platform.mk":
                    continue
                if "infra-post-deploy-consumer" not in str(action.get("reason", "")):
                    continue
                post_deploy_action = action
                break

            self.assertIsNotNone(post_deploy_action, msg=f"missing post-deploy manual action: {required_manual_actions}")
            self.assertIn(
                "scripts/bin/infra/provision_deploy.sh",
                str(post_deploy_action.get("dependency_of", "")),
            )
            self.assertIn(
                "LOCAL_POST_DEPLOY_HOOK_CMD",
                str(post_deploy_action.get("dependency_of", "")),
            )
            self.assertIn(
                "required consumer-owned make target `infra-post-deploy-consumer` is still placeholder",
                str(post_deploy_action.get("reason", "")),
            )
            self.assertIn(
                "LOCAL_POST_DEPLOY_HOOK_ENABLED=true",
                str(post_deploy_action.get("reason", "")),
            )
            self.assertIn(
                "make blueprint-upgrade-consumer-validate",
                post_deploy_action.get("required_follow_up_commands", []),
            )

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            apply_actions = apply_report.get("required_manual_actions", [])
            self.assertTrue(
                any(
                    isinstance(action, dict)
                    and "infra-post-deploy-consumer" in str(action.get("reason", ""))
                    for action in apply_actions
                ),
                msg=f"missing apply manual action for infra-post-deploy-consumer: {apply_actions}",
            )

    def test_upgrade_plan_does_not_flag_placeholder_local_post_deploy_consumer_target_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)
            _write(
                source_repo / "blueprint/contract.yaml",
                (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"),
            )
            _write(
                source_repo / "scripts/bin/infra/provision_deploy.sh",
                (REPO_ROOT / "scripts/bin/infra/provision_deploy.sh").read_text(encoding="utf-8"),
            )
            _write(source_repo / "make/platform.mk", (REPO_ROOT / "make/platform.mk").read_text(encoding="utf-8"))
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            _write(
                target_repo / "make/platform.mk",
                (
                    "# Platform-owned Make targets.\n"
                    "\n"
                    ".PHONY: apps-ci-bootstrap apps-ci-bootstrap-consumer infra-post-deploy-consumer\n"
                    "\n"
                    "apps-ci-bootstrap:\n"
                    "\t@$(MAKE) apps-ci-bootstrap-consumer\n"
                    "\n"
                    "apps-ci-bootstrap-consumer:\n"
                    "\t@echo consumer-ci-bootstrap-implemented\n"
                    "\n"
                    "infra-post-deploy-consumer:\n"
                    "\t@echo \"[blueprint] infra-post-deploy-consumer placeholder active; implement deterministic local post-deploy reconciliation commands in make/platform.mk and set LOCAL_POST_DEPLOY_HOOK_ENABLED=true when ready\" >&2\n"
                    "\t@exit 1\n"
                ),
            )
            _write(
                target_repo / "blueprint/repo.init.env",
                (REPO_ROOT / "blueprint/repo.init.env").read_text(encoding="utf-8").replace(
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED=true",
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED=false",
                    1,
                ),
            )
            _commit_all(target_repo, "consumer post-deploy hook placeholder but disabled")

            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            required_manual_actions = plan.get("required_manual_actions", [])
            self.assertFalse(
                any(
                    isinstance(action, dict)
                    and "infra-post-deploy-consumer" in str(action.get("reason", ""))
                    for action in required_manual_actions
                ),
                msg=f"unexpected post-deploy manual action while hook disabled: {required_manual_actions}",
            )

    def test_upgrade_plan_includes_new_template_assets_from_source_contract_when_target_contract_lags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)

            template_a = "scripts/templates/infra/bootstrap/infra/local/helm/core/cert-manager.values.yaml"
            template_b = "scripts/templates/infra/bootstrap/infra/gitops/platform/base/extensions/kustomization.yaml"
            _write(source_repo / "blueprint/contract.yaml", (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"))
            _write(source_repo / template_a, "crds:\n  enabled: true\n")
            _write(source_repo / template_b, "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\n")
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(source_repo / MANAGED_TEST_PATH, "baseline\nhead\n")
            _commit_all(source_repo, "head")

            lagging_contract = _generated_contract_text(
                drop_paths=(
                    template_a,
                    template_b,
                )
            )
            target_repo = _create_generated_repo(
                tmp_root,
                MANAGED_TEST_PATH,
                "baseline\n",
                contract_text=lagging_contract,
            )
            result = _run(
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
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            plan = _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json")
            first_entry = _plan_entry(plan, template_a)
            self.assertEqual(first_entry.get("action"), "create")
            self.assertEqual(first_entry.get("source_exists"), True)
            self.assertEqual(first_entry.get("target_exists"), False)
            second_entry = _plan_entry(plan, template_b)
            self.assertEqual(second_entry.get("action"), "create")
            self.assertEqual(second_entry.get("source_exists"), True)
            self.assertEqual(second_entry.get("target_exists"), False)

    def test_apply_runs_three_way_merge_for_diverged_blueprint_managed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = _create_source_repo(
                tmp_root,
                MANAGED_TEST_PATH,
                "header\nlocal-slot\nmiddle\nupstream-slot\nfooter\n",
                "header\nlocal-slot\nmiddle\nupstream-slot-updated\nfooter\n",
            )
            target_repo = _create_generated_repo(
                tmp_root,
                MANAGED_TEST_PATH,
                "header\nlocal-slot-updated\nmiddle\nupstream-slot\nfooter\n",
            )

            result = _run(
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
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            merged = (target_repo / MANAGED_TEST_PATH).read_text(encoding="utf-8")
            self.assertIn("local-slot-updated", merged)
            self.assertIn("upstream-slot-updated", merged)
            self.assertNotIn("<<<<<<<", merged)

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            path_result = _apply_result(apply_report, MANAGED_TEST_PATH)
            self.assertEqual(path_result.get("result"), "merged")
            self.assertEqual(apply_report.get("status"), "success")
            _assert_json_schema(
                _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json"),
                PLAN_SCHEMA,
            )
            _assert_json_schema(apply_report, APPLY_SCHEMA)

    def test_apply_create_preserves_executable_mode_from_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            _init_git_repo(source_repo)

            executable_path = "scripts/bin/blueprint/new_exec.sh"
            source_file = source_repo / executable_path
            _write(source_file, "#!/usr/bin/env bash\necho baseline\n")
            source_file.chmod(0o755)
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")

            _write(source_file, "#!/usr/bin/env bash\necho head\n")
            source_file.chmod(0o755)
            _commit_all(source_repo, "head")

            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "baseline\n")
            result = _run(
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
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            target_file = target_repo / executable_path
            self.assertTrue(target_file.is_file())
            self.assertEqual(target_file.stat().st_mode & 0o777, 0o755)

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            path_result = _apply_result(apply_report, executable_path)
            self.assertEqual(path_result.get("result"), "applied")

    def test_apply_conflict_creates_artifact_and_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = _create_source_repo(
                tmp_root,
                MANAGED_TEST_PATH,
                "shared\n",
                "upstream-change\n",
            )
            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "local-change\n")

            result = _run(
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
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("conflict", result.stderr)

            apply_report = _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json")
            self.assertEqual(apply_report.get("status"), "failure")
            path_result = _apply_result(apply_report, MANAGED_TEST_PATH)
            self.assertEqual(path_result.get("result"), "conflict")
            _assert_json_schema(
                _load_json(target_repo / "artifacts/blueprint/upgrade_plan.json"),
                PLAN_SCHEMA,
            )
            _assert_json_schema(apply_report, APPLY_SCHEMA)

            conflict_artifact_rel = str(path_result.get("conflict_artifact", ""))
            self.assertTrue(conflict_artifact_rel)
            conflict_artifact = target_repo / conflict_artifact_rel
            self.assertTrue(conflict_artifact.is_file())
            conflict_payload = _load_json(conflict_artifact)
            self.assertEqual(conflict_payload.get("path"), MANAGED_TEST_PATH)
            self.assertIn("baseline_content", conflict_payload)
            self.assertIn("merged_content", conflict_payload)

            # Target content must remain untouched on conflict.
            self.assertEqual((target_repo / MANAGED_TEST_PATH).read_text(encoding="utf-8"), "local-change\n")

    def test_three_way_merge_accepts_git_conflict_exit_codes_above_one(self) -> None:
        merge_result = subprocess.CompletedProcess(
            args=["git", "merge-file", "-p", "ours", "base", "theirs"],
            returncode=3,
            stdout="<<<<<<< ours\nlocal\n=======\nremote\n>>>>>>> theirs\n",
            stderr="",
        )

        with mock.patch.object(upgrade_consumer, "_run", return_value=merge_result):
            merged_content, has_conflicts = upgrade_consumer._three_way_merge("base\n", "ours\n", "theirs\n")

        self.assertTrue(has_conflicts)
        self.assertIn("<<<<<<<", merged_content)

    def test_three_way_merge_treats_positive_exit_without_markers_as_conflict(self) -> None:
        merge_result = subprocess.CompletedProcess(
            args=["git", "merge-file", "-p", "ours", "base", "theirs"],
            returncode=4,
            stdout="",
            stderr="",
        )

        with mock.patch.object(upgrade_consumer, "_run", return_value=merge_result):
            merged_content, has_conflicts = upgrade_consumer._three_way_merge("base\n", "ours\n", "theirs\n")

        self.assertEqual(merged_content, "")
        self.assertTrue(has_conflicts)

    def test_three_way_merge_raises_on_negative_exit(self) -> None:
        merge_result = subprocess.CompletedProcess(
            args=["git", "merge-file", "-p", "ours", "base", "theirs"],
            returncode=-1,
            stdout="",
            stderr="signal: killed",
        )

        with mock.patch.object(upgrade_consumer, "_run", return_value=merge_result):
            with self.assertRaisesRegex(RuntimeError, "git merge-file failed"):
                upgrade_consumer._three_way_merge("base\n", "ours\n", "theirs\n")

    def test_relative_report_paths_cannot_escape_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = _create_source_repo(tmp_root, MANAGED_TEST_PATH, "base\n", "head\n")
            target_repo = _create_generated_repo(tmp_root, MANAGED_TEST_PATH, "base\n")

            result = _run(
                [
                    sys.executable,
                    str(UPGRADE_SCRIPT),
                    "--repo-root",
                    str(target_repo),
                    "--source",
                    str(source_repo),
                    "--ref",
                    "HEAD",
                    "--plan-path",
                    "../escape.json",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("--plan-path must stay within the repository root", result.stderr)


class UpgradeConsumerValidateTests(unittest.TestCase):
    def _create_validation_repo(
        self,
        tmp_root: Path,
        *,
        include_marker: bool = False,
        repo_mode: str = "generated-consumer",
        missing_required_paths: tuple[str, ...] = (),
        include_source_only_required_path: str | None = None,
    ) -> Path:
        repo = tmp_root / "validate"
        _init_git_repo(repo)

        make_targets = [
            "quality-hooks-fast",
            "infra-validate",
            "quality-docs-check-core-targets-sync",
            "quality-docs-check-contract-metadata-sync",
            "quality-docs-check-runtime-identity-summary-sync",
            "quality-docs-check-module-contract-summaries-sync",
        ]
        lines = [".PHONY: " + " ".join(make_targets)]
        for target in make_targets:
            lines.append(f"{target}:")
            lines.append("\t@mkdir -p artifacts/blueprint")
            lines.append(f"\t@echo {target} >> artifacts/blueprint/validate_targets.log")

        contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
        keep_required_paths = {
            "Makefile",
            "blueprint/contract.yaml",
            "docs/reference/generated/core_targets.generated.md",
            "docs/reference/generated/contract_metadata.generated.md",
        }
        if include_source_only_required_path:
            keep_required_paths.add(include_source_only_required_path)
        drop_required_paths = tuple(
            path for path in contract.repository.required_files if path not in keep_required_paths
        )
        _write(
            repo / "blueprint/contract.yaml",
            _contract_text_for_repo_mode(repo_mode, drop_paths=drop_required_paths),
        )

        for required_path in sorted(keep_required_paths):
            if required_path == "blueprint/contract.yaml":
                continue
            if required_path in missing_required_paths:
                continue
            if required_path == "Makefile":
                _write(repo / "Makefile", "\n".join(lines) + "\n")
                continue
            _write(repo / required_path, f"{required_path}\n")

        if include_marker:
            _write(repo / "marker.txt", "<<<<<<< HEAD\n")

        _commit_all(repo, "validation baseline")
        return repo

    def test_validate_reports_success_and_runs_required_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo = self._create_validation_repo(tmp_root)

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            summary = report.get("summary", {})
            self.assertEqual(summary.get("status"), "success")
            self.assertEqual(summary.get("commands_total"), 6)
            self.assertEqual(summary.get("merge_markers_pre_count"), 0)
            self.assertEqual(summary.get("merge_markers_post_count"), 0)
            self.assertEqual(summary.get("runtime_dependency_missing_count"), 0)
            self.assertEqual(summary.get("required_files_missing_count"), 0)
            self.assertEqual(summary.get("generated_reference_missing_path_count"), 0)
            self.assertEqual(summary.get("contract_load_error_count"), 0)
            runtime_dependency_check = report.get("runtime_dependency_edge_check", {})
            self.assertIsInstance(runtime_dependency_check, dict)
            self.assertGreaterEqual(len(runtime_dependency_check.get("required_edges", [])), 1)
            self.assertEqual(runtime_dependency_check.get("missing", []), [])
            required_files_report = _load_json(repo / "artifacts/blueprint/upgrade/required_files_status.json")
            self.assertEqual(
                required_files_report.get("required_file_reconciliation", {}).get("missing_count"),
                0,
            )
            _assert_json_schema(report, VALIDATE_SCHEMA)

            command_results = report.get("command_results", [])
            self.assertEqual(len(command_results), 6)
            self.assertTrue(all(result.get("returncode") == 0 for result in command_results if isinstance(result, dict)))

    def test_validate_fails_when_merge_markers_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo = self._create_validation_repo(tmp_root, include_marker=True)

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("merge markers detected", result.stderr)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            summary = report.get("summary", {})
            self.assertEqual(summary.get("status"), "failure")
            self.assertGreater(summary.get("merge_markers_pre_count", 0), 0)
            self.assertEqual(summary.get("contract_load_error_count"), 0)
            _assert_json_schema(report, VALIDATE_SCHEMA)

    def test_validate_fails_when_runtime_dependency_edge_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo = self._create_validation_repo(tmp_root)
            _write(
                repo / "scripts/bin/infra/smoke.sh",
                "run_cmd \"$ROOT_DIR/scripts/bin/platform/auth/reconcile_runtime_identity.sh\"\n",
            )

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("runtime dependency edges missing required files", result.stderr)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            summary = report.get("summary", {})
            self.assertEqual(summary.get("status"), "failure")
            self.assertEqual(summary.get("runtime_dependency_missing_count"), 1)
            self.assertEqual(summary.get("contract_load_error_count"), 0)
            runtime_dependency_check = report.get("runtime_dependency_edge_check", {})
            self.assertEqual(len(runtime_dependency_check.get("missing", [])), 1)
            missing = runtime_dependency_check.get("missing", [])[0]
            self.assertEqual(missing.get("consumer_path"), "scripts/bin/infra/smoke.sh")
            self.assertEqual(
                missing.get("dependency_path"),
                "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
            )
            _assert_json_schema(report, VALIDATE_SCHEMA)

    def test_validate_fails_when_required_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            missing_path = "docs/reference/generated/core_targets.generated.md"
            repo = self._create_validation_repo(tmp_root, missing_required_paths=(missing_path,))

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing required files for active repo_mode", result.stderr)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            summary = report.get("summary", {})
            self.assertEqual(summary.get("status"), "failure")
            self.assertEqual(summary.get("required_files_missing_count"), 1)
            self.assertEqual(summary.get("contract_load_error_count"), 0)
            required_reconciliation = report.get("required_file_reconciliation", {})
            self.assertEqual(required_reconciliation.get("missing_paths"), [missing_path])
            entries = required_reconciliation.get("entries", [])
            self.assertIsInstance(entries, list)
            missing_entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("status") == "missing"]
            self.assertEqual(len(missing_entries), 1)
            self.assertEqual(missing_entries[0].get("path"), missing_path)
            remediation = missing_entries[0].get("remediation", {})
            self.assertEqual(remediation.get("action"), "render")
            _assert_json_schema(report, VALIDATE_SCHEMA)

    def test_validate_generated_consumer_repo_mode_excludes_source_only_required_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_only_required_path = "tests/blueprint/contract_refactor_governance_structure_cases.py"
            repo = self._create_validation_repo(
                tmp_root,
                repo_mode="generated-consumer",
                include_source_only_required_path=source_only_required_path,
                missing_required_paths=(source_only_required_path,),
            )

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            required_reconciliation = report.get("required_file_reconciliation", {})
            self.assertEqual(required_reconciliation.get("missing_count"), 0)
            self.assertEqual(report.get("summary", {}).get("contract_load_error_count"), 0)
            excluded = required_reconciliation.get("excluded_by_repo_mode", [])
            self.assertIn(source_only_required_path, excluded)
            _assert_json_schema(report, VALIDATE_SCHEMA)

    def test_validate_template_source_repo_mode_requires_source_only_required_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_only_required_path = "tests/blueprint/contract_refactor_governance_structure_cases.py"
            repo = self._create_validation_repo(
                tmp_root,
                repo_mode="template-source",
                include_source_only_required_path=source_only_required_path,
                missing_required_paths=(source_only_required_path,),
            )

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            required_reconciliation = report.get("required_file_reconciliation", {})
            self.assertEqual(required_reconciliation.get("missing_count"), 1)
            self.assertEqual(report.get("summary", {}).get("contract_load_error_count"), 0)
            self.assertEqual(required_reconciliation.get("missing_paths"), [source_only_required_path])
            _assert_json_schema(report, VALIDATE_SCHEMA)

    def test_validate_writes_failure_artifacts_when_contract_cannot_be_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo = self._create_validation_repo(tmp_root)
            _write(repo / "blueprint/contract.yaml", "<<<<<<< HEAD\n")

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("unable to load blueprint contract for required-files reconciliation", result.stderr)

            report = _load_json(repo / "artifacts/blueprint/upgrade_validate.json")
            summary = report.get("summary", {})
            self.assertEqual(summary.get("status"), "failure")
            self.assertEqual(summary.get("commands_total"), 0)
            self.assertEqual(summary.get("contract_load_error_count"), 1)
            self.assertGreaterEqual(summary.get("generated_reference_missing_target_count"), 1)
            self.assertGreater(summary.get("merge_markers_pre_count", 0), 0)
            self.assertIsInstance(report.get("contract_load_error"), str)

            required_files_status = _load_json(repo / "artifacts/blueprint/upgrade/required_files_status.json")
            self.assertIsInstance(required_files_status.get("contract_load_error"), str)
            self.assertEqual(
                required_files_status.get("required_file_reconciliation", {}).get("repo_mode"),
                "unknown",
            )
            _assert_json_schema(report, VALIDATE_SCHEMA)


if __name__ == "__main__":
    unittest.main()
