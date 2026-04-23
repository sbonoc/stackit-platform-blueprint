# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Remove `2>&1` from `run_cmd_capture` in `scripts/lib/shell/exec.sh`
- [x] T-002 Add inline doc comment above `run_cmd_capture` describing the stdout-only contract
- [x] T-003 No blueprint docs or diagram updates required (doc comment is the authoritative documentation)
- [x] T-004 No consumer-facing docs updates required (no consumer-facing contract changes)

## Test Automation
- [x] T-101 Add `test_run_cmd_capture_does_not_merge_stderr_into_stdout` in `tests/blueprint/contract_refactor_scripts_cases.py` asserting: (a) `2>&1` is absent from the `run_cmd_capture` function body, (b) the doc comment is present
- [x] T-102 No new contract tests required (no new contract surfaces)
- [x] T-103 No filter/payload-transform logic — gate not applicable
- [x] T-104 Pre-PR finding (stderr merged into stdout) translated to structural test before implementing the fix; fix turns it green
- [x] T-105 No boundary/integration tests required beyond T-101

## Validation and Release Readiness
- [x] T-201 Run `shellcheck --severity=error scripts/lib/shell/exec.sh` and `make quality-hooks-fast`
- [x] T-202 Attach validation evidence to `traceability.md`
- [x] T-203 Confirm no stale TODOs, dead code, or drift in `exec.sh`
- [x] T-204 Run `make docs-build` and `make docs-smoke`
- [x] T-205 Run `make quality-hardening-review`

## Publish
- [x] P-001 Update `hardening_review.md`
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 PR description references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; blueprint utility only
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact
