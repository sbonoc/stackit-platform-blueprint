from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.exec import DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS, run_command


REPO_ROOT = Path(__file__).resolve().parents[2]
UPGRADE_PREFLIGHT_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/upgrade_preflight.py"
UPGRADE_PREFLIGHT_WRAPPER = REPO_ROOT / "scripts/bin/blueprint/upgrade_consumer_preflight.sh"


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
            contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
            keep_required_paths = {
                "README.md",
                "docs/reference/generated/contract_metadata.generated.md",
            }
            drop_required_paths = tuple(
                path for path in contract.repository.required_files if path not in keep_required_paths
            )
            (repo_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo_root / "blueprint/contract.yaml").write_text(
                _contract_text_for_repo_mode("generated-consumer", drop_paths=drop_required_paths),
                encoding="utf-8",
            )

            plan_payload = {
                "entries": [
                    {"path": "README.md", "action": "create"},
                    {"path": "scripts/bin/blueprint/upgrade_consumer.sh", "action": "update"},
                    {"path": "docs/platform/consumer/quickstart.md", "action": "merge-required"},
                    {"path": "docs/reference/generated/contract_metadata.generated.md", "action": "conflict"},
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
            self.assertEqual(summary["required_surface_delta_count"], 2)
            self.assertEqual(summary["required_surface_auto_apply_count"], 1)
            self.assertEqual(summary["required_surface_at_risk_count"], 1)
            self.assertEqual(summary["merge_risk_blocking_bucket_count"], 3)
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
                    "blueprint/runtime_identity_contract.yaml",
                    "docs/platform/consumer/quickstart.md",
                    "docs/platform/consumer/runtime_credentials_eso.md",
                    "docs/reference/generated/contract_metadata.generated.md",
                ],
            )
            merge_risk = report["merge_risk_classification"]
            self.assertEqual(merge_risk["status"], "blocked")
            self.assertEqual(
                merge_risk["blocking_buckets"],
                [
                    "consumer_owned_manual_review",
                    "generated_references_regenerate",
                    "conflicts_unresolved",
                ],
            )
            self.assertEqual(merge_risk["blocking_bucket_count"], 3)
            buckets = {row["bucket"]: row for row in merge_risk["buckets"]}
            self.assertEqual(buckets["blueprint_managed_safe_to_take"]["count"], 2)
            self.assertEqual(buckets["consumer_owned_manual_review"]["count"], 2)
            self.assertEqual(buckets["generated_references_regenerate"]["count"], 1)
            self.assertEqual(buckets["conflicts_unresolved"]["count"], 2)
            required_surfaces = report["required_surface_reconciliation"]
            self.assertTrue(required_surfaces["contract_available"])
            self.assertEqual(required_surfaces["repo_mode"], "generated-consumer")
            self.assertEqual(required_surfaces["required_files_expected_count"], 2)
            self.assertEqual(len(required_surfaces["required_surface_deltas"]), 2)
            self.assertEqual(required_surfaces["required_surfaces_auto_apply"], ["README.md"])
            self.assertEqual(
                required_surfaces["required_surfaces_at_risk"],
                [
                    {
                        "action": "conflict",
                        "path": "docs/reference/generated/contract_metadata.generated.md",
                        "risk_reasons": ["plan-action:conflict"],
                    }
                ],
            )

    def test_preflight_excludes_benign_skip_and_keeps_missing_target_skip_as_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            artifacts_dir = repo_root / "artifacts/blueprint"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
            keep_required_paths = {"README.md"}
            drop_required_paths = tuple(path for path in contract.repository.required_files if path not in keep_required_paths)
            (repo_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo_root / "blueprint/contract.yaml").write_text(
                _contract_text_for_repo_mode("generated-consumer", drop_paths=drop_required_paths),
                encoding="utf-8",
            )

            plan_payload = {
                "entries": [
                    {
                        "path": "README.md",
                        "action": "skip",
                        "reason": "path already matches upgrade source content",
                        "source_exists": True,
                        "target_exists": True,
                    },
                    {
                        "path": "README.md",
                        "action": "skip",
                        "reason": "path is consumer-owned and excluded from blueprint upgrade apply",
                        "source_exists": True,
                        "target_exists": False,
                    },
                ],
                "required_manual_actions": [],
            }
            apply_payload = {"results": []}
            (artifacts_dir / "upgrade_plan.json").write_text(json.dumps(plan_payload), encoding="utf-8")
            (artifacts_dir / "upgrade_apply.json").write_text(json.dumps(apply_payload), encoding="utf-8")

            report_path = artifacts_dir / "upgrade_preflight.json"
            result = self._run_preflight(repo_root)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            summary = report["summary"]
            self.assertEqual(summary["required_surface_delta_count"], 2)
            self.assertEqual(summary["required_surface_at_risk_count"], 1)
            self.assertEqual(summary["merge_risk_blocking_bucket_count"], 1)
            self.assertEqual(report["merge_risk_classification"]["status"], "blocked")
            required_surfaces = report["required_surface_reconciliation"]
            self.assertEqual(
                required_surfaces["required_surfaces_at_risk"],
                [
                    {
                        "action": "skip",
                        "path": "README.md",
                        "risk_reasons": ["plan-action:skip-missing-target"],
                    }
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

    def test_preflight_wrapper_handles_empty_forward_args_without_nounset_failure(self) -> None:
        result = run_command(
            [str(UPGRADE_PREFLIGHT_WRAPPER)],
            cwd=REPO_ROOT,
            env={
                "BLUEPRINT_UPGRADE_SOURCE": str(REPO_ROOT),
                "BLUEPRINT_UPGRADE_REF": "HEAD",
            },
            timeout_seconds=DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS,
        )

        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("running blueprint consumer upgrade", combined_output)
        self.assertIn("generated-consumer repositories", combined_output)
        self.assertNotIn("forward_args[@]: unbound variable", combined_output)
