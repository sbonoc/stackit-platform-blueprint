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
- [ ] T-003 Extend verdict merger return value to include `merger_overhead` dict (`findings_before_dedup`, `findings_after_dedup`, `severity_escalation_events`)
- [ ] T-004 Accumulate per-expert token counts from LiteLLM `usage` block; write sentinel `-1` on missing usage; add to C7 envelope as `outcome_details.token_usage`
- [ ] T-005 Add `outcome_details.merger_overhead` to C7 envelope construction on all panel-dispatched phases
- [ ] T-006 Widen `outcome_details.routing_keys` population to all panel-dispatched phases (not only `agent-pr-review`)
- [ ] T-007 Add per-ticket token accumulator to orchestrator; emit `outcome_details.ticket_token_summary` on step08 close-out event

### Slice 3 — `audit-cost` CLI sub-command
- [ ] T-008 Add `audit-cost --ticket <id>` sub-command to `scripts/bin/sdd/c7_emit.py`
- [ ] T-009 Pin per-ticket cost ceiling as a named Python constant with calibration comment; implement ceiling-check logic (exit 1 on breach, emit `rejection_reason: cost-ceiling-exceeded`)

### Slice 4 — Step02 routing fixture
- [ ] T-010 Write `tests/blueprint/orchestrator/test_step02_routing_fixture.py` under #361's test tree with ≥ 25 parametrized `(question_text, expected_expert_set)` rows across 5 question-shape categories
- [ ] T-011 Expose `EMBEDDING_UPGRADE_THRESHOLD = 0.20` constant and module-level docstring describing the embedding-upgrade unblock trigger
- [ ] T-012 Add summary assertion: `fraction_failing < EMBEDDING_UPGRADE_THRESHOLD`

## Test Automation
- [ ] T-101 Unit test: simulated panel-dispatched C7 event contains `outcome_details.token_usage` (per-expert, ≥ 0 or -1 sentinel) + `outcome_details.merger_overhead` fields + passes C7 schema validation; covers AC-001, AC-002, AC-005
- [ ] T-102 Unit test: step08 roll-up `ticket_token_summary.total_input_tokens` equals arithmetic sum of per-expert input_tokens (excluding -1) across all phases for a test ticket_id; covers AC-003
- [ ] T-103 Unit test: `c7_emit.py audit-cost` exits 1 + emits `rejection_reason: cost-ceiling-exceeded` for over-budget synthetic ticket; exits 0 for in-budget ticket; covers AC-004
- [ ] T-104 Routing fixture: `uv run python3 -m pytest tests/blueprint/orchestrator/test_step02_routing_fixture.py` exits 0 with ≥ 25 rows collected, zero failures; EMBEDDING_UPGRADE_THRESHOLD == 0.20; docstring contains "embedding-match"; covers AC-006, AC-007
- [ ] T-105 No additional boundary tests required — routing fixture and unit tests cover all contract surfaces

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 N/A — no user-facing flow; NFR-A11Y-001 explicitly scoped as N/A in spec.md
- [x] T-A02 N/A — no UI
- [x] T-A03 N/A — no UI
- [x] T-A04 N/A — no UI
- [x] T-A05 N/A — no UI

## Validation and Release Readiness
- [x] T-201 T-201 test suite (`test_design_contracts_c7_extension_fields_issue368.py`) — 22 assertions pass; covers AC-008
- [ ] T-202 Attach evidence to traceability.md (test run outputs for T-101–T-104)
- [ ] T-203 Confirm no stale TODOs/dead code/drift in design-contracts.md or ADR
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (T-101–T-104 pass, T-201 pass), and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
<!-- no-impact: all implementation is in #361; this blueprint repo has no new make-target additions -->
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact (no new app scope in this repo)
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — no-impact
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — no-impact
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — no-impact
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — no-impact
