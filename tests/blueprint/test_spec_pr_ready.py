from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "scripts/bin/quality/check_spec_pr_ready.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_spec_pr_ready", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load checker module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_checker = _load_checker()
_check_tasks = _checker._check_tasks
_check_plan = _checker._check_plan
_check_hardening_review = _checker._check_hardening_review
_check_pr_context = _checker._check_pr_context
_resolve_spec_dir = _checker._resolve_spec_dir
PREFIX = _checker.PREFIX


# ---------------------------------------------------------------------------
# Fixtures: minimal "filled" content that should produce zero violations
# ---------------------------------------------------------------------------

_FILLED_TASKS = """\
# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Create the new check script with focused check functions
- [x] T-002 Add make target to blueprint makefile template and regenerate
- [x] T-003 Wire into hooks_fast.sh with branch-pattern guard
- [x] T-004 Create ADR documenting the design decision

## Test Automation
- [x] T-101 Add or update unit tests
- [x] T-102 Add or update contract tests
- [x] T-103 No filter/payload-transform logic; gate not applicable
- [x] T-104 Triggering incident translated into per-file negative-path tests
- [x] T-105 Add boundary/integration tests where required

## Validation and Release Readiness
- [x] T-201 Run required Make validation bundles
- [x] T-202 Attach evidence to traceability document
- [x] T-203 Confirm no stale TODOs/dead code/drift
- [x] T-204 Run documentation validation
- [x] T-205 Run hardening review validation bundle

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [x] A-002 Backend app lanes are available
- [x] A-003 Frontend app lanes are available
- [x] A-004 Aggregate gates are available
- [x] A-005 Port-forward operational wrappers are available
"""

_FILLED_PLAN = """\
# Implementation Plan

## Constitution Gates (Pre-Implementation)
- Simplicity gate: single script, no shared abstractions
- Anti-abstraction gate: use pathlib and re directly; no external parser
- Integration-first testing gate: tests drive detection logic
- Positive-path filter/transform test gate: not applicable — no filter/transform logic
- Finding-to-test translation gate: triggering incident translated into negative-path tests

## Delivery Slices
1. Slice 1 — script and make target: create check_spec_pr_ready.py, add make target
2. Slice 2 — hooks integration and docs: wire hooks_fast.sh, add ADR

## Change Strategy
- Migration/rollout sequence: additive; no migration required
- Backward compatibility policy: new additive target; existing workflows unaffected
- Rollback plan: remove the make target and hooks_fast.sh invocation

## Validation Strategy (Shift-Left)
- Unit checks: test_spec_pr_ready.py — positive and negative-path per file
- Contract checks: make infra-contract-test-fast
- Integration checks: make quality-hooks-fast on the SDD branch
- E2E checks: N/A — local tooling only

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: tooling-only change

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR created; core-targets doc auto-updated
- Consumer docs updates: none
- Mermaid diagrams updated: none
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: violations printed with prefix; exit code is the signal
- Alerts/ownership: none; blueprint maintainer owns the script
- Runbook updates: none required

## Risks and Mitigations
- Risk 1: static label allowlist drifts from scaffold templates -> mitigation: per-label negative-path tests catch drift at test time
"""

_FILLED_HARDENING_REVIEW = """\
# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: publish-gate files shipped with all-placeholder content in previous spec; fixed by adding check_spec_pr_ready.py

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new metrics; violations printed to stdout with prefix
- Operational diagnostics updates: each violation includes file name and line number

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: four focused check functions; single responsibility per function
- Test-automation and pyramid checks: positive and per-file negative-path tests added
- Documentation/diagram/CI/skill consistency checks: ADR created; core-targets doc updated

## Proposals Only (Not Implemented)
- Proposal 1: add a spec template drift test that fails when .spec-kit template labels change without updating the allowlist in check_spec_pr_ready.py — deferred; requires parsing template files
"""

