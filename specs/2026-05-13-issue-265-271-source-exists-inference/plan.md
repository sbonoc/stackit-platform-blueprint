# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two files change — `upgrade_consumer.py` (2 functions) and `upgrade_triage.schema.json` (1 optional property). No new modules, no new abstractions.
- Anti-abstraction gate: `_recommended_action` receives `source_exists: bool` as a plain parameter. No strategy pattern, no config object.
- Integration-first testing gate: Triage output tests drive the RED phase before any production code is touched.
- Positive-path filter/transform test gate: `blueprint-managed + source_exists=True → take_source` is the positive path. `test_triage_entry_includes_source_exists_field` asserts that a matching entry produces `recommended_action: take_source` and `source_exists: true` in the output JSON.
- Finding-to-test translation gate: No pre-PR smoke findings. Change is pure Python + schema; no deterministic pre-PR failures discovered.

## Delivery Slices

1. Slice 1 (RED — failing tests):
   - Add `test_triage_blueprint_managed_source_exists_true_yields_take_source` to `tests/blueprint/test_upgrade_consumer.py` — drives `blueprint-managed` + `source_exists=True` → `take_source` and `source_exists: true` in entry.
   - Add `test_triage_blueprint_managed_source_exists_false_yields_human_required` — drives `source_exists: false` → `human_required`.
   - Add `test_triage_entry_includes_source_exists_field` — drives presence of `source_exists` field on each conflict entry regardless of ownership class.
   - Run: `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -k "source_exists" -v` — expect RED.

2. Slice 2 (GREEN — implementation):
   - In `scripts/lib/blueprint/upgrade_consumer.py`:
     - Add `source_exists: bool` parameter to `_recommended_action(ownership_class, source_exists)`.
     - Inside: if `ownership_class == "blueprint-managed" and source_exists`, return `"take_source"`.
     - In `_write_upgrade_triage()`: extract `source_exists` from `entry.source_exists if entry else False`; pass to `_recommended_action`; add `"source_exists": source_exists` to each triage entry dict.
   - In `scripts/lib/blueprint/schemas/upgrade_triage.schema.json`:
     - Add `"source_exists": {"type": "boolean"}` as an optional property inside the conflict entry object (not in `required`).
   - Run tests: `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -k "source_exists" -v` — expect GREEN.
   - Run full suite: `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -v` — expect GREEN.

## Change Strategy
- Migration/rollout sequence: single-file change; no migration needed.
- Backward compatibility policy: `source_exists` is added as optional to the schema (not required); existing triage files without the field remain valid. Running `blueprint-upgrade-consumer-resolve` on old triage files is unaffected — the resolver reads `recommended_action`, which remains the authoritative dispatch field.
- Rollback plan: revert the two-file change; `_recommended_action` reverts to single-parameter form; `source_exists` is removed from schema. No persisted state to roll back.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -v`
- Contract checks: `make infra-contract-test-fast` — verify schema validation still passes for both old and new triage files.
- Integration checks: `make infra-validate` — contract.yaml unchanged; no impact expected.
- E2E checks: N/A — upgrade engine tooling only; no HTTP route scope.

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
- Notes: Upgrade engine tooling change only; no app delivery workflow scope. All listed targets are pre-existing and unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR already drafted (`docs/blueprint/architecture/decisions/ADR-issue-265-271-source-exists-inference.md`); no further narrative docs required.
- Consumer docs updates: none — the change is transparent to consumers (auto-resolution improves; no new CLI flags or behavioral opt-in required).
- Mermaid diagrams updated: architecture.md flowchart already reflects the post-change flow.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route or filter logic.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: N/A — upgrade engine tooling only; no runtime observability surface.
- Alerts/ownership: N/A
- Runbook updates: N/A

## Risks and Mitigations
- Risk 1: a consumer who creates a file under a `blueprint_managed_roots` path that coincidentally matches a blueprint source file will have it auto-overwritten → mitigation: this is the existing `blueprint_managed_roots` exclusivity contract; no new risk surface; documented in ADR Consequences.
