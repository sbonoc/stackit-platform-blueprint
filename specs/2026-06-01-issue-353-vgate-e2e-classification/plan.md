# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - `_check_vgate_classification` is a pure function; no I/O, no state. Single responsibility.
  - Do not introduce abstraction layers beyond what is needed to wire the check into the existing validator pipeline.
- Anti-abstraction gate:
  - Use the same field-parsing pattern already established in `_check_ac_format` (regex line scan). No new base classes or helpers.
- Integration-first testing gate:
  - Write all test cases (T-101..T-112) in RED state before any implementation code is written.
  - Tests use in-memory spec.md text fixtures; no filesystem mocks beyond what the existing test suite uses.
- Positive-path filter/transform test gate:
  - Not applicable — this check is a classification validator, not a filter or payload-transform function.
- Finding-to-test translation gate:
  - Any pre-PR failure found via `make quality-sdd-check` on real specs MUST be translated into a test case; add to T-101..T-112 range.

## Delivery Slices

1. Slice 1 (RED — tests): Write `TestVgateClassification` class in `tests/infra/test_sdd_asset_checker.py` covering all AC-001..AC-009 cases. Write `TestVgateTemplateFields` class in `tests/blueprint/test_quality_gating.py` covering AC-010..AC-012. All tests fail (function not yet implemented).

2. Slice 2 (GREEN — core check): Implement `_check_vgate_classification(spec_text, slug)` in `check_sdd_assets.py`. Add `_VGATE_GATE_SINCE` constant. Wire `_check_vgate_classification` into `_validate_work_item_specs`. Tests T-101..T-109 turn green.

3. Slice 3 (GREEN — templates): Update `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` to seed the three new Implementation Stack Profile fields. Run `sync_consumer_init_sdd_assets.py` to mirror into consumer init template. Tests T-110..T-111 turn green.

4. Slice 4 (GREEN — AGENTS.md): Add mandatory Playwright E2E artifact rule to AGENTS.md testing and quality section. Test T-112 turns green.

5. Slice 5 (VERIFY): Run `make quality-sdd-check` on full catalog; confirm zero new violations. Confirm this work item's own spec passes (has-user-facing-flow: false, E2E gate classification: N/A). Capture evidence.

## Change Strategy
- Migration/rollout sequence: Forward-only guard (`_VGATE_GATE_SINCE`) ensures no pre-existing spec is affected. Spec template update seeds the fields for every new scaffold from this point forward. AGENTS.md update documents the rule for future authors.
- Backward compatibility policy: All pre-gate-date specs are exempt. No backfill required for existing consumer or blueprint specs.
- Rollback plan: Revert the `check_sdd_assets.py` commit; gate behavior is immediately restored to pre-change state. Template changes can be reverted independently without breaking the check.

## Validation Strategy (Shift-Left)
- Unit checks: pytest unit tests (T-101..T-112) covering all AC cases; run via `uv run python3 -m pytest tests/infra/test_sdd_asset_checker.py tests/blueprint/test_quality_gating.py`.
- Contract checks: `make quality-sdd-check` on full spec catalog — confirms no pre-existing spec is broken.
- Integration checks: none required (check is pure Python, no service boundaries).
- E2E checks: none (tooling change, no UI, no runtime components).

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
- Notes: Tooling-only change to `check_sdd_assets.py` and spec templates. No new make targets added; no app delivery workflow targets affected. All listed targets are pre-existing and unaffected by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: AGENTS.md — add mandatory Playwright E2E artifact rule (FR-007).
- Consumer docs updates: none beyond template seeding.
- Mermaid diagrams updated: `architecture.md` contains the V-gate decision tree diagram.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes or filter logic.
- Publish checklist:
  - include requirement/contract coverage (FR-001..FR-008, NFR-001..NFR-005, AC-001..AC-012)
  - include key reviewer files (check_sdd_assets.py, spec templates, AGENTS.md)
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: Metric `sdd_vgate_manual_e2e_violation=<count>` emitted to stderr on violation. No new runtime logging or tracing.
- Alerts/ownership: platform-team owns `check_sdd_assets.py`; no new alert wiring required.
- Runbook updates: AGENTS.md updated with mandatory Playwright E2E artifact rule (the authoritative runbook surface for this check).

## Risks and Mitigations
- Risk 1: `_VGATE_GATE_SINCE` set to the wrong date — pre-existing specs caught retroactively. Mitigation: set `_VGATE_GATE_SINCE` to the actual merge date of this PR; forward-only guard test (AC-006 / T-106) catches regressions.
- Risk 2: Consumer init template mirror drifts from consumer spec template after field addition. Mitigation: Slice 3 explicitly runs `sync_consumer_init_sdd_assets.py`; existing sync test coverage will catch drift.