_FILLED_PR_CONTEXT = """\
# PR Context

## Summary
- Work item: 2026-04-22-quality-spec-pr-ready-publish-gate
- Objective: add quality-spec-pr-ready make target to detect scaffold placeholders in publish-gate files
- Scope boundaries: check_spec_pr_ready.py, makefile template, hooks_fast.sh, tests

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007
- Contract surfaces changed: quality-spec-pr-ready make target added

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/quality/check_spec_pr_ready.py` — check functions and main
  - `scripts/bin/quality/hooks_fast.sh` — branch-pattern guard wiring
- High-risk files:
  - `scripts/bin/quality/hooks_fast.sh` — conditional invocation change

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make quality-sdd-check`, `make infra-contract-test-fast`
- Result summary: all gates green
- Artifact references: specs/2026-04-22-quality-spec-pr-ready-publish-gate/traceability.md

## Risk and Rollback
- Main risks: static label allowlist must be updated when scaffold templates change
- Rollback strategy: remove make target from template and hooks_fast.sh invocation; rerun make blueprint-render-makefile

## Deferred Proposals
- Proposal 1 (not implemented): spec template drift test that validates allowlist against scaffold templates — deferred; requires template parser
"""


class PositivePathTests(unittest.TestCase):
    """A fully-filled spec dir with no scaffold placeholders must produce zero violations."""

    def test_filled_tasks_no_violations(self) -> None:
        violations = _check_tasks(_FILLED_TASKS, "tasks.md")
        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_filled_plan_no_violations(self) -> None:
        violations = _check_plan(_FILLED_PLAN, "plan.md")
        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_filled_hardening_review_no_violations(self) -> None:
        violations = _check_hardening_review(_FILLED_HARDENING_REVIEW, "hardening_review.md")
        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_filled_pr_context_no_violations(self) -> None:
        violations = _check_pr_context(_FILLED_PR_CONTEXT, "pr_context.md")
        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_fully_filled_spec_dir_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            spec_dir = repo_root / "specs" / "2026-04-22-test-item"
            spec_dir.mkdir(parents=True)
            (spec_dir / "tasks.md").write_text(_FILLED_TASKS, encoding="utf-8")
            (spec_dir / "plan.md").write_text(_FILLED_PLAN, encoding="utf-8")
            (spec_dir / "hardening_review.md").write_text(_FILLED_HARDENING_REVIEW, encoding="utf-8")
            (spec_dir / "pr_context.md").write_text(_FILLED_PR_CONTEXT, encoding="utf-8")
            old_slug = os.environ.get("SPEC_SLUG")
            try:
                os.environ["SPEC_SLUG"] = "2026-04-22-test-item"
                exit_code = _checker.main(repo_root=repo_root)
            finally:
                if old_slug is None:
                    os.environ.pop("SPEC_SLUG", None)
                else:
                    os.environ["SPEC_SLUG"] = old_slug
            self.assertEqual(exit_code, 0, "expected exit code 0 for fully-filled spec dir")


# ---------------------------------------------------------------------------
# tasks.md checks
# ---------------------------------------------------------------------------

