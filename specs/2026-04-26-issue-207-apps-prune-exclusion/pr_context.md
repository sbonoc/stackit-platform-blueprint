# PR Context

## Summary
- Work item: 2026-04-26-issue-207-apps-prune-exclusion
- Objective: Prevent the blueprint upgrade planner from deleting consumer workload manifests in `infra/gitops/platform/base/apps/` when `BLUEPRINT_UPGRADE_ALLOW_DELETE=true`.
- Scope boundaries: `upgrade_consumer.py` — `_classify_entries()` guard + `_is_consumer_owned_workload()` predicate. No contract schema changes. No changes to kustomization.yaml management.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005
- Contract surfaces changed: none (no config, API, OpenAPI, event, Make, or docs contract changes)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_is_consumer_owned_workload()` (new) and guard block in `_classify_entries()`
  - `tests/blueprint/test_upgrade_consumer.py` — `ConsumerOwnedWorkloadPruneTests` class (6 new tests)
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer.py` — classification logic is central to the upgrade pipeline; the guard is additive and does not alter any existing branch

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make quality-sdd-check SPEC_SLUG=2026-04-26-issue-207-apps-prune-exclusion`, `make quality-hardening-review`, `make test-unit-all`, `make docs-build`, `make docs-smoke`
- Result summary: all passed; 6 new tests green; no pre-existing test regressions; SDD check clean
- Artifact references: `specs/2026-04-26-issue-207-apps-prune-exclusion/` (full SDD artifact set)

## Risk and Rollback
- Main risks: If blueprint adds a non-kustomization managed manifest under `base/apps/` in a future release, that file will be silently skipped during consumer upgrades. Documented in ADR with reference to issue #206 for general resolution.
- Rollback strategy: Revert the guard block (approx. 15 lines) and remove `_is_consumer_owned_workload()`. No data migration, no schema change, no consumer action required.

## Deferred Proposals
- none
