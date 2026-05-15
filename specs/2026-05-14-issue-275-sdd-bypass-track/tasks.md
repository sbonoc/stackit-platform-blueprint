# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Write `tests/blueprint/test_sdd_bypass_track.py` with AC-001 through AC-005 test cases (red)
- [x] T-002 Confirm all 5 tests fail before the bypass logic is added
- [x] T-003 Add `SPEC_READY_EXCEPTION` + `authorized-by` field parsing to `check_sdd_assets.py`
- [x] T-004 Add bypass branch: skip non-`{spec.md, pr_context.md}` artifact checks when exception is valid and `authorized-by` is present
- [x] T-005 Add `authorized-by` required violation when exception is set but field is absent/empty/`none`
- [x] T-006 Demote "implementation tasks checked while SPEC_READY not true" to warning when exception + `authorized-by` are set
- [x] T-007 Emit `[METRIC] name=sdd_exception_gate_total value=1 type=<type> authorized_by=<handle>` on the bypass path
- [x] T-008 Update `spec.md` scaffold template to include `SPEC_READY_EXCEPTION: none` and `authorized-by: none` default fields
- [x] T-009 Register `tests/blueprint/test_sdd_bypass_track.py` in `test_pyramid_contract.json` unit scope
- [x] T-010 Confirm all 5 tests pass (green)
- [x] T-011 Add `## Lightweight SDD Bypass Track` subsection to `AGENTS.md`

## Test Automation
- [x] T-101 `tests/blueprint/test_sdd_bypass_track.py` — AC-001: bypass path skips non-essential artifact checks for valid exception + authorized-by
- [x] T-102 `tests/blueprint/test_sdd_bypass_track.py` — AC-002: no specs/ dir → exit 0 (chore passive pass, regression guard)
- [x] T-103 `tests/blueprint/test_sdd_bypass_track.py` — AC-003: SPEC_READY:true + no exception → all 10 artifacts still required (no regression)
- [x] T-104 `tests/blueprint/test_sdd_bypass_track.py` — AC-004: bypass path emits sdd_exception_gate_total metric line
- [x] T-105 `tests/blueprint/test_sdd_bypass_track.py` — AC-005: exception set but no authorized-by → violation raised

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 N/A — NFR-A11Y-001 declared in spec.md as not applicable (no UI changes)
- [x] T-A02 N/A — no UI changes
- [x] T-A03 N/A — no UI changes
- [x] T-A04 N/A — no UI changes
- [x] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [x] T-201 Run `uv run python3 -m pytest tests/blueprint/test_sdd_bypass_track.py -v` and `make test-unit-all`
- [x] T-202 Attach test evidence to traceability document
- [x] T-203 Confirm no stale TODOs or drift — `make quality-sdd-check-all` PASS
- [x] T-204 Run `make docs-build` and `make docs-smoke`
- [x] T-205 Run `make quality-hardening-review`

## Publish
- [x] P-001 Update `hardening_review.md` with findings and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement coverage, key reviewer files, test evidence, and rollback notes
- [x] P-003 Ensure PR description references `pr_context.md` and closes #275

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; targets unchanged by this work item
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact; targets unchanged
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact; targets unchanged
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact; targets unchanged
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact; targets unchanged