class TasksCheckTests(unittest.TestCase):

    def test_unchecked_box_produces_violation(self) -> None:
        content = _FILLED_TASKS.replace("- [x] G-001", "- [ ] G-001", 1)
        violations = _check_tasks(content, "tasks.md")
        self.assertTrue(any("unchecked task box" in v for v in violations), violations)

    def test_scaffold_task_t001_produces_violation(self) -> None:
        content = _FILLED_TASKS.replace(
            "- [x] T-001 Create the new check script with focused check functions",
            "- [x] T-001 Update contract/governance surfaces",
        )
        violations = _check_tasks(content, "tasks.md")
        self.assertTrue(any("verbatim scaffold task text" in v for v in violations), violations)

    def test_scaffold_task_t002_produces_violation(self) -> None:
        content = _FILLED_TASKS.replace(
            "- [x] T-002 Add make target to blueprint makefile template and regenerate",
            "- [x] T-002 Implement runtime/code changes",
        )
        violations = _check_tasks(content, "tasks.md")
        self.assertTrue(any("verbatim scaffold task text" in v for v in violations), violations)

    def test_scaffold_task_t003_produces_violation(self) -> None:
        content = _FILLED_TASKS.replace(
            "- [x] T-003 Wire into hooks_fast.sh with branch-pattern guard",
            "- [x] T-003 Update blueprint docs/diagrams",
        )
        violations = _check_tasks(content, "tasks.md")
        self.assertTrue(any("verbatim scaffold task text" in v for v in violations), violations)

    def test_scaffold_task_t004_produces_violation(self) -> None:
        content = _FILLED_TASKS.replace(
            "- [x] T-004 Create ADR documenting the design decision",
            "- [x] T-004 Update consumer-facing docs/diagrams when contracts/behavior change",
        )
        violations = _check_tasks(content, "tasks.md")
        self.assertTrue(any("verbatim scaffold task text" in v for v in violations), violations)

    def test_missing_p001_produces_violation(self) -> None:
        content = _FILLED_TASKS.replace(
            "- [x] P-001 Update `hardening_review.md`",
            "- [ ] P-001 Update `hardening_review.md`",
        )
        violations = _check_tasks(content, "tasks.md")
        # Both unchecked box AND missing P-001 [x]
        self.assertTrue(any("P-001" in v for v in violations), violations)

    def test_missing_p003_produces_violation(self) -> None:
        lines = _FILLED_TASKS.splitlines()
        content = "\n".join(ln for ln in lines if "P-003" not in ln)
        violations = _check_tasks(content, "tasks.md")
        self.assertTrue(any("P-003" in v for v in violations), violations)


# ---------------------------------------------------------------------------
# plan.md checks
# ---------------------------------------------------------------------------

class PlanCheckTests(unittest.TestCase):

    def test_empty_simplicity_gate_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "- Simplicity gate: single script, no shared abstractions",
            "- Simplicity gate:",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("Simplicity gate:" in v for v in violations), violations)

    def test_empty_migration_sequence_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "- Migration/rollout sequence: additive; no migration required",
            "- Migration/rollout sequence:",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("Migration/rollout sequence:" in v for v in violations), violations)

    def test_empty_unit_checks_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "- Unit checks: test_spec_pr_ready.py — positive and negative-path per file",
            "- Unit checks:",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("Unit checks:" in v for v in violations), violations)

    def test_scaffold_slice_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "1. Slice 1 — script and make target: create check_spec_pr_ready.py, add make target",
            "1. Slice 1:",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("delivery slice placeholder" in v for v in violations), violations)

    def test_select_one_impact_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "- App onboarding impact: no-impact",
            "- App onboarding impact: no-impact | impacted (select one)",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("select one" in v for v in violations), violations)

    def test_scaffold_risk_mitigation_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "- Risk 1: static label allowlist drifts from scaffold templates -> mitigation: per-label negative-path tests catch drift at test time",
            "- Risk 1 -> mitigation:",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("risk mitigation placeholder" in v for v in violations), violations)

    def test_empty_logging_field_produces_violation(self) -> None:
        content = _FILLED_PLAN.replace(
            "- Logging/metrics/traces: violations printed with prefix; exit code is the signal",
            "- Logging/metrics/traces:",
        )
        violations = _check_plan(content, "plan.md")
        self.assertTrue(any("Logging/metrics/traces:" in v for v in violations), violations)

    def test_filled_plan_no_violations(self) -> None:
        violations = _check_plan(_FILLED_PLAN, "plan.md")
        self.assertEqual(violations, [], msg="\n".join(violations))


# ---------------------------------------------------------------------------
# hardening_review.md checks
# ---------------------------------------------------------------------------

