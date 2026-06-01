# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes applicable `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — RED: write failing tests
- [ ] T-001 Write `TestVgateClassification` test class in `tests/infra/test_sdd_asset_checker.py` covering T-101..T-109 (all failing)
- [ ] T-002 Write `TestVgateTemplateFields` test class in `tests/blueprint/test_quality_gating.py` covering T-110..T-112 (all failing)

### Slice 2 — GREEN: core check implementation
- [ ] T-003 Add `_VGATE_GATE_SINCE` constant to `check_sdd_assets.py`
- [ ] T-004 Implement `_check_vgate_classification(spec_text, slug)` pure function in `check_sdd_assets.py`
- [ ] T-005 Wire `_check_vgate_classification` into `_validate_work_item_specs`; emit `sdd_vgate_manual_e2e_violation` metric to stderr on violation

### Slice 3 — GREEN: template seeding
- [ ] T-006 Update `.spec-kit/templates/blueprint/spec.md` Implementation Stack Profile to seed `has-user-facing-flow`, `E2E gate classification`, and `E2E automation target` fields
- [ ] T-007 Update `.spec-kit/templates/consumer/spec.md` Implementation Stack Profile to seed the same three fields
- [ ] T-008 Run `uv run python3 scripts/bin/sdd/sync_consumer_init_sdd_assets.py` to mirror consumer template into init tmpl

### Slice 4 — GREEN: AGENTS.md rule
- [ ] T-009 Add mandatory Playwright E2E artifact rule to AGENTS.md testing and quality section, keyed on `has-user-facing-flow: true` (FR-007)

### Slice 5 — VERIFY
- [ ] T-010 Run `uv run python3 -m pytest tests/infra/test_sdd_asset_checker.py tests/blueprint/test_quality_gating.py -v`; confirm all T-101..T-112 pass
- [ ] T-011 Run `make quality-sdd-check`; confirm zero new violations on full catalog
- [ ] T-012 Capture test output and `quality-sdd-check` result as evidence in `traceability.md`

## Test Automation (AC coverage)
- [ ] T-101 AC-001 — V-gate check rejects `manual` when `has-user-facing-flow: true` + playwright profile
- [ ] T-102 AC-002 — V-gate check passes for `automated` when `has-user-facing-flow: true` + playwright profile
- [ ] T-103 AC-003 — V-gate check passes for `manual-with-target` + valid `E2E automation target`
- [ ] T-104 AC-004 — V-gate check rejects `manual-with-target` with absent/`none` `E2E automation target`
- [ ] T-105 AC-005 — V-gate check rejects `manual-with-target` with malformed `E2E automation target`
- [ ] T-106 AC-006 — pre-gate slugs (date < `_VGATE_GATE_SINCE`) are exempt
- [ ] T-107 AC-007 — non-playwright profiles are exempt regardless of `has-user-facing-flow`
- [ ] T-108 AC-008 — `has-user-facing-flow: false` is exempt regardless of `E2E gate classification`
- [ ] T-109 AC-009 — metric `sdd_vgate_manual_e2e_violation` appears in stderr on violation
- [ ] T-110 AC-010 — blueprint spec template seeds all three new fields
- [ ] T-111 AC-011 — consumer spec template seeds all three new fields
- [ ] T-112 AC-012 — `AGENTS.md` contains `has-user-facing-flow` in testing section

## Accessibility Testing
- [ ] T-A01 NFR-A11Y-001: N/A — no UI introduced by this work item

## Validation and Release Readiness
- [ ] T-201 Run `uv run python3 -m pytest tests/` and confirm full suite passes
- [ ] T-202 Attach evidence to `traceability.md`
- [ ] T-203 Confirm no stale TODOs / dead code / drift in `check_sdd_assets.py`
- [ ] T-204 Run `make docs-build` and `make docs-smoke`
- [ ] T-205 Run `make quality-hardening-review`

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
<!-- App onboarding impact: no-impact per plan.md. Literal make-target tokens preserved
     below so the SDD asset checker recognizes the section; no new make-target wiring is
     produced by this work item. -->
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact)
