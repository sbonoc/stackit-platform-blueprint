# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Four lines of code added to `upgrade_consumer.py`; no new modules, no new abstractions beyond a single pure predicate.
- Anti-abstraction gate: Predicate is a standalone function, not a class or config object. No wrapper layers.
- Integration-first testing gate: Unit tests define the classification boundary before implementation; tests cover the predicate and the `_classify_entries()` integration path.
- Positive-path filter/transform test gate: AC-001 verified by positive-path test — consumer manifest absent in source → skip entry emitted (not delete). Filter/classify operation directly tested.
- Finding-to-test translation gate: Consumer finding (manifests deleted under `allow_delete=True`) translated into `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` before fix applied.

## Delivery Slices

### Slice 1 — Predicate and guard implementation
1. Add `_is_consumer_owned_workload(relative_path: str) -> bool` after `_entry_looks_like_dir()` in `upgrade_consumer.py`.
2. Add guard block in `_classify_entries()` before the `not source_exists and target_exists` branch.
3. Add inline comment referencing issue #203 for future unification.

### Slice 2 — Test coverage
1. Add unit tests to `tests/blueprint/test_upgrade_consumer.py`:
   - `test_is_consumer_owned_workload_returns_true_for_consumer_manifest`
   - `test_is_consumer_owned_workload_returns_false_for_kustomization`
   - `test_is_consumer_owned_workload_returns_false_for_unrelated_path`
   - `test_consumer_workload_manifests_not_deleted_when_allow_delete_true`
   - `test_kustomization_yaml_in_base_apps_is_not_protected`

### Slice 3 — Quality validation
1. `make quality-hooks-fast`
2. `make quality-sdd-check SPEC_SLUG=2026-04-26-issue-207-apps-prune-exclusion`
3. `make quality-hardening-review`
4. Full test suite: `make test-unit-all`

### Slice 4 — Documentation and publish
1. Write ADR: `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-207-apps-prune-exclusion.md`
2. Populate publish artifacts: `pr_context.md`, `hardening_review.md`
3. Commit and push; create PR.

## Change Strategy
- Migration/rollout sequence: Single commit on feature branch; merge to main via PR.
- Backward compatibility policy: Fully backward-compatible. The new skip class only fires for paths that previously would have been deleted. Paths that would have been skipped (allow_delete=false) continue to be skipped with the existing "deletion skipped" reason. No consumer action required.
- Rollback plan: Revert the four-line guard block and remove the predicate function. No data migration needed.

## Validation Strategy (Shift-Left)
- Unit checks: Predicate tests + `_classify_entries()` integration test with mock filesystem via `tmp_path`.
- Contract checks: `make quality-sdd-check` — verifies spec, plan, tasks, and traceability artifacts are complete and consistent.
- Integration checks: Full test suite (`make test-unit-all`); test pyramid contract check.
- E2E checks: Not applicable — no HTTP endpoints or provisioning pipeline changes.

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
- Notes: Change is internal to the upgrade planner classification loop. No app bootstrap, smoke, or test lane targets are affected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR only.
- Consumer docs updates: none — behavior change is transparent to consumers (files are no longer deleted instead of being silently destroyed).
- Mermaid diagrams updated: architecture.md diagram in this spec.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable — no HTTP routes or filter/payload-transform logic changed.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: No changes. Skip entries are already emitted to plan output.
- Alerts/ownership: No alerts changed.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1 → mitigation: Blueprint adds a real managed manifest under `base/apps/` (non-kustomization) in a future release — it would be silently skipped by consumer upgrades. Mitigation: document this in ADR; issue #206 delivers the correct long-term mechanism. The comment in code points to #203/#206 for future unification.