class HardeningReviewCheckTests(unittest.TestCase):

    def test_empty_finding_produces_violation(self) -> None:
        content = _FILLED_HARDENING_REVIEW.replace(
            "- Finding 1: publish-gate files shipped with all-placeholder content in previous spec; fixed by adding check_spec_pr_ready.py",
            "- Finding 1:",
        )
        violations = _check_hardening_review(content, "hardening_review.md")
        self.assertTrue(any("finding placeholder" in v for v in violations), violations)

    def test_no_findings_at_all_produces_violation(self) -> None:
        content = """\
# Hardening Review

## Repository-Wide Findings Fixed

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new metrics
- Operational diagnostics updates: none

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: compliant
- Test-automation and pyramid checks: tests added
- Documentation/diagram/CI/skill consistency checks: docs updated

## Proposals Only (Not Implemented)
- Proposal 1: some proposal content here
"""
        violations = _check_hardening_review(content, "hardening_review.md")
        self.assertTrue(any("Repository-Wide Findings Fixed" in v for v in violations), violations)

    def test_empty_metrics_field_produces_violation(self) -> None:
        content = _FILLED_HARDENING_REVIEW.replace(
            "- Metrics/logging/tracing updates: no new metrics; violations printed to stdout with prefix",
            "- Metrics/logging/tracing updates:",
        )
        violations = _check_hardening_review(content, "hardening_review.md")
        self.assertTrue(any("Metrics/logging/tracing updates:" in v for v in violations), violations)

    def test_empty_solid_field_produces_violation(self) -> None:
        content = _FILLED_HARDENING_REVIEW.replace(
            "- SOLID / Clean Architecture / Clean Code / DDD checks: four focused check functions; single responsibility per function",
            "- SOLID / Clean Architecture / Clean Code / DDD checks:",
        )
        violations = _check_hardening_review(content, "hardening_review.md")
        self.assertTrue(any("SOLID" in v for v in violations), violations)

    def test_scaffold_proposal_with_no_none_produces_violation(self) -> None:
        content = """\
# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: a real finding with content

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no changes
- Operational diagnostics updates: none required

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: compliant
- Test-automation and pyramid checks: tests added
- Documentation/diagram/CI/skill consistency checks: docs updated

## Proposals Only (Not Implemented)
- Proposal 1:
"""
        violations = _check_hardening_review(content, "hardening_review.md")
        self.assertTrue(any("Proposals Only" in v for v in violations), violations)

    def test_explicit_none_proposal_passes(self) -> None:
        content = """\
# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: some real finding here

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no changes
- Operational diagnostics updates: none required

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: compliant
- Test-automation and pyramid checks: tests added
- Documentation/diagram/CI/skill consistency checks: docs updated

## Proposals Only (Not Implemented)
- none
"""
        violations = _check_hardening_review(content, "hardening_review.md")
        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_filled_hardening_review_no_violations(self) -> None:
        violations = _check_hardening_review(_FILLED_HARDENING_REVIEW, "hardening_review.md")
        self.assertEqual(violations, [], msg="\n".join(violations))


# ---------------------------------------------------------------------------
# pr_context.md checks
# ---------------------------------------------------------------------------

