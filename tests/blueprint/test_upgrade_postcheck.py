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


def _write_validate_report(
    repo: Path,
    *,
    status: str,
    prune_glob_violation_count: int = 0,
    prune_glob_violations: list[str] | None = None,
) -> None:
    payload: dict[str, object] = {
        "summary": {
            "status": status,
        }
    }
    if prune_glob_violation_count > 0:
        payload["prune_glob_check"] = {
            "status": "failure",
            "globs_checked": ["docs/blueprint/architecture/decisions/ADR-*.md"],
            "violations": prune_glob_violations or [],
            "violation_count": prune_glob_violation_count,
            "remediation_hint": "Remove the listed files and re-run: make blueprint-upgrade-consumer-validate",
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


FIXTURE_DIR = REPO_ROOT / "tests/blueprint/fixtures/shell_behavioral_check"


def _write_apply_report_with_merged_sh(repo: Path, sh_path_relative: str) -> None:
    """Write plan, apply, and reconcile reports for a single result=merged .sh file.

    The reconcile report includes metadata that exactly matches the plan so that
    the stale-detection check does NOT recompute it (which would classify the
    merge-required plan entry as conflicts_unresolved).
    """
    source = "git@github.com:example/source.git"
    upgrade_ref = "v1.1.0"
    commit = "abc123"
    baseline = "v1.0.0"

    apply_payload = {
        "results": [
            {
                "path": sh_path_relative,
                "planned_action": "merge-required",
                "planned_operation": "update",
                "result": "merged",
                "reason": "diverged from baseline; 3-way merge applied",
            }
        ]
    }
    _write(repo / "artifacts/blueprint/upgrade_apply.json", json.dumps(apply_payload) + "\n")

    plan_payload = {
        "source": source,
        "upgrade_ref": upgrade_ref,
        "resolved_upgrade_commit": commit,
        "baseline_ref": baseline,
        "entries": [{"path": sh_path_relative, "action": "merge-required", "operation": "update"}],
        "required_manual_actions": [],
    }
    _write(repo / "artifacts/blueprint/upgrade_plan.json", json.dumps(plan_payload) + "\n")

    # Write a reconcile report whose metadata matches the plan so the stale-detection
    # check does NOT recompute it (recomputation would classify merge-required plan
    # entries as conflicts_unresolved, masking the behavioral gate under test).
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
        repo / "artifacts/blueprint/upgrade/upgrade_reconcile_report.json",
        json.dumps(reconcile_payload) + "\n",
    )


