# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Local lane mirrors the langfuse/neo4j `argocd_optional_manifest` pattern exactly. No new abstractions; minimal new code surface.
- Anti-abstraction gate: `workflows_local.sh` is a thin env-setup lib; no wrapper layers beyond what the platform convention requires.
- Integration-first testing gate: Contract tests (`test_local_contract.py`) are static-analysis only (source-reading). No subprocess execution per platform convention.
- Positive-path filter/transform test gate: No filter/payload-transform logic in this work item. N/A.
- Finding-to-test translation gate: No pre-PR smoke findings expected for a local lane spec. Any smoke finding during implementation MUST be translated into a failing contract assertion before the fix.

## Delivery Slices (Red → Green TDD Order)

### Slice 1 — Contract skeleton + test pyramid (red) · owner: sbonoc
_Inputs:_ none · _Outputs:_ `test_local_contract.py` (failing), pyramid registration · _Depends on:_ nothing
1. Create `tests/infra/modules/workflows/test_local_contract.py` with ≥ 10 failing/stub assertions (files do not exist yet → path-existence assertions will fail immediately).
2. Register `test_local_contract.py` in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope.
3. Run `make infra-contract-test-fast` — confirm expected failures; no green yet.

### Slice 2 — Version pin + library (green for FR-002) · owner: sbonoc
_Inputs:_ Slice 1 complete · _Outputs:_ `workflows_local.sh`, `versions.sh` entry · _Depends on:_ Slice 1
4. Add `WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN="1.20.0"` to `scripts/lib/infra/versions.sh` — MUST precede lib creation because `workflows_local_init_env()` will source this value.
5. Create `scripts/lib/infra/workflows_local.sh` with `workflows_local_init_env()`, `workflows_local_public_url()`, and chart version accessor (sources `versions.sh`).
6. Run `make infra-contract-test-fast` — lib-function assertions turn green.

### Slice 3 — Module execution dispatch + make targets (green for FR-010, FR-011) · owner: sbonoc
_Inputs:_ Slice 2 complete · _Outputs:_ `module_execution.sh` dispatch case, `render_makefile.sh` section · _Depends on:_ Slice 2
7. Add `local-workflows:plan | local-workflows:apply | local-workflows:deploy | local-workflows:destroy` case to `scripts/lib/infra/module_execution.sh`.
8. Add `local-workflows` section to `scripts/bin/blueprint/render_makefile.sh` with all five make targets mapped to `local_workflows_*.sh` scripts.
9. Run `make quality-makefile-render` — verify `infra-local-workflows-*` targets appear in rendered Makefile.

### Slice 4 — Shell scripts (green for FR-003 through FR-007) · owner: sbonoc
_Inputs:_ Slices 2 + 3 complete (lib + dispatch available) · _Outputs:_ five `local_workflows_*.sh` scripts · _Depends on:_ Slices 2, 3
10. Create `scripts/bin/infra/local_workflows_plan.sh`.
11. Create `scripts/bin/infra/local_workflows_apply.sh`.
12. Create `scripts/bin/infra/local_workflows_deploy.sh`.
13. Create `scripts/bin/infra/local_workflows_smoke.sh`.
14. Create `scripts/bin/infra/local_workflows_destroy.sh`.
15. Run `make infra-contract-test-fast` — script-existence and key-pattern assertions turn green.

### Slice 5 — Helm values + ArgoCD manifests (green for FR-008, FR-009, AC-006, AC-007) · owner: sbonoc
_Inputs:_ Slice 3 complete (dispatch registered) · _Outputs:_ `airflow.values.yaml`, ArgoCD Application, `appproject.yaml` update · _Depends on:_ Slice 3 (parallel-capable with Slice 4)
16. Create `infra/local/helm/workflows/airflow.values.yaml` — `executor: LocalExecutor`, `dags.gitSync.enabled: true`, resource limits ≤ 1 CPU / ≤ 1Gi per component, `webserver.webserverConfig` OIDC block referencing `WORKFLOWS_LOCAL_OIDC_*` vars.
17. Replace ConfigMap stub with ArgoCD `Application` manifest at `infra/gitops/argocd/optional/local/workflows.yaml` — chart `apache-airflow/airflow`, version `1.20.0`, values file reference.
18. Add `https://airflow.apache.org` to `sourceRepos` in `infra/gitops/argocd/overlays/local/appproject.yaml`.
19. Run `make infra-contract-test-fast` — AC-006 and AC-007 assertions turn green.

