from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


UPGRADE_WRAPPER_REL = Path("scripts/bin/blueprint/upgrade_consumer.sh")
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
plan_path.parent.mkdir(parents=True, exist_ok=True)
apply_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)
plan_path.write_text(json.dumps({"entries": [], "required_manual_actions": [], "summary": {"total": 0, "required_manual_action_count": 0}}) + "\\n", encoding="utf-8")
apply_path.write_text(json.dumps({"results": [], "required_manual_actions": [], "summary": {"total": 0, "required_manual_action_count": 0}, "status": "success"}) + "\\n", encoding="utf-8")
summary_path.write_text("source-engine\\n", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
