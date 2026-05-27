# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Delivery Slices (TDD red→green order)

1. Slice 1: Faro receiver — shell lib + contract + state + smoke (FR-001, FR-002, FR-006, FR-007, FR-008).
   - Owner: bonos
   - Depends on: none (can start immediately after SPEC_READY)
   - Validation: write failing tests for `observability_faro_endpoint` and `FARO_ENDPOINT` contract output; add helper and init_env export; update apply/smoke; run tests green.

2. Slice 2: OTEL pipeline improvements — values files + ArgoCD inline values (FR-003, FR-004, FR-005, FR-009, FR-010, FR-011).
   - Owner: bonos
   - Depends on: none (independent of Slice 1; values file changes do not require shell lib changes to land first)
   - Validation: write failing tests for Faro port, memory_limiter, filter, and spanmetrics in values files; update all five config sources (local values, STACKIT values, dev/stage/prod ArgoCD manifests); run tests green.

3. Slice 3: Dashboard provisioning — scripts + make targets + seed dashboards + bootstrap mirror (FR-012, FR-013, FR-014, FR-015, FR-016, FR-017).
   - Owner: bonos
   - Depends on: Slice 1 (OBSERVABILITY_DASHBOARDS_NAME contract change must land before make target references it)
   - Validation: write failing tests for script presence, make target declaration, seed dashboard existence, and OBSERVABILITY_DASHBOARDS_NAME in contract; implement all; run tests green.

4. Slice 4: Documentation + quality gates — update README, run make quality-hooks-fast, validate bootstrap template drift (FR-019, SDD-C-011).
   - Owner: bonos
   - Depends on: Slices 1, 2, 3 (README documents all three capabilities; quality gates require all changes present)
   - Validation: no regressions in quality-hooks-fast; quality-validate-bootstrap-template-drift passes; pytest ≥12 new assertions pass.

## App Onboarding Contract (Normative)
- App onboarding impact: impacted
- Notes: two new make targets (`infra-observability-dashboards-apply`, `infra-observability-dashboards-destroy`) added to blueprint generated Makefile; consumers using blueprint upgrade gain these targets. Consumer apps gain `FARO_ENDPOINT` in their environment without any change to their code — the env var is exported by `observability_init_env`.
- Required minimum make targets (N/A — tooling/infrastructure-only; new make targets are infra-layer, not app delivery workflow):
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

## Risks and Mitigations
- Risk 1 -> mitigation: ArgoCD Application inline values diverging from the baseline values file — mitigated by updating all three manifests (dev/stage/prod) in Slice 2 in a single commit; contract test asserts Faro port in all three manifests.
- Risk 2 -> mitigation: `kubectl create configmap --from-file` fails when no JSON files exist — mitigated by shipping at least one seed dashboard (golden-signals.json) so the apply script always has at least one file to pack.
- Risk 3 -> mitigation: `memory_limiter` processor out-of-order breaks pipeline — mitigated by unit test asserting `memory_limiter` appears before `batch` in both lane configs.
