from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
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
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


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


def _generated_contract_text() -> str:
    return (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
        "repo_mode: template-source",
        "repo_mode: generated-consumer",
        1,
    )


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


def _create_generated_repo(root: Path, relative_path: str, content: str) -> Path:
    target_repo = root / "target"
    _init_git_repo(target_repo)
    _write(target_repo / "blueprint/contract.yaml", _generated_contract_text())
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
            _assert_json_schema(first_plan, PLAN_SCHEMA)
            _assert_json_schema(
                _load_json(target_repo / "artifacts/blueprint/upgrade_apply.json"),
                APPLY_SCHEMA,
            )

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
                "run_cmd \"$ROOT_DIR/scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh\"\n",
            )
            _write(
                source_repo / "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
                "#!/usr/bin/env bash\necho ok\n",
            )
            _commit_all(source_repo, "baseline")
            _require_success(_git(source_repo, "tag", f"v{_template_version()}"), "git tag template version")
            _write(
                source_repo / "scripts/bin/infra/smoke.sh",
                "echo warmup\nrun_cmd \"$ROOT_DIR/scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh\"\n",
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
                "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
            )
            self.assertEqual(dependency_entry.get("action"), "skip")
            self.assertIn("required-manual-action", str(dependency_entry.get("reason", "")))
            self.assertIn("scripts/bin/infra/smoke.sh", str(dependency_entry.get("reason", "")))

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
    def _create_validation_repo(self, tmp_root: Path, *, include_marker: bool = False) -> Path:
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
        _write(repo / "Makefile", "\n".join(lines) + "\n")
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
            runtime_dependency_check = report.get("runtime_dependency_edge_check", {})
            self.assertIsInstance(runtime_dependency_check, dict)
            self.assertGreaterEqual(len(runtime_dependency_check.get("required_edges", [])), 1)
            self.assertEqual(runtime_dependency_check.get("missing", []), [])
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
            _assert_json_schema(report, VALIDATE_SCHEMA)

    def test_validate_fails_when_runtime_dependency_edge_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo = self._create_validation_repo(tmp_root)
            _write(
                repo / "scripts/bin/infra/smoke.sh",
                "run_cmd \"$ROOT_DIR/scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh\"\n",
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
            runtime_dependency_check = report.get("runtime_dependency_edge_check", {})
            self.assertEqual(len(runtime_dependency_check.get("missing", [])), 1)
            missing = runtime_dependency_check.get("missing", [])[0]
            self.assertEqual(missing.get("consumer_path"), "scripts/bin/infra/smoke.sh")
            self.assertEqual(
                missing.get("dependency_path"),
                "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
            )
            _assert_json_schema(report, VALIDATE_SCHEMA)


if __name__ == "__main__":
    unittest.main()