### Slice 6 — Contract YAML + docs (green for FR-013, FR-014, AC-008, AC-009) · owner: sbonoc
_Inputs:_ Slices 4 + 5 complete · _Outputs:_ `module.contract.yaml`, README Local Lane section · _Depends on:_ Slices 4, 5
20. Create `blueprint/modules/local-workflows/module.contract.yaml`.
21. Update `docs/platform/modules/workflows/README.md` with Local Lane section.
22. Run `make docs-build && make docs-smoke` — exit 0.
23. Run `make infra-validate` — exit 0.

### Slice 7 — Full validation bundle (all green) · owner: sbonoc
_Inputs:_ Slices 1–6 complete · _Outputs:_ green CI-equivalent bundle · _Depends on:_ all prior slices
24. Run `make test-unit-all` — all assertions pass; `test_local_contract.py` count ≥ 10.
25. Run `make quality-hooks-fast` — all pre-commit checks pass.
26. Run `make quality-sdd-check` — no violations.
27. Run `make quality-hardening-review` — no blocking findings.

## Change Strategy
- Migration/rollout sequence: Additive only. No existing STACKIT workflows scripts, make targets, or contract YAML are modified.
- Backward compatibility policy: `WORKFLOWS_LOCAL_ENABLED` defaults to `false`; existing environments not using the flag are unaffected.
- Rollback plan: `make infra-local-workflows-destroy` removes the ArgoCD Application. Reverting the PR removes all new files. No database or managed-service state to clean up.

## Validation Strategy (Shift-Left)
- Unit checks: `make infra-contract-test-fast` — static analysis of new script and lib files.
- Contract checks: `make infra-validate` — validates `blueprint/modules/local-workflows/module.contract.yaml`.
- Integration checks: not applicable for this work item (local lane deployment validated by smoke, not automated integration tests).
- E2E checks: `make infra-local-workflows-smoke` on Docker Desktop Kubernetes (manual; not automated in CI).

## App Onboarding Contract (Normative)
- App onboarding impact: no-impact — this work item adds a new optional infrastructure module. No app make targets are added or changed.
- Notes: All existing app delivery targets remain unchanged.
- Required minimum make targets (all N/A — infrastructure-only scope):
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
- Blueprint docs updates: `docs/platform/modules/workflows/README.md` — add Local Lane section (env vars, make targets, DAG git-sync setup, Keycloak OIDC wiring, smoke command).
- Consumer docs updates: none — no consumer-facing contract change.
- Mermaid diagrams updated: architecture.md diagrams (Diagram 1 and Diagram 2 in this spec).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: Not required for this work item — no HTTP route handlers, query/filter logic, or new API endpoints are added. The local Airflow smoke (`make infra-local-workflows-smoke`) is a live cluster check, not automatable in CI.
- Publish checklist:
  - Requirement/contract coverage: all FR/NFR/AC traced in `traceability.md`
  - Key reviewer files: `scripts/lib/infra/workflows_local.sh`, `infra/local/helm/workflows/airflow.values.yaml`, `infra/gitops/argocd/optional/local/workflows.yaml`, `tests/infra/modules/workflows/test_local_contract.py`
  - Validation evidence: `make test-unit-all`, `make infra-validate`, `make quality-hooks-fast`, `make docs-build && make docs-smoke`
  - Rollback notes: `make infra-local-workflows-destroy` removes all local lane resources; PR revert removes all files.

## Operational Readiness
- Logging/metrics/traces: Airflow webserver and scheduler logs available via `kubectl logs -n data`. No Prometheus/Grafana integration for local lane.
- Alerts/ownership: Not applicable for local-only deployment.
- Runbook updates: README Local Lane section serves as the runbook for local Airflow operations.

## Risks and Mitigations
- Risk 1: Docker Desktop Kubernetes memory pressure → mitigation: conservative resource requests/limits in `airflow.values.yaml` (≤ 1 CPU, ≤ 1Gi per component).
- Risk 2: Airflow chart version breaking changes → mitigation: pin version in `versions.sh`; upgrade via standard version-bump PR process.
- Risk 3: Airflow 3.1 chart API changes (git-sync sidecar key names differ between chart versions) → mitigation: chart pinned at `1.20.0`; verify `dags.gitSync.*` key names against that chart's `values.yaml` before writing `airflow.values.yaml`.
