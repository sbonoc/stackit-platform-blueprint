# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions count = 0 and unresolved alternatives = 0
- [ ] G-003 Confirm all four sign-offs are approved (Product, Architecture, Security, Operations)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes SDD-C-005 through SDD-C-015
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated
- [ ] G-006 Resolve Q-1 (Airflow chart version pin)
- [ ] G-007 Resolve Q-2 (DAG env var naming: `WORKFLOWS_LOCAL_DAGS_*` vs reuse `STACKIT_WORKFLOWS_DAGS_*`)
- [ ] G-008 Resolve Q-3 (OIDC wiring: `webserverConfig.py` vs OAuth2-proxy sidecar)
- [ ] G-009 Resolve Q-4 (OIDC env vars: new `WORKFLOWS_LOCAL_OIDC_*` vs Keycloak realm defaults)

## Implementation — Slice 1: Contract skeleton + test pyramid
- [ ] T-001 Create `tests/infra/modules/workflows/test_local_contract.py` with ≥ 10 static-analysis assertions
- [ ] T-002 Register `test_local_contract.py` in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope
- [ ] T-003 Confirm `make infra-contract-test-fast` shows expected failures (files not yet created)

## Implementation — Slice 2: Library + env contract
- [ ] T-010 Create `scripts/lib/infra/workflows_local.sh` with `workflows_local_init_env()` and helper functions
- [ ] T-011 Add `WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN` to `scripts/lib/infra/versions.sh`
- [ ] T-012 Confirm `test_local_contract.py` lib assertions turn green

## Implementation — Slice 3: Module execution dispatch + make targets
- [ ] T-020 Add `local-workflows:*` dispatch case to `scripts/lib/infra/module_execution.sh`
- [ ] T-021 Add `local-workflows` section to `scripts/bin/blueprint/render_makefile.sh` with five make targets
- [ ] T-022 Confirm rendered Makefile contains `infra-local-workflows-*` targets

## Implementation — Slice 4: Shell scripts
- [ ] T-030 Create `scripts/bin/infra/local_workflows_plan.sh`
- [ ] T-031 Create `scripts/bin/infra/local_workflows_apply.sh`
- [ ] T-032 Create `scripts/bin/infra/local_workflows_deploy.sh`
- [ ] T-033 Create `scripts/bin/infra/local_workflows_smoke.sh`
- [ ] T-034 Create `scripts/bin/infra/local_workflows_destroy.sh`
- [ ] T-035 Confirm `make infra-contract-test-fast` all passing

## Implementation — Slice 5: Helm values + ArgoCD manifests
- [ ] T-040 Create `infra/local/helm/workflows/airflow.values.yaml` with `LocalExecutor` + git-sync sidecar
- [ ] T-041 Replace ConfigMap stub with ArgoCD `Application` manifest at `infra/gitops/argocd/optional/local/workflows.yaml`
- [ ] T-042 Add `https://airflow.apache.org` to `infra/gitops/argocd/overlays/local/appproject.yaml` sourceRepos
- [ ] T-043 Confirm AC-006 and AC-007 assertions green

## Implementation — Slice 6: Contract YAML + docs
- [ ] T-050 Create `blueprint/modules/local-workflows/module.contract.yaml`
- [ ] T-051 Update `docs/platform/modules/workflows/README.md` with Local Lane section
- [ ] T-052 Run `make docs-build && make docs-smoke` — exit 0
- [ ] T-053 Run `make infra-validate` — exit 0

## Test Automation
- [ ] T-101 Confirm `test_local_contract.py` contains ≥ 10 passing assertions (static analysis only; no subprocess execution)
- [ ] T-102 Confirm `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` absent from all state file key assertions
- [ ] T-103 Confirm `WORKFLOWS_LOCAL_ENABLED` guard tested (log_fatal/log_info guard present in each script)
- [ ] T-104 Confirm `dags.gitSync.enabled` pattern present in `airflow.values.yaml` assertion
- [ ] T-105 Confirm `kind: Application` assertion for `workflows.yaml` ArgoCD manifest

## Accessibility Testing
- [ ] T-A01 NFR-A11Y-001 declared in `spec.md` as N/A — no UI or frontend changes. Confirmed.

## Validation and Release Readiness
- [ ] T-201 Run `make test-unit-all` — all passing; `test_local_contract.py` count ≥ 10
- [ ] T-202 Run `make infra-validate` — exit 0
- [ ] T-203 Run `make quality-hooks-fast` — all checks pass
- [ ] T-204 Run `make docs-build && make docs-smoke` — exit 0
- [ ] T-205 Run `make quality-hardening-review` — no blocking findings
- [ ] T-206 Run `make quality-sdd-check` — no violations

## Publish
- [ ] P-001 Update `hardening_review.md` with findings from `make quality-hardening-review`
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Confirm PR description references `pr_context.md` and uses "Part of #248" (not "Closes #248")
- [ ] P-004 Update `traceability.md` Validation Summary with actual command output
- [ ] P-005 Regenerate `evidence_manifest.json` with updated sha256 values

## App Onboarding Minimum Targets
- [ ] A-001 `apps-bootstrap` — N/A (infrastructure-only; no consumer app scope)
- [ ] A-002 `apps-smoke` — N/A
- [ ] A-003 `backend-test-unit` — N/A
- [ ] A-004 `backend-test-integration` — N/A
- [ ] A-005 `backend-test-contracts` — N/A
- [ ] A-006 `backend-test-e2e` — N/A
- [ ] A-007 `touchpoints-test-unit` — N/A
- [ ] A-008 `touchpoints-test-integration` — N/A
- [ ] A-009 `touchpoints-test-contracts` — N/A
- [ ] A-010 `touchpoints-test-e2e` — N/A
- [ ] A-011 `test-unit-all` — N/A (no new app tests; infra contract tests covered under T-201)
- [ ] A-012 `test-integration-all` — N/A
- [ ] A-013 `test-contracts-all` — N/A
- [ ] A-014 `test-e2e-all-local` — N/A
- [ ] A-015 `infra-port-forward-start` — N/A (local Airflow accessed via kubectl port-forward; not a make target)
- [ ] A-016 `infra-port-forward-stop` — N/A
- [ ] A-017 `infra-port-forward-cleanup` — N/A