class BehavioralCheckPostcheckTests(unittest.TestCase):
    """AC-001 through AC-005: behavioral gate integration via postcheck orchestrator."""

    def _base_repo(self, tmpdir: str, *, repo_mode: str = "generated-consumer") -> Path:
        repo = Path(tmpdir) / "repo"
        _init_git_repo(repo)
        _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode(repo_mode))
        _write_validate_report(repo, status="success")
        _write_reconcile_report(repo, conflicts_unresolved_count=0, blocked=False)
        return repo

    def _run_postcheck(self, repo: Path, *, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(POSTCHECK_SCRIPT), "--repo-root", str(repo)]
        if extra_args:
            cmd.extend(extra_args)
        return _run(cmd, cwd=REPO_ROOT)

    def test_behavioral_check_passes_for_clean_merged_script(self) -> None:
        """AC-003: merged .sh with all defs present → postcheck succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self._base_repo(tmpdir)
            rel = "scripts/bin/platform/clean_script.sh"
            dest = repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text((FIXTURE_DIR / "clean_script.sh").read_text())
            _write_apply_report_with_merged_sh(repo, rel)

            result = self._run_postcheck(repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertEqual(report["summary"]["status"], "success")
            self.assertNotIn("behavioral-check-failure", report["summary"]["blocked_reasons"])
            bc = report["behavioral_check"]
            self.assertEqual(bc["status"], "pass")
            self.assertFalse(bc["skipped"])
            self.assertEqual(bc["syntax_errors"], [])
            self.assertEqual(bc["unresolved_symbols"], [])
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_behavioral_check_blocks_on_syntax_error(self) -> None:
        """AC-001: syntax error in merged .sh → postcheck fails; error in report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self._base_repo(tmpdir)
            rel = "scripts/bin/platform/syntax_error_script.sh"
            dest = repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text((FIXTURE_DIR / "syntax_error_script.sh").read_text())
            _write_apply_report_with_merged_sh(repo, rel)

            result = self._run_postcheck(repo)

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertEqual(report["summary"]["status"], "failure")
            # AC-005: blocked_reasons contains behavioral-check-failure iff status=fail
            self.assertIn("behavioral-check-failure", report["summary"]["blocked_reasons"])
            bc = report["behavioral_check"]
            self.assertEqual(bc["status"], "fail")
            self.assertGreater(len(bc["syntax_errors"]), 0)
            entry = bc["syntax_errors"][0]
            # REQ-003: file path present in finding
            self.assertIn("syntax_error_script.sh", entry["file"])
            self.assertIn("error", entry)
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_behavioral_check_blocks_on_unresolved_symbol(self) -> None:
        """AC-002: dropped function def in merged .sh → postcheck fails; symbol in report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self._base_repo(tmpdir)
            rel = "scripts/bin/platform/missing_def_script.sh"
            dest = repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text((FIXTURE_DIR / "missing_def_script.sh").read_text())
            _write_apply_report_with_merged_sh(repo, rel)

            result = self._run_postcheck(repo)

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertEqual(report["summary"]["status"], "failure")
            # AC-005
            self.assertIn("behavioral-check-failure", report["summary"]["blocked_reasons"])
            bc = report["behavioral_check"]
            self.assertEqual(bc["status"], "fail")
            self.assertGreater(len(bc["unresolved_symbols"]), 0)
            symbols = [e["symbol"] for e in bc["unresolved_symbols"]]
            self.assertIn("setup_environment", symbols)
            # REQ-003: file, symbol, and line present
            for entry in bc["unresolved_symbols"]:
                self.assertIn("file", entry)
                self.assertIn("symbol", entry)
                self.assertIn("line", entry)
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_behavioral_check_skipped_via_flag(self) -> None:
        """AC-004: --skip-behavioral-check → gate skipped; postcheck exits zero for that reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self._base_repo(tmpdir)
            rel = "scripts/bin/platform/missing_def_script.sh"
            dest = repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text((FIXTURE_DIR / "missing_def_script.sh").read_text())
            _write_apply_report_with_merged_sh(repo, rel)

            result = self._run_postcheck(repo, extra_args=["--skip-behavioral-check"])

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            bc = report["behavioral_check"]
            self.assertEqual(bc["status"], "skipped")
            self.assertTrue(bc["skipped"])
            self.assertNotIn("behavioral-check-failure", report["summary"]["blocked_reasons"])
            # AC-004: warning must appear in stderr
            self.assertIn("behavioral", result.stderr.lower())
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_behavioral_check_blocked_reasons_absent_when_passing(self) -> None:
        """AC-005: behavioral-check-failure NOT in blocked_reasons when status=pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self._base_repo(tmpdir)
            rel = "scripts/bin/platform/clean_script.sh"
            dest = repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text((FIXTURE_DIR / "clean_script.sh").read_text())
            _write_apply_report_with_merged_sh(repo, rel)

            result = self._run_postcheck(repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            self.assertNotIn("behavioral-check-failure", report["summary"]["blocked_reasons"])

    def test_behavioral_check_summary_fields_present(self) -> None:
        """REQ-006: postcheck summary includes behavioral_check_skipped and behavioral_check_failure_count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self._base_repo(tmpdir)
            _write_reconcile_report(repo, conflicts_unresolved_count=0, blocked=False)

            result = self._run_postcheck(repo)

            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            summary = report["summary"]
            self.assertIn("behavioral_check_skipped", summary)
            self.assertIn("behavioral_check_failure_count", summary)
            self.assertIsInstance(summary["behavioral_check_skipped"], bool)
            self.assertIsInstance(summary["behavioral_check_failure_count"], int)
            _assert_json_schema(report, POSTCHECK_SCHEMA)

    def test_postcheck_blocks_when_validate_report_has_prune_glob_violations(self) -> None:
        """REQ-014: postcheck exits non-zero; prune-glob-violations in blocked_reasons."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            _init_git_repo(repo)
            _write(repo / "blueprint/contract.yaml", _contract_text_for_repo_mode("generated-consumer"))
            _write_validate_report(
                repo,
                status="failure",
                prune_glob_violation_count=1,
                prune_glob_violations=["docs/blueprint/architecture/decisions/ADR-issue-99-test.md"],
            )
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

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            report = _load_json(repo / "artifacts/blueprint/upgrade_postcheck.json")
            reasons = report.get("summary", {}).get("blocked_reasons", [])
            self.assertIn("prune-glob-violations", reasons)
            prune_violations = report.get("prune_glob_violations", {})
            self.assertEqual(prune_violations.get("violation_count"), 1)
            self.assertIn(
                "docs/blueprint/architecture/decisions/ADR-issue-99-test.md",
                prune_violations.get("violations", []),
            )
            _assert_json_schema(report, POSTCHECK_SCHEMA)


if __name__ == "__main__":
    unittest.main()
