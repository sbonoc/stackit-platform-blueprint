# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: two one-line changes in two bash scripts; no new helpers or abstractions.
- Anti-abstraction gate: reuses existing `record_reconcile_issue` and `log_info` helpers.
- Integration-first testing gate: structural contract tests verify the fix intent; no live-cluster tests required.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: issue #105 (abort before state file) and #110 (ambiguous gho_ warning) translated into `RuntimeAuthBestEffortTests` structural assertions.

## Delivery Slices
1. Slice 1 — ESO kustomize guard: wrap `run_kustomize_apply` in `if !` in `reconcile_eso_runtime_secrets.sh`; add `test_eso_kustomize_apply_is_guarded`.
2. Slice 2 — gho_ token policy: replace `record_reconcile_issue` with `log_info` for `gho_` in `reconcile_argocd_repo_credentials.sh`; add `test_argocd_repo_credentials_accepts_gho_token`.

## Change Strategy
- Migration/rollout sequence: both slices ship in one PR; no migration needed.
- Backward compatibility policy: dry-run mode unaffected; required=true failure path preserved by FR-003.
- Rollback plan: revert the two one-line changes in the two scripts.

## Validation Strategy (Shift-Left)
- Unit checks: `RuntimeAuthBestEffortTests` (2 tests) in `tests/infra/test_tooling_contracts.py`.
- Contract checks: `make infra-contract-test-fast` (99 tests pass).
- Integration checks: `make quality-hooks-fast` passes end-to-end.
- E2E checks: N/A (live cluster not available in CI).

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
- Notes: no app delivery scope affected; all targets above remain functional.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-105-110-runtime-auth-best-effort-fix.md`; `AGENTS.decisions.md`.
- Consumer docs updates: none.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `log_info` added for `gho_` acceptance; `record_reconcile_issue` added for kustomize apply failure.
- Alerts/ownership: none.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1: accepting `gho_` tokens means ArgoCD can lose repo access on token expiry -> mitigation: default `ARGOCD_REPO_CREDENTIALS_REQUIRED=false`; INFO log guides operators to PATs.
- Risk 2: the `if !` guard in best-effort mode silently captures kustomize apply failures -> mitigation: `record_reconcile_issue` captures the failure in the state file; operators can inspect artifacts.
