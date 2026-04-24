# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: change is a single `if` block (~8 lines) in one shell script. No new abstractions, no new files in the runtime path.
- Anti-abstraction gate: direct use of `cp -r` and `mkdir -p`; no wrapper layer introduced.
- Integration-first testing gate: two new integration tests added (Slice 1, red) before the fix (Slice 2, green) — tests exercise the shell wrapper end-to-end via subprocess and git.
- Positive-path filter/transform test gate: not applicable — no filter/transform logic.
- Finding-to-test translation gate: the reproduction path from GH issue #182 (`make blueprint-upgrade-consumer-apply` → `make blueprint-upgrade-fresh-env-gate` → FAIL) is translated into `test_gate_passes_when_artifacts_present_and_seeded` which must fail red before Slice 2 and green after.

## Delivery Slices
1. Slice 1 — Failing tests (red): add two integration test cases to `tests/blueprint/test_upgrade_fresh_env_gate.py`. Run suite to confirm both new tests FAIL.
2. Slice 2 — Implementation (green): add artifact-seeding block to `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` after `worktree_created=true`. Run suite to confirm all tests PASS.
3. Slice 3 — Docs: update `docs/blueprint/architecture/execution_model.md` to document the seeding step. Run `make quality-docs-check-changed`.

## Change Strategy
- Migration/rollout sequence: blueprint fix shipped → consumers receive it on next `make blueprint-upgrade-consumer` run.
- Backward compatibility policy: fully backward compatible. When `artifacts/blueprint/` is absent the gate behaviour is identical to pre-fix (the seeding step is a no-op).
- Rollback plan: remove the seeding `if` block from `upgrade_fresh_env_gate.sh`. No state, database, or external API to revert.

## Validation Strategy (Shift-Left)
- Unit checks: not applicable — no pure functions added.
- Contract checks: `make quality-hooks-fast` (includes SDD check, docs-check-changed).
- Integration checks: `python3 -m pytest tests/blueprint/test_upgrade_fresh_env_gate.py -v` — covers both new cases and all existing cases.
- E2E checks: `make test-smoke-all-local` — not required for this change (no HTTP route, no infra config changed); scope is tooling-only shell script.

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
- App onboarding impact: no-impact — tooling-only change; no app onboarding surface modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/execution_model.md` — add seeding step to fresh-env gate description.
- Consumer docs updates: none.
- Mermaid diagrams updated: none — the gate flow diagram change is prose-only.
- Docs validation commands:
  - `make quality-docs-check-changed`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not required — no HTTP route, query, filter, or new endpoint in scope.
- Publish checklist:
  - include REQ-001 through REQ-008 coverage
  - include AC-001 through AC-005 coverage
  - include test evidence (pytest output)
  - include rollback note

## Operational Readiness
- Logging/metrics/traces: `log_info` on seed and on skip (REQ-003, REQ-004). Existing `blueprint_upgrade_fresh_env_gate_status_total` metric unchanged.
- Alerts/ownership: no changes.
- Runbook updates: none required — the gate log output is self-describing.

## Risks and Mitigations
- Risk 1: `cp -r` fails if the worktree `artifacts/` parent directory cannot be created (e.g. permissions). Mitigation: `set -euo pipefail` causes the script to exit non-zero immediately, which is the correct failure behavior; the EXIT trap cleans up.
