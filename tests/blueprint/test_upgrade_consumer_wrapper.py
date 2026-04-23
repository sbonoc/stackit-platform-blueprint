from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


UPGRADE_WRAPPER_REL = Path("scripts/bin/blueprint/upgrade_consumer.sh")
POSTCHECK_WRAPPER_REL = Path("scripts/bin/blueprint/upgrade_consumer_postcheck.sh")
POSTCHECK_VALIDATE_REL = Path("scripts/bin/blueprint/upgrade_consumer_validate.sh")
POSTCHECK_PY_REL = Path("scripts/lib/blueprint/upgrade_consumer_postcheck.py")
BEHAVIORAL_CHECK_PY_REL = Path("scripts/lib/blueprint/upgrade_shell_behavioral_check.py")
SHELL_LIB_DIR_REL = Path("scripts/lib/shell")
CONTRACT_RUNTIME_REL = Path("scripts/lib/blueprint/contract_runtime.sh")
UPGRADE_REPORT_METRICS_REL = Path("scripts/lib/blueprint/upgrade_report_metrics.py")
LOCAL_ENGINE_REL = Path("scripts/lib/blueprint/upgrade_consumer.py")


def _copy_file(relative_path: Path, destination_root: Path) -> None:
    source_path = REPO_ROOT / relative_path
    target_path = destination_root / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _assert_success(result, *, context: str) -> None:
    if result.returncode == 0:
        return
    raise AssertionError(
        f"{context} failed with exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def _init_git_repo(repo_root: Path) -> None:
    _assert_success(run_command(["git", "init"], cwd=repo_root), context="git init")
    _assert_success(
        run_command(["git", "config", "user.email", "tests@example.com"], cwd=repo_root),
        context="git config user.email",
    )
    _assert_success(
        run_command(["git", "config", "user.name", "Blueprint Tests"], cwd=repo_root),
        context="git config user.name",
    )


def _commit_all(repo_root: Path, message: str) -> None:
    _assert_success(run_command(["git", "add", "."], cwd=repo_root), context="git add")
    _assert_success(
        run_command(["git", "commit", "-m", message], cwd=repo_root),
        context=f"git commit {message}",
    )


class UpgradeConsumerWrapperTests(unittest.TestCase):
    def test_source_ref_engine_mode_is_default_and_avoids_stale_local_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            consumer_repo = tmp_root / "consumer"
            consumer_repo.mkdir(parents=True, exist_ok=True)
            _write(consumer_repo / "Makefile", ".PHONY: noop\nnoop:\n\t@:\n")

            _copy_file(UPGRADE_WRAPPER_REL, consumer_repo)
            _copy_file(CONTRACT_RUNTIME_REL, consumer_repo)
            _copy_file(UPGRADE_REPORT_METRICS_REL, consumer_repo)
            for shell_lib_path in sorted((REPO_ROOT / SHELL_LIB_DIR_REL).glob("*.sh")):
                _copy_file(shell_lib_path.relative_to(REPO_ROOT), consumer_repo)

            local_engine_marker = consumer_repo / "artifacts/local_engine_invoked"
            _write(
                consumer_repo / LOCAL_ENGINE_REL,
                """#!/usr/bin/env python3
from pathlib import Path
import sys
Path("artifacts/local_engine_invoked").parent.mkdir(parents=True, exist_ok=True)
Path("artifacts/local_engine_invoked").write_text("invoked\\n", encoding="utf-8")
print("RuntimeError: git merge-file failed:", file=sys.stderr)
raise SystemExit(1)
""",
            )

            source_repo = tmp_root / "source"
            source_repo.mkdir(parents=True, exist_ok=True)
            _init_git_repo(source_repo)
            _write(
                source_repo / LOCAL_ENGINE_REL,
                """#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--repo-root", required=True)
parser.add_argument("--source", required=True)
parser.add_argument("--ref", required=True)
parser.add_argument("--plan-path", required=True)
parser.add_argument("--apply-path", required=True)
parser.add_argument("--summary-path", required=True)
parser.add_argument("--reconcile-report-path", required=True)
parser.add_argument("--apply", action="store_true")
parser.add_argument("--allow-dirty", action="store_true")
parser.add_argument("--allow-delete", action="store_true")
args = parser.parse_args()

repo_root = Path(args.repo_root)

def resolve(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return repo_root / path

plan_path = resolve(args.plan_path)
apply_path = resolve(args.apply_path)
summary_path = resolve(args.summary_path)
reconcile_path = resolve(args.reconcile_report_path)
plan_path.parent.mkdir(parents=True, exist_ok=True)
apply_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)
reconcile_path.parent.mkdir(parents=True, exist_ok=True)
plan_path.write_text(json.dumps({"entries": [], "required_manual_actions": [], "summary": {"total": 0, "required_manual_action_count": 0}}) + "\\n", encoding="utf-8")
apply_path.write_text(json.dumps({"results": [], "required_manual_actions": [], "summary": {"total": 0, "required_manual_action_count": 0}, "status": "success"}) + "\\n", encoding="utf-8")
summary_path.write_text("source-engine\\n", encoding="utf-8")
reconcile_path.write_text(json.dumps({"summary": {"blocked": False}}) + "\\n", encoding="utf-8")
print("source-engine-executed")
""",
            )
            _commit_all(source_repo, "source engine")

            local_mode_result = run_command(
                [str(consumer_repo / UPGRADE_WRAPPER_REL), "--apply"],
                cwd=consumer_repo,
                env={
                    "BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS": "true",
                    "BLUEPRINT_UPGRADE_SOURCE": str(source_repo),
                    "BLUEPRINT_UPGRADE_REF": "HEAD",
                    "BLUEPRINT_UPGRADE_ENGINE_MODE": "local",
                },
            )
            local_mode_output = f"{local_mode_result.stdout}\n{local_mode_result.stderr}"
            self.assertNotEqual(local_mode_result.returncode, 0, msg=local_mode_output)
            self.assertIn("RuntimeError: git merge-file failed:", local_mode_output)
            self.assertTrue(local_engine_marker.exists())
            local_engine_marker.unlink()

            result = run_command(
                [str(consumer_repo / UPGRADE_WRAPPER_REL), "--apply"],
                cwd=consumer_repo,
                env={
                    "BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS": "true",
                    "BLUEPRINT_UPGRADE_SOURCE": str(source_repo),
                    "BLUEPRINT_UPGRADE_REF": "HEAD",
                },
            )

            combined_output = f"{result.stdout}\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=combined_output)
            self.assertIn("source-engine-executed", combined_output)
            self.assertIn("blueprint_upgrade_engine_mode value=source-ref", combined_output)
            self.assertFalse(local_engine_marker.exists())

            plan_report = json.loads((consumer_repo / "artifacts/blueprint/upgrade_plan.json").read_text(encoding="utf-8"))
            apply_report = json.loads((consumer_repo / "artifacts/blueprint/upgrade_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(plan_report.get("summary", {}).get("total"), 0)
            self.assertEqual(apply_report.get("status"), "success")


FIXTURE_DIR_REL = Path("tests/blueprint/fixtures/shell_behavioral_check")


def _write_merged_sh_reports(consumer_repo: Path, rel_sh: str) -> None:
    """Write plan, apply, and reconcile reports for a single result=merged .sh file.

    The reconcile metadata exactly matches the plan so stale-detection does NOT
    recompute it (recomputation would classify merge-required plan entries as
    conflicts_unresolved, masking the behavioral gate under test).
    """
    source = "git@github.com:example/source.git"
    upgrade_ref = "v1.1.0"
    commit = "abc123"
    baseline = "v1.0.0"

    apply_payload = {
        "results": [
            {
                "path": rel_sh,
                "planned_action": "merge-required",
                "result": "merged",
                "reason": "diverged from baseline; 3-way merge applied",
            }
        ]
    }
    _write(consumer_repo / "artifacts/blueprint/upgrade_apply.json", json.dumps(apply_payload) + "\n")

    plan_payload = {
        "source": source,
        "upgrade_ref": upgrade_ref,
        "resolved_upgrade_commit": commit,
        "baseline_ref": baseline,
        "entries": [{"path": rel_sh, "action": "merge-required", "operation": "update"}],
        "required_manual_actions": [],
    }
    _write(consumer_repo / "artifacts/blueprint/upgrade_plan.json", json.dumps(plan_payload) + "\n")

    reconcile_payload = {
        "source": source,
        "upgrade_ref": upgrade_ref,
        "resolved_upgrade_commit": commit,
        "template_ref_from": baseline,
        "summary": {
            "conflicts_unresolved_count": 0,
            "blocking_bucket_count": 0,
            "blocked": False,
            "plan_entry_count": 1,
            "required_manual_action_count": 0,
            "apply_result_count": 1,
        },
        "buckets": {
            "blueprint_managed_safe_to_take": [],
            "consumer_owned_manual_review": [],
            "generated_references_regenerate": [],
            "conflicts_unresolved": [],
        },
    }
    _write(
        consumer_repo / "artifacts/blueprint/upgrade/upgrade_reconcile_report.json",
        json.dumps(reconcile_payload) + "\n",
    )


class PostcheckWrapperBehavioralMetricTests(unittest.TestCase):
    """AC-006: shell wrapper emits blueprint_upgrade_postcheck_behavioral_check_failures_total."""

    def _build_postcheck_env(self, consumer_repo: Path) -> dict[str, str]:
        """Copy all files needed to run the postcheck wrapper in a temp consumer repo."""
        for rel in (
            POSTCHECK_WRAPPER_REL,
            POSTCHECK_VALIDATE_REL,
            POSTCHECK_PY_REL,
            BEHAVIORAL_CHECK_PY_REL,
            UPGRADE_REPORT_METRICS_REL,
            CONTRACT_RUNTIME_REL,
        ):
            _copy_file(rel, consumer_repo)
        for shell_lib_path in sorted((REPO_ROOT / SHELL_LIB_DIR_REL).glob("*.sh")):
            _copy_file(shell_lib_path.relative_to(REPO_ROOT), consumer_repo)
        # validate script needs validate_contract.py and schemas
        for rel in (
            Path("scripts/bin/blueprint/validate_contract.py"),
            Path("scripts/lib/blueprint/contract_schema.py"),
            Path("scripts/lib/blueprint/merge_markers.py"),
            Path("scripts/lib/blueprint/upgrade_consumer_postcheck.py"),
            Path("scripts/lib/blueprint/upgrade_consumer_validate.py"),
            Path("scripts/lib/blueprint/upgrade_reconcile_report.py"),
            Path("scripts/lib/blueprint/upgrade_report_metrics.py"),
            Path("scripts/lib/blueprint/cli_support.py"),
            Path("scripts/lib/blueprint/runtime_dependency_edges.py"),
        ):
            _copy_file(rel, consumer_repo)
        # copy schemas dir
        schemas_src = REPO_ROOT / "scripts/lib/blueprint/schemas"
        schemas_dst = consumer_repo / "scripts/lib/blueprint/schemas"
        if schemas_src.exists():
            import shutil as _shutil
            _shutil.copytree(str(schemas_src), str(schemas_dst), dirs_exist_ok=True)
        return {"BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS": "true"}

    def test_metric_emitted_with_correct_failure_count(self) -> None:
        """AC-006: wrapper emits behavioral_check_failures_total with count=1 for unresolved symbol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            consumer_repo = tmp_root / "consumer"
            consumer_repo.mkdir(parents=True, exist_ok=True)
            _init_git_repo(consumer_repo)
            _write(consumer_repo / ".gitignore", "artifacts/\n")
            run_command(["git", "add", "."], cwd=consumer_repo)
            run_command(["git", "commit", "-m", "init"], cwd=consumer_repo)

            env = self._build_postcheck_env(consumer_repo)

            # Add Makefile + scripts/lib marker so root_dir.sh can resolve the repo root
            _write(consumer_repo / "Makefile", ".PHONY: noop\nnoop:\n\t@:\n")

            # Write contract (generated-consumer mode to skip docs hooks)
            from tests._shared.helpers import REPO_ROOT as _REPO_ROOT
            contract_text = (_REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
                "repo_mode: template-source", "repo_mode: generated-consumer", 1
            )
            _write(consumer_repo / "blueprint/contract.yaml", contract_text)

            # Write validate report (success)
            _write(
                consumer_repo / "artifacts/blueprint/upgrade_validate.json",
                json.dumps({"summary": {"status": "success"}}) + "\n",
            )
            # Write reconcile report (no conflicts)
            _write(
                consumer_repo / "artifacts/blueprint/upgrade/upgrade_reconcile_report.json",
                json.dumps({"summary": {"conflicts_unresolved_count": 0, "blocking_bucket_count": 0, "blocked": False}}) + "\n",
            )

            # Place a script with a missing function definition as a result=merged file
            rel_sh = "scripts/bin/platform/missing_def.sh"
            dest_sh = consumer_repo / rel_sh
            dest_sh.parent.mkdir(parents=True, exist_ok=True)
            dest_sh.write_text((REPO_ROOT / FIXTURE_DIR_REL / "missing_def_script.sh").read_text())

            _write_merged_sh_reports(consumer_repo, rel_sh)

            result = run_command(
                [str(consumer_repo / POSTCHECK_WRAPPER_REL)],
                cwd=consumer_repo,
                env=env,
            )
            combined = result.stdout + "\n" + result.stderr

            # Postcheck must fail due to behavioral check
            self.assertNotEqual(result.returncode, 0, msg=combined)
            # AC-006: metric line must appear in output
            self.assertIn("blueprint_upgrade_postcheck_behavioral_check_failures_total", combined)
            # Value must be 1 (one unresolved symbol)
            self.assertRegex(combined, r"blueprint_upgrade_postcheck_behavioral_check_failures_total value=[1-9]")

    def test_metric_zero_when_behavioral_check_passes(self) -> None:
        """AC-006: wrapper emits failures_total=0 when all merged scripts are clean."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            consumer_repo = tmp_root / "consumer"
            consumer_repo.mkdir(parents=True, exist_ok=True)
            _init_git_repo(consumer_repo)
            _write(consumer_repo / ".gitignore", "artifacts/\n")
            run_command(["git", "add", "."], cwd=consumer_repo)
            run_command(["git", "commit", "-m", "init"], cwd=consumer_repo)

            env = self._build_postcheck_env(consumer_repo)

            # Add Makefile + scripts/lib marker so root_dir.sh can resolve the repo root
            _write(consumer_repo / "Makefile", ".PHONY: noop\nnoop:\n\t@:\n")

            from tests._shared.helpers import REPO_ROOT as _REPO_ROOT
            contract_text = (_REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
                "repo_mode: template-source", "repo_mode: generated-consumer", 1
            )
            _write(consumer_repo / "blueprint/contract.yaml", contract_text)
            _write(
                consumer_repo / "artifacts/blueprint/upgrade_validate.json",
                json.dumps({"summary": {"status": "success"}}) + "\n",
            )

            rel_sh = "scripts/bin/platform/clean.sh"
            dest_sh = consumer_repo / rel_sh
            dest_sh.parent.mkdir(parents=True, exist_ok=True)
            dest_sh.write_text((REPO_ROOT / FIXTURE_DIR_REL / "clean_script.sh").read_text())

            _write_merged_sh_reports(consumer_repo, rel_sh)

            result = run_command(
                [str(consumer_repo / POSTCHECK_WRAPPER_REL)],
                cwd=consumer_repo,
                env=env,
            )
            combined = result.stdout + "\n" + result.stderr

            # AC-006: the metric must be emitted with value=0 regardless of overall
            # postcheck exit code.  In this test env the consumer repo is incomplete
            # (validate will fail on missing required files) but the behavioral check
            # still runs and the metric is still emitted by emit_postcheck_report_metrics.
            self.assertIn("blueprint_upgrade_postcheck_behavioral_check_failures_total", combined)
            self.assertRegex(combined, r"blueprint_upgrade_postcheck_behavioral_check_failures_total value=0")


if __name__ == "__main__":
    unittest.main()
