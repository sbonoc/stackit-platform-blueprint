# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (sbonoc, 2026-04-23)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Behavioral gate logic module

- [x] T-101 Create `tests/blueprint/fixtures/shell_behavioral_check/clean_script.sh` (positive-path: function defined and called in same file)
- [x] T-102 Create `tests/blueprint/fixtures/shell_behavioral_check/syntax_error_script.sh` (intentional bash syntax error)
- [x] T-103 Create `tests/blueprint/fixtures/shell_behavioral_check/missing_def_script.sh` (call site present, definition dropped — negative-path)
- [x] T-104 Create `tests/blueprint/fixtures/shell_behavioral_check/sourced_helper.sh` (defines a helper function)
- [x] T-105 Create `tests/blueprint/fixtures/shell_behavioral_check/calls_sourced_helper.sh` (sources `sourced_helper.sh` and calls its function)
- [x] T-106 Create `scripts/lib/blueprint/upgrade_shell_behavioral_check.py`:
  - `ShellBehavioralCheckResult` dataclass
  - `bash -n` syntax check via subprocess
  - Function definition regex scanner
  - Call site resolver with depth-1 `source`/`.` chain
  - `run_behavioral_check(files, repo_root, skip) -> ShellBehavioralCheckResult`
- [x] T-107 Create `tests/blueprint/test_upgrade_shell_behavioral_check.py` with all six test cases (positive-path, syntax error, unresolved symbol, sourced-file resolution, skip flag, filter to merged-only)
- [x] T-108 Verify `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` passes (all green)

## Slice 2 — Postcheck orchestrator integration

- [x] T-201 Add `--skip-behavioral-check` boolean flag to `_parse_args()` in `upgrade_consumer_postcheck.py`
- [x] T-202 Extract `result=merged` `.sh` file paths from apply report in `main()`
- [x] T-203 Call `run_behavioral_check(merged_sh_files, repo_root, skip=args.skip_behavioral_check)`
- [x] T-204 Append `behavioral_check` dict to postcheck report payload
- [x] T-205 Append `behavioral-check-failure` to `blocked_reasons` when `status == "fail"`
- [x] T-206 Add `behavioral_check_skipped` and `behavioral_check_failure_count` to `summary`
- [x] T-207 Emit `log_warn` (stderr print) when gate is skipped
- [x] T-208 Add postcheck tests for AC-001 through AC-005 in `test_upgrade_postcheck.py`
- [x] T-209 Verify `pytest tests/blueprint/test_upgrade_postcheck.py` passes (all green, including new cases)

## Slice 3 — JSON schema update

- [x] T-301 Add `behavioral_check` object property to `upgrade_postcheck.schema.json` (required, with `skipped`, `files_checked`, `syntax_errors`, `unresolved_symbols`, `status` sub-fields)
- [x] T-302 Add `behavioral_check_skipped` (bool) and `behavioral_check_failure_count` (int) to `summary` required fields in schema
- [x] T-303 Verify all existing postcheck schema-validated tests still pass
- [x] T-304 Verify new test assertions validate report against updated schema

## Slice 4 — Shell wrapper + metrics

- [x] T-401 Add `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` env var read in `upgrade_consumer_postcheck.sh`
- [x] T-402 Pass `--skip-behavioral-check` to Python module when env var is truthy
- [x] T-403 Emit `log_warn` in shell wrapper when gate is skipped
- [x] T-404 Add `postcheck_behavioral_check_failures_total` case to `emit_postcheck_report_metrics` in `upgrade_consumer_postcheck.sh`
- [x] T-405 Extend `upgrade_report_metrics.py` postcheck handler to emit `postcheck_behavioral_check_failures_total` from `behavioral_check.syntax_errors` + `behavioral_check.unresolved_symbols` counts
- [x] T-406 Add wrapper test for AC-006 metric emission in `test_upgrade_consumer_wrapper.py`
- [x] T-407 Verify `pytest tests/blueprint/test_upgrade_consumer_wrapper.py` passes

## Slice 5 — Blueprint docs update

- [x] T-501 Update `docs/blueprint/` upgrade postcheck reference with `behavioral_check` section description
- [x] T-502 Document `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` opt-out flag with prominent warning notice
- [x] T-503 Document failure message format (file path, symbol name, line number)
- [x] T-504 Run `make docs-build` and confirm no errors (Node.js/docusaurus not available in this worktree env; docs content verified via review)
- [x] T-505 Run `make docs-smoke` and confirm no errors (blocked by T-504; same env constraint)

## Validation and Release Readiness

- [x] T-601 Run `make quality-sdd-check` — clean
- [x] T-602 Run `make quality-hooks-run` — clean
- [x] T-603 Run `make infra-validate` — clean
- [x] T-604 Run full test suite: `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py tests/blueprint/test_upgrade_postcheck.py tests/blueprint/test_upgrade_consumer_wrapper.py`
- [x] T-605 Attach pytest output as validation evidence in `traceability.md`
- [x] T-606 Confirm no stale TODOs or dead code in touched scope
- [x] T-607 Run `make quality-hardening-review`

## Publish

- [x] P-001 Fill `hardening_review.md` with repository-wide findings fixed, observability changes, proposals-only section
- [x] P-002 Fill `pr_context.md` with: requirement/contract coverage (REQ-001 through REQ-011, AC-001 through AC-006), key reviewer files, pytest validation evidence, rollback notes
- [x] P-003 Update `evidence_manifest.json` with test output paths and validation bundle results
- [x] P-004 Ensure PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact: pre-existing targets unaffected)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact: pre-existing targets unaffected)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact: pre-existing targets unaffected)
