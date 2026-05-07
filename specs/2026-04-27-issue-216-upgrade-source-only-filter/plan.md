# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: one new function, two new dataclass fields, one test fixture — minimal scope.
- Anti-abstraction gate: use direct `Path.exists()` calls; do not introduce a new path-resolution utility.
- Integration-first testing gate: write the failing regression test (fixture consumer with `specs/` + source contract containing `specs` in `source_only`) before implementing `_filter_source_only`.
- Positive-path filter/transform test gate: AC-003 and AC-005 are positive-path — a consumer-added entry IS preserved (carry-forward); a consumer with no conflicts IS unchanged.
- Finding-to-test translation gate: the reproduction command from issue #216 is deterministic; translate it into a pytest fixture before coding the fix.

## Delivery Slices

### Slice 1 (red) — Failing regression tests
- Write `test_resolve_contract_conflict_source_only_phase1_drop`: fixture consumer with `specs/` populated and source contract with `specs` in `source_only`; assert resolved `source_only` still contains `specs` before fix (reproduces #216, AC-001).
- Write `test_resolve_contract_conflict_source_only_phase2_carry_forward`: fixture consumer with a consumer-added `source_only` entry; assert it is dropped after Stage 3 before fix (AC-003).
- Confirm all new tests fail before fix.

### Slice 2 (green) — Implementation
1. Add `_filter_source_only(source_list, consumer_list, repo_root)` to `resolve_contract_upgrade.py` implementing Phase 1 (drop source entries existing on disk) and Phase 2 (carry forward consumer additions existing on disk).
2. Extend `ContractResolveResult` with `dropped_source_only` and `kept_consumer_source_only` fields.
3. Wire `_filter_source_only` into `resolve_contract_conflict` after FR-007 prune-globs step.
4. Extend `decisions` dict and pipeline stdout logging to include `dropped_source_only` and `kept_consumer_source_only`.
5. Confirm regression tests pass green.

### Slice 3 — Quality and docs
- Run `make quality-sdd-check`, `make quality-hooks-run`, `make infra-validate`.
- No docs changes required (internal tooling fix; no consumer-facing contract change).

## Change Strategy
- Migration/rollout sequence: no consumer migration needed; fix is transparent (corrects silent overwrite behavior).
- Backward compatibility policy: consumers with no consumer-added `source_only` entries and no on-disk conflicts produce an identical result to current behavior for those entries (AC-005).
- Rollback plan: revert the PR; consumers re-apply their manual post-edit workaround.

## Validation Strategy (Shift-Left)
- Unit checks: pytest fixtures for Phase 1 (drop), Phase 2 (carry-forward), backward-compat (no conflict).
- Contract checks: fixture-level `infra-validate` check on the resolved contract (AC-004).
- Integration checks: none required (function-level fixture is sufficient).
- E2E checks: `make blueprint-template-smoke` to confirm no smoke regression.

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
- App onboarding impact: no-impact — changes are confined to Python Stage 3 resolver script with no effect on app delivery Make targets or runtime infrastructure.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none required (internal tooling fix; Stage 3 behavior corrected to match documented FR-009 semantics).
- Consumer docs updates: none.
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP routes or API endpoints.
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-005, AC-001–AC-005)
  - include key reviewer files (`scripts/lib/blueprint/resolve_contract_upgrade.py`, test files)
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: Stage 3 stdout extended with `dropped_source_only` and `kept_consumer_source_only` counts.
- Alerts/ownership: none (CLI tooling).
- Runbook updates: none.

## Risks and Mitigations
- Risk 1: Phase 1 silently drops intentional on-disk `source_only` entries. Mitigation: decision log records all drops; matches v1.7.0 behavior; consumer can verify via the decisions JSON artifact.
