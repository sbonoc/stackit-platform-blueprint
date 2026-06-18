# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated
- [x] G-006 Q-1 (budget ceiling values) resolved — Option A: `COST_CEILING_USD = 5`, `TOKEN_CEILING_INPUT = 500_000` as placeholder Python constants with calibration comment (PR #371 comment by sbonoc, 2026-06-17; spec.md § FR-004 Clarifications)

## Implementation

### Slice 1 — Design-contracts § C7 amendment + ADR
- [x] T-001 Amend `docs/blueprint/autonomous-factory/design-contracts.md` § C7 extension-field vocabulary: add `outcome_details.token_usage`, `outcome_details.merger_overhead`, `outcome_details.ticket_token_summary` rows; update `outcome_details.routing_keys` scope description
- [x] T-002 ADR-issue-368 committed and approved (status: approved)

### Slice 2 — Orchestrator token-usage accumulation
- [x] T-003 Specified in spec.md FR-002 + architecture.md Context A; implementation lands in #361 workspace
- [x] T-004 Specified in spec.md FR-001 + NFR-REL-001 (sentinel -1); implementation lands in #361 workspace
- [x] T-005 Specified in spec.md FR-002; implementation lands in #361 workspace
- [x] T-006 Specified in spec.md FR-005; scope widening documented in design-contracts.md (Slice 1 — complete in this PR)
- [x] T-007 Specified in spec.md FR-003 + architecture.md Context A (JSONL read-back); implementation lands in #361 workspace

### Slice 3 — `audit-cost` CLI sub-command
- [x] T-008 Specified in spec.md FR-004 + NFR-OPS-001; implementation lands in #361 workspace
- [x] T-009 Specified in spec.md FR-004 (`COST_CEILING_USD = 5`, `TOKEN_CEILING_INPUT = 500_000`); implementation lands in #361 workspace

### Slice 4 — Step02 routing fixture
- [x] T-010 Specified in spec.md FR-006; implementation lands in #361 workspace
- [x] T-011 Specified in spec.md FR-008; implementation lands in #361 workspace
- [x] T-012 Specified in spec.md FR-008; implementation lands in #361 workspace

## Test Automation
- [x] T-101 Specified in spec.md AC-001, AC-002, AC-005; test lands in #361 workspace
- [x] T-102 Specified in spec.md AC-003; test lands in #361 workspace
- [x] T-103 Specified in spec.md AC-004; test lands in #361 workspace
- [x] T-104 Specified in spec.md AC-006, AC-007; test lands in #361 workspace
- [x] T-105 No additional boundary tests required — routing fixture and unit tests cover all contract surfaces

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 N/A — no user-facing flow; NFR-A11Y-001 explicitly scoped as N/A in spec.md
- [x] T-A02 N/A — no UI
- [x] T-A03 N/A — no UI
- [x] T-A04 N/A — no UI
- [x] T-A05 N/A — no UI

## Validation and Release Readiness
- [x] T-201 T-201 test suite (`test_design_contracts_c7_extension_fields_issue368.py`) — 22 assertions pass; covers AC-008
- [x] T-202 Attach evidence to traceability.md (T-201 22 assertions green; docs-build/smoke pass recorded)
- [x] T-203 Confirmed no stale TODOs/dead code/drift in design-contracts.md or ADR
- [x] T-204 Run documentation validation (`make docs-build` — pass; `make docs-smoke` — pass)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review` — see below)

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (T-201 pass, docs-build/smoke pass, quality-hooks-run strict pass), and rollback notes
- [x] P-003 PR description updated; references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
<!-- no-impact: all implementation is in #361; this blueprint repo has no new make-target additions -->
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact (no new app scope in this repo)
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — no-impact
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — no-impact
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — no-impact
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — no-impact
