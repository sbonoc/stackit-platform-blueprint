# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1 (RED)

- [ ] T-001 Add `test_triage_blueprint_managed_source_exists_true_yields_take_source` to `tests/blueprint/test_upgrade_consumer.py` — assert a `blueprint-managed` conflict with `source_exists=True` produces `recommended_action: take_source` and `source_exists: true` in the triage entry
- [ ] T-002 Add `test_triage_blueprint_managed_source_exists_false_yields_human_required` — assert `source_exists=False` on a `blueprint-managed` entry produces `recommended_action: human_required`
- [ ] T-003 Add `test_triage_entry_includes_source_exists_field` — assert all conflict entries in `upgrade_triage.json` carry a `source_exists` boolean field
- [ ] T-004 Run `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -k "source_exists" -v` — confirm RED

## Implementation — Slice 2 (GREEN)

- [ ] T-005 In `scripts/lib/blueprint/upgrade_consumer.py`: extend `_recommended_action(ownership_class, source_exists)` to accept `source_exists: bool`; add inference: `if ownership_class == "blueprint-managed" and source_exists: return "take_source"`
- [ ] T-006 In `_write_upgrade_triage()`: extract `source_exists` from `entry.source_exists if entry else False`; pass to `_recommended_action`; add `"source_exists": source_exists` to each triage entry dict; set `reason` to inference note for promoted entries
- [ ] T-007 In `scripts/lib/blueprint/schemas/upgrade_triage.schema.json`: add `"source_exists": {"type": "boolean"}` as an optional (non-required) property on the conflict entry object
- [ ] T-008 Run `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -k "source_exists" -v` — confirm GREEN
- [ ] T-009 Run `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -v` — confirm full suite GREEN
- [ ] T-010 Verify schema validation passes for both old triage files (without `source_exists`) and new (with it): `make infra-contract-test-fast`

## Accessibility Testing (Normative — N/A)
- [x] T-A01 N/A — upgrade engine tooling only; no UI components (NFR-A11Y-001)
- [x] T-A02 N/A
- [x] T-A03 N/A
- [x] T-A04 N/A
- [x] T-A05 N/A

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast` — confirm zero violations
- [ ] T-202 Run `make infra-validate` — confirm no contract violations
- [ ] T-203 Run `uv run python3 -m pytest tests/blueprint/ -v` — confirm full blueprint test suite GREEN
- [ ] T-204 Run `make docs-build` and `make docs-smoke` — confirm no docs build failures
- [ ] T-205 Run `make quality-hardening-review` — complete hardening review

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A: no app delivery workflow scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A: no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A: no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A: no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A: no-impact
