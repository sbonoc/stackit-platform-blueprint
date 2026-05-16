# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Minimal additive changes only — new TF module files, new shell helpers, additive state keys. No refactoring of existing scripts or routing.
- Anti-abstraction gate: No new wrapper layers. Shell helpers follow the existing `secrets_manager_*()` naming convention already in `secrets_manager.sh`. TF module mirrors foundation pattern directly.
- Integration-first testing gate: `test_contract.py` written in the red phase with ≥ 10 assertions before the shell/TF implementation is complete.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic. Contract tests cover state key existence and value correctness.
- Finding-to-test translation gate: N/A — no pre-PR smoke failures requiring test translation; module is a new capability, not a bug fix.

## Delivery Slices

### Slice 1 — Terraform standalone module (red → green)
1. Write failing `test_contract.py` assertions for TF module structure (AC-001–AC-004).
2. Write `main.tf`, `variables.tf`, `outputs.tf` → turn assertions green.

### Slice 2 — Shell layer and contract (red → green)
1. Write failing `test_contract.py` assertions for contract outputs, namespace/auth helpers, reconcile secret, apply/plan/smoke state keys, and security invariant (AC-005–AC-013).
2. Update `module.contract.yaml`, `secrets_manager.sh` (add `secrets_manager_namespace`, `secrets_manager_auth_method_details`, `secrets_manager_reconcile_runtime_secret`), `secrets_manager_apply.sh`, `secrets_manager_plan.sh`, `secrets_manager_smoke.sh` → turn assertions green.
3. Update `tests/infra/test_optional_modules.py` to assert `namespace` and `auth_method_details` in runtime state (additive).

## Change Strategy
- Migration/rollout sequence: All changes are additive. No existing state file keys are renamed. No existing script behaviour is altered. New state keys appear on next `infra-provision MODULE=secrets-manager` run.
- Backward compatibility policy: Fully additive — existing consumers that do not read `namespace` or `auth_method_details` are unaffected.
- Rollback plan: Revert the three script changes and the contract.yaml addition. Destroy the provisioned STACKIT instance via `foundation_reconcile_apply` driver.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run pytest tests/infra/modules/secrets-manager/test_contract.py -v` — ≥ 10 assertions, all green.
- Contract checks: `uv run pytest tests/infra/test_optional_modules.py -v -k secrets_manager` — updated assertions for namespace/auth_method_details.
- Integration checks: `make infra-provision MODULE=secrets-manager` on STACKIT lane (manual, CI-gated) — state file present with all required keys; smoke exits 0.
- E2E checks: N/A — no runtime service changes.

## App Onboarding Contract (Normative)
- App onboarding impact: no-impact
- Notes: Tooling/infrastructure-only change — no app delivery workflow impact.
- Required minimum make targets (all N/A — tooling-only scope):
  - `apps-bootstrap` — N/A
  - `apps-smoke` — N/A
  - `backend-test-unit` — N/A
  - `backend-test-integration` — N/A
  - `backend-test-contracts` — N/A
  - `backend-test-e2e` — N/A
  - `touchpoints-test-unit` — N/A
  - `touchpoints-test-integration` — N/A
  - `touchpoints-test-contracts` — N/A
  - `touchpoints-test-e2e` — N/A
  - `test-unit-all` — N/A
  - `test-integration-all` — N/A
  - `test-contracts-all` — N/A
  - `test-e2e-all-local` — N/A
  - `infra-port-forward-start` — N/A
  - `infra-port-forward-stop` — N/A
  - `infra-port-forward-cleanup` — N/A

## Documentation Plan (Document Phase)
- Blueprint docs updates: Module documentation for secrets-manager updated to reflect new outputs (`SECRETS_MANAGER_NAMESPACE`, `SECRETS_MANAGER_AUTH_METHOD_DETAILS`) and `blueprint-secrets-manager-auth` K8s Secret.
- Consumer docs updates: N/A — consumer-side ESO SecretStore configuration is out of scope.
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route or filter changes.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes
  - reference "Part of #248" (NOT "Closes #248")

## Operational Readiness
- Logging/metrics/traces: All script output prefixed with `[secrets-manager]`. No metrics/tracing changes (tooling-only).
- Alerts/ownership: N/A — no runtime service.
- Runbook updates: N/A — smoke check serves as operational gate.

## Risks and Mitigations
- Risk 1: Foundation Terraform already manages a `stackit_secretsmanager_instance` — standalone module introduces a second provisioning path → Mitigated by keeping the two independent (foundation never calls standalone module).
- Risk 2: Password inadvertently logged in apply script → Mitigated by `NFR-SEC-001` enforcement via `test_contract.py` assertion (AC-012) and code review.
