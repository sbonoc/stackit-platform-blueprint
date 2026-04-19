from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT
from tests._shared.json_schema import assert_json_matches_schema, load_json_schema


POSTCHECK_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/upgrade_consumer_postcheck.py"
POSTCHECK_SCHEMA = REPO_ROOT / "scripts/lib/blueprint/schemas/upgrade_postcheck.schema.json"


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
    _write(repo / ".gitignore", "artifacts/\n")
    _require_success(_git(repo, "add", "."), "git add .")
    _require_success(_git(repo, "commit", "-m", "init"), "git commit -m init")


def _contract_text_for_repo_mode(repo_mode: str) -> str:
    return (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
        "repo_mode: template-source",
        f"repo_mode: {repo_mode}",
        1,
    )


def _write_validate_report(repo: Path, *, status: str) -> None:
    payload = {
        "summary": {
            "status": status,
        }
    }
    _write(repo / "artifacts/blueprint/upgrade_validate.json", json.dumps(payload) + "\n")


def _write_reconcile_report(repo: Path, *, conflicts_unresolved_count: int, blocked: bool) -> None:
    payload = {
        "summary": {
            "conflicts_unresolved_count": conflicts_unresolved_count,
            "blocking_bucket_count": 1 if blocked else 0,
            "blocked": blocked,
        }
    }
    _write(repo / "artifacts/blueprint/upgrade/upgrade_reconcile_report.json", json.dumps(payload) + "\n")


def _write_plan_apply_reports(
    repo: Path,
    *,
    plan_payload: dict[str, object],
    apply_payload: dict[str, object],
) -> None:
    _write(repo / "artifacts/blueprint/upgrade_plan.json", json.dumps(plan_payload) + "\n")
    _write(repo / "artifacts/blueprint/upgrade_apply.json", json.dumps(apply_payload) + "\n")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_json_schema(payload: dict[str, object], schema_path: Path) -> None:
    schema = load_json_schema(schema_path)
    assert_json_matches_schema(payload, schema)


class UpgradePostcheckTests(unittest.TestCase):
    def test_postcheck_succeeds_for_generated_consumer_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            _init_git_repo(repo)
            _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode("generated-consumer"))
            _write_validate_report(repo, status="success")
            _write_reconcile_report(repo, conflicts_unresolved_count=0, blocked=False)

            result = _run(
                [
                    sys.executable,
                    str(POSTCHECK_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertEqual(report.get("summary", {}).get("status"), "success")
            self.assertEqual(report.get("summary", {}).get("blocked_reason_count"), 0)
            self.assertEqual(report.get("docs_hook_checks", {}).get("targets"), [])
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_postcheck_fails_when_reconcile_conflicts_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            _init_git_repo(repo)
            _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode("generated-consumer"))
            _write_validate_report(repo, status="success")
            _write_reconcile_report(repo, conflicts_unresolved_count=2, blocked=True)

            result = _run(
                [
                    sys.executable,
                    str(POSTCHECK_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            reasons = report.get("summary", {}).get("blocked_reasons", [])
            self.assertIn("reconcile-conflicts-unresolved", reasons)
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_postcheck_fails_when_merge_markers_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            _init_git_repo(repo)
            _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode("generated-consumer"))
            _write_validate_report(repo, status="success")
            _write_reconcile_report(repo, conflicts_unresolved_count=0, blocked=False)
            _write(repo / "zeta.txt", "<<<<<<< HEAD\nlocal\n=======\nupstream\n>>>>>>> branch\n")
            _write(repo / "alpha.txt", "<<<<<<< HEAD\nlocal\n=======\nupstream\n>>>>>>> branch\n")

            result = _run(
                [
                    sys.executable,
                    str(POSTCHECK_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            reasons = report.get("summary", {}).get("blocked_reasons", [])
            self.assertIn("merge-markers-present", reasons)
            self.assertGreater(report.get("summary", {}).get("merge_marker_count", 0), 0)
            marker_paths = report.get("merge_marker_check", {}).get("paths", [])
            self.assertEqual(marker_paths, sorted(marker_paths))
            self.assertEqual(marker_paths[0], "alpha.txt:1:<<<<<<< HEAD")
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_postcheck_recomputes_stale_reconcile_report_when_plan_apply_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            _init_git_repo(repo)
            _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode("generated-consumer"))
            _write_validate_report(repo, status="success")
            _write(
                repo / "artifacts/blueprint/upgrade/upgrade_reconcile_report.json",
                json.dumps(
                    {
                        "source": "git@github.com:example/old-source.git",
                        "upgrade_ref": "v0.9.0",
                        "resolved_upgrade_commit": "old-commit",
                        "template_ref_from": "v0.8.0",
                        "summary": {
                            "conflicts_unresolved_count": 0,
                            "blocking_bucket_count": 0,
                            "blocked": False,
                            "plan_entry_count": 0,
                            "apply_result_count": 0,
                            "required_manual_action_count": 0,
                        },
                    }
                )
                + "\n",
            )
            _write_plan_apply_reports(
                repo,
                plan_payload={
                    "source": "git@github.com:example/new-source.git",
                    "upgrade_ref": "v1.1.0",
                    "resolved_upgrade_commit": "new-commit",
                    "baseline_ref": "v1.0.0",
                    "entries": [
                        {"path": "docs/platform/consumer/quickstart.md", "action": "conflict"},
                    ],
                    "required_manual_actions": [],
                },
                apply_payload={
                    "results": [
                        {"path": "docs/platform/consumer/quickstart.md", "result": "conflict"},
                    ]
                },
            )

            result = _run(
                [
                    sys.executable,
                    str(POSTCHECK_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertEqual(report.get("reconcile_report_source"), "recomputed-stale-artifact")
            stale_reasons = report.get("reconcile_report_stale_reasons", [])
            self.assertIn("metadata-source-mismatch", stale_reasons)
            self.assertGreater(
                int(report.get("reconcile_summary", {}).get("conflicts_unresolved_count", 0)),
                0,
            )
            self.assertIn(
                "reconcile-conflicts-unresolved",
                report.get("summary", {}).get("blocked_reasons", []),
            )
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_postcheck_repo_mode_docs_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            _init_git_repo(repo)
            _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode("template-source"))
            _write(repo / "Makefile", ".PHONY: quality-docs-check-blueprint-template-sync\nquality-docs-check-blueprint-template-sync:\n\t@echo ok\n")
            _write_validate_report(repo, status="success")
            _write_reconcile_report(repo, conflicts_unresolved_count=0, blocked=False)

            result = _run(
                [
                    sys.executable,
                    str(POSTCHECK_SCRIPT),
                    "--repo-root",
                    str(repo),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertEqual(
                report.get("docs_hook_checks", {}).get("targets"),
                ["quality-docs-check-blueprint-template-sync"],
            )
            self.assertEqual(report.get("docs_hook_checks", {}).get("failed_targets"), [])
            self.assertEqual(len(report.get("docs_hook_checks", {}).get("command_results", [])), 1)
            _assert_json_schema(report, POSTCHECK_SCHEMA)


if __name__ == "__main__":
    unittest.main()
