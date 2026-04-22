# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: checker is minimal — pure functions, no ORM, no class hierarchy, just dataclasses and plain functions.
- Anti-abstraction gate: no wrapper layers; `run_cmd python3 version_contract_checker.py` is the only integration point.
- Integration-first testing gate: 22 unit tests written before shell integration.
- Positive-path filter/transform test gate: `test_all_vars_match_returns_all_passed` and `test_consistent_lock_and_manifest_returns_all_passed` provide positive-path coverage.
- Finding-to-test translation gate: `test_catalog_check_mode_exits_nonzero_when_lock_stale` and `test_consistency_mode_exits_nonzero_when_stale_lock` encode the pre-PR deterministic finding as automated tests.

## Delivery Slices
1. Slice 1 — Python core + tests: `scripts/lib/platform/apps/version_contract_checker.py` + `tests/infra/test_version_contract_checker.py` (22 tests).
2. Slice 2 — Shell integration: extend `audit_versions.sh` (catalog-check), `audit_versions_cached.sh` (fingerprint), `smoke.sh` (consistency); update `test_pyramid_contract.json`.

## Change Strategy
- Migration/rollout sequence: additive — existing behavior unchanged; new checks only activate when catalog files exist.
- Backward compatibility policy: fully backward-compatible; `APP_CATALOG_SCAFFOLD_ENABLED=false` repos skip all new checks.
- Rollback plan: revert the commit; no persistent state introduced.

## Validation Strategy (Shift-Left)
- Unit checks: `python3 -m pytest tests/infra/test_version_contract_checker.py -v` — 22 tests.
- Contract checks: no contract surfaces changed (no new make targets, no new env vars).
- Integration checks: `make quality-hooks-fast` exercises the full fast-lane gate.
- E2E checks: not applicable (no cluster state changed).

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
- App onboarding impact: impacted — `apps-smoke` behavior extended for catalog-enabled repos.
- Notes: the consistency check is additive; repos with catalog disabled are not affected. Backend, frontend, and aggregate test lanes are unaffected (blueprint governance tooling only).

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260423-issue-56-app-version-contract-checks.md`.
- Consumer docs updates: none — no consumer-facing contract changes.
- Mermaid diagrams updated: ADR diagram only.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP route/filter changes).
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `apps_version_contract_check_total` metric; `contract_checks` + `contract_failures` in summary metric.
- Alerts/ownership: no new alerts; existing drift alert thresholds cover the new failure mode.
- Runbook updates: none required; `--help` on `version_contract_checker.py` documents modes.

## Risks and Mitigations
- Risk 1 (text-match manifest fragility) → mitigation: manifest is machine-generated from a fixed template; format changes require a separate template change that would also require a checker update.
