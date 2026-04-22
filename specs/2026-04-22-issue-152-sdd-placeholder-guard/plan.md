# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Single new validation loop in `check_sdd_assets.py`; config-driven via `contract.yaml` to avoid hard-coding fields.
- Anti-abstraction gate:
  - Reuses existing `_parse_bullet_kv` helper; no new helper or class needed.
- Integration-first testing gate:
  - Three contract tests cover the three acceptance criteria scenarios (fail when ready, pass for "none", pass when not ready).
- Positive-path filter/transform test gate:
  - N/A: no filter or payload-transform logic.
- Finding-to-test translation gate:
  - The gap discovered in PR #151 (placeholders shipped with SPEC_READY=true) is covered by `test_empty_context_pack_required_field_fails_when_spec_ready`.

## Delivery Slices
1. Slice 1 — Contract config: add `work_item_document_required_fields` to `blueprint/contract.yaml` and its bootstrap template copy.
2. Slice 2 — Validator: add parsing of the new config key and the per-field guard loop in `check_sdd_assets.py`; add three tests in `SddPlaceholderGuardTests`.

## Change Strategy
- Migration/rollout sequence: Both slices ship together in one PR. The guard is gated on `spec_ready=True`, so all in-progress work items (SPEC_READY=false) are unaffected.
- Backward compatibility policy: Existing SPEC_READY=true work items must have non-empty required fields. The only historical gap was `specs/2026-04-22-issue-104-106-107-upgrade-additive-file-helper-gaps/context_pack.md`, which was fixed in this PR.
- Rollback plan: Remove `work_item_document_required_fields` from `blueprint/contract.yaml` and its bootstrap template copy.

## Validation Strategy (Shift-Left)
- Unit checks: `SddPlaceholderGuardTests` (3 tests) in `tests/infra/test_tooling_contracts.py`.
- Contract checks: `make infra-contract-test-fast` (97 tests pass).
- Integration checks: `make quality-hooks-fast` passes end-to-end.
- E2E checks: N/A (no HTTP routes or runtime changes).

## App Onboarding Contract (Normative)
- Required minimum make targets (all unaffected by this work item):
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
- Notes: no app delivery scope affected; all targets above remain functional

## Documentation Plan (Document Phase)
- Blueprint docs updates: none (ADR created at `docs/blueprint/architecture/decisions/ADR-20260422-issue-152-sdd-placeholder-guard.md`).
- Consumer docs updates: none.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: none; read-only validation.
- Alerts/ownership: none.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1: retroactively catches SPEC_READY=true work items with empty required fields -> mitigation: audited all existing work items; fixed the one remaining gap (`issue-104-106-107` context_pack.md).