class PrContextCheckTests(unittest.TestCase):

    def test_empty_work_item_produces_violation(self) -> None:
        content = _FILLED_PR_CONTEXT.replace(
            "- Work item: 2026-04-22-quality-spec-pr-ready-publish-gate",
            "- Work item:",
        )
        violations = _check_pr_context(content, "pr_context.md")
        self.assertTrue(any("Work item:" in v for v in violations), violations)

    def test_empty_objective_produces_violation(self) -> None:
        content = _FILLED_PR_CONTEXT.replace(
            "- Objective: add quality-spec-pr-ready make target to detect scaffold placeholders in publish-gate files",
            "- Objective:",
        )
        violations = _check_pr_context(content, "pr_context.md")
        self.assertTrue(any("Objective:" in v for v in violations), violations)

    def test_empty_requirement_ids_produces_violation(self) -> None:
        content = _FILLED_PR_CONTEXT.replace(
            "- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008",
            "- Requirement IDs covered:",
        )
        violations = _check_pr_context(content, "pr_context.md")
        self.assertTrue(any("Requirement IDs covered:" in v for v in violations), violations)

    def test_empty_result_summary_produces_violation(self) -> None:
        content = _FILLED_PR_CONTEXT.replace(
            "- Result summary: all gates green",
            "- Result summary:",
        )
        violations = _check_pr_context(content, "pr_context.md")
        self.assertTrue(any("Result summary:" in v for v in violations), violations)

    def test_missing_primary_reviewer_files_produces_violation(self) -> None:
        content = """\
# PR Context

## Summary
- Work item: some-work-item
- Objective: some objective here
- Scope boundaries: some scope

## Requirement Coverage
- Requirement IDs covered: FR-001
- Acceptance criteria covered: AC-001
- Contract surfaces changed: none

## Key Reviewer Files
- Primary files to review first:
- High-risk files:
  - `some/file.py`

## Validation Evidence
- Required commands executed: make quality-hooks-fast
- Result summary: all green
- Artifact references: traceability.md

## Risk and Rollback
- Main risks: minimal
- Rollback strategy: revert commit

## Deferred Proposals
- Proposal 1 (not implemented): some deferred proposal here
"""
        violations = _check_pr_context(content, "pr_context.md")
        self.assertTrue(
            any("Primary files to review first" in v for v in violations),
            msg=f"expected violation for missing sub-bullets, got: {violations}",
        )

    def test_scaffold_deferred_proposal_produces_violation(self) -> None:
        content = _FILLED_PR_CONTEXT.replace(
            "- Proposal 1 (not implemented): spec template drift test that validates allowlist against scaffold templates — deferred; requires template parser",
            "- Proposal 1 (not implemented):",
        )
        violations = _check_pr_context(content, "pr_context.md")
        self.assertTrue(any("scaffold deferred proposal" in v for v in violations), violations)

    def test_filled_pr_context_no_violations(self) -> None:
        violations = _check_pr_context(_FILLED_PR_CONTEXT, "pr_context.md")
        self.assertEqual(violations, [], msg="\n".join(violations))


# ---------------------------------------------------------------------------
# Branch resolution and spec dir
# ---------------------------------------------------------------------------

class BranchResolutionTests(unittest.TestCase):

    def test_spec_slug_env_var_overrides_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            spec_dir = repo_root / "specs" / "2026-04-22-my-work-item"
            spec_dir.mkdir(parents=True)
            old_slug = os.environ.get("SPEC_SLUG")
            try:
                os.environ["SPEC_SLUG"] = "2026-04-22-my-work-item"
                result = _resolve_spec_dir(repo_root)
                self.assertEqual(result, spec_dir)
            finally:
                if old_slug is None:
                    os.environ.pop("SPEC_SLUG", None)
                else:
                    os.environ["SPEC_SLUG"] = old_slug

    def test_sdd_branch_pattern_resolves_spec_dir(self) -> None:
        """Verify the SDD branch regex matches correctly."""
        import re
        pattern = _checker._SDD_BRANCH_PATTERN
        m = pattern.match("codex/2026-04-22-quality-spec-pr-ready-publish-gate")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "2026-04-22-quality-spec-pr-ready-publish-gate")

    def test_non_sdd_branch_does_not_match_pattern(self) -> None:
        import re
        pattern = _checker._SDD_BRANCH_PATTERN
        self.assertIsNone(pattern.match("main"))
        self.assertIsNone(pattern.match("feature/something"))
        self.assertIsNone(pattern.match("codex/not-date-prefixed"))


class MissingSpecDirTests(unittest.TestCase):

    def test_nonexistent_spec_dir_exits_nonzero(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["python3", str(SCRIPT_PATH)],
                env={**os.environ, "SPEC_SLUG": "2026-04-22-does-not-exist"},
                cwd=Path(tmpdir),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(PREFIX, result.stderr + result.stdout)

    def test_missing_file_in_spec_dir_exits_nonzero(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "specs" / "2026-04-22-partial"
            spec_dir.mkdir(parents=True)
            # Only create tasks.md — leave others missing
            (spec_dir / "tasks.md").write_text(_FILLED_TASKS, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(SCRIPT_PATH)],
                env={**os.environ, "SPEC_SLUG": "2026-04-22-partial"},
                cwd=Path(tmpdir),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
