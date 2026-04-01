from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from tests._shared.exec import DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS, run_command


REPO_ROOT = Path(__file__).resolve().parents[2]
UPGRADE_PREFLIGHT_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/upgrade_preflight.py"


class UpgradePreflightTests(unittest.TestCase):
    def _run_preflight(self, repo_root: Path, *args: str):
        return run_command(
            [
                sys.executable,
                str(UPGRADE_PREFLIGHT_SCRIPT),
                "--repo-root",
                str(repo_root),
                *args,
            ],
            cwd=REPO_ROOT,
            timeout_seconds=DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS,
        )

    def test_preflight_report_groups_actions_manual_steps_and_follow_up_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            artifacts_dir = repo_root / "artifacts/blueprint"
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            plan_payload = {
                "entries": [
                    {"path": "README.md", "action": "create"},
                    {"path": "scripts/bin/blueprint/upgrade_consumer.sh", "action": "update"},
                    {"path": "docs/platform/consumer/quickstart.md", "action": "merge-required"},
                    {"path": "blueprint/contract.yaml", "action": "conflict"},
                    {"path": "docs/legacy.md", "action": "skip"},
                ],
                "required_manual_actions": [
                    {
                        "dependency_path": "blueprint/runtime_identity_contract.yaml",
                        "required_follow_up_commands": [
                            "make blueprint-upgrade-consumer-validate",
                            "make infra-validate",
                        ],
                    },
                    {
                        "dependency_path": "docs/platform/consumer/runtime_credentials_eso.md",
                        "required_follow_up_commands": [
                            "make infra-validate",
                            "make quality-hooks-run",
                        ],
                    },
                ],
            }
            apply_payload = {
                "results": [
                    {"path": "README.md", "result": "created"},
                    {"path": "scripts/bin/blueprint/upgrade_consumer.sh", "result": "updated"},
                ]
            }
            (artifacts_dir / "upgrade_plan.json").write_text(json.dumps(plan_payload), encoding="utf-8")
            (artifacts_dir / "upgrade_apply.json").write_text(json.dumps(apply_payload), encoding="utf-8")

            report_path = artifacts_dir / "upgrade_preflight.json"
            result = self._run_preflight(
                repo_root,
                "--plan-path",
                "artifacts/blueprint/upgrade_plan.json",
                "--apply-path",
                "artifacts/blueprint/upgrade_apply.json",
                "--output-path",
                "artifacts/blueprint/upgrade_preflight.json",
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("upgrade preflight report:", result.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            summary = report["summary"]
            self.assertEqual(summary["plan_entry_count"], 5)
            self.assertEqual(summary["apply_result_count"], 2)
            self.assertEqual(summary["auto_apply_count"], 2)
            self.assertEqual(summary["manual_merge_count"], 1)
            self.assertEqual(summary["conflict_count"], 1)
            self.assertEqual(summary["skip_count"], 1)
            self.assertEqual(summary["required_manual_action_count"], 2)
            self.assertEqual(summary["required_follow_up_command_count"], 3)
            self.assertEqual(summary["blocking_path_count"], 4)
            self.assertEqual(
                report["required_follow_up_commands"],
                [
                    "make blueprint-upgrade-consumer-validate",
                    "make infra-validate",
                    "make quality-hooks-run",
                ],
            )
            self.assertEqual(
                report["blocking_paths"],
                [
                    "blueprint/contract.yaml",
                    "blueprint/runtime_identity_contract.yaml",
                    "docs/platform/consumer/quickstart.md",
                    "docs/platform/consumer/runtime_credentials_eso.md",
                ],
            )

    def test_preflight_fails_when_apply_report_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            artifacts_dir = repo_root / "artifacts/blueprint"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "upgrade_plan.json").write_text(json.dumps({"entries": []}), encoding="utf-8")

            result = self._run_preflight(repo_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing upgrade apply report", result.stderr)

    def test_preflight_rejects_relative_paths_outside_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            artifacts_dir = repo_root / "artifacts/blueprint"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "upgrade_plan.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
            (artifacts_dir / "upgrade_apply.json").write_text(json.dumps({"results": []}), encoding="utf-8")

            result = self._run_preflight(repo_root, "--plan-path", "../upgrade_plan.json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--plan-path must stay within the repository root", result.stderr)
