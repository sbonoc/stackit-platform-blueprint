# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md` — confirmed 2026-05-20
- [x] G-002 Confirm open questions count = 0 and unresolved alternatives = 0 — confirmed 2026-05-20
- [x] G-003 Confirm all four sign-offs are approved (Product, Architecture, Security, Operations) — confirmed 2026-05-20
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes SDD-C-005 through SDD-C-015 — confirmed 2026-05-20
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated — confirmed 2026-05-20
- [x] G-006 Q-1 resolved — chart `1.20.0` (Airflow 3.1.8); PR #316 comment 2026-05-20
- [x] G-007 Q-2 resolved — new `WORKFLOWS_LOCAL_DAGS_*` vars (Option A); PR #316 comment 2026-05-20
- [x] G-008 Q-3 resolved — `webserverConfig.py` override (Option A); PR #316 comment 2026-05-20
- [x] G-009 Q-4 resolved — dedicated `WORKFLOWS_LOCAL_OIDC_*` vars (Option A); PR #316 comment 2026-05-20

## Implementation — Slice 1: Contract skeleton + test pyramid
- [x] T-001 Create `tests/infra/modules/workflows/test_local_contract.py` with ≥ 10 static-analysis assertions
- [x] T-002 Register `test_local_contract.py` in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope
- [x] T-003 Confirm `make infra-contract-test-fast` shows expected failures (files not yet created)

## Implementation — Slice 2: Version pin + library (owner: sbonoc)
- [x] T-010 Add `WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN="1.20.0"` to `scripts/lib/infra/versions.sh` (MUST precede lib creation)
- [x] T-011 Create `scripts/lib/infra/workflows_local.sh` with `workflows_local_init_env()` and helper functions
- [x] T-012 Confirm `test_local_contract.py` lib assertions turn green

## Implementation — Slice 3: Module execution dispatch + make targets
- [x] T-020 Add `local-workflows:*` dispatch case to `scripts/lib/infra/module_execution.sh`
- [x] T-021 Add `local-workflows` section to `scripts/bin/blueprint/render_makefile.sh` with five make targets
- [x] T-022 Confirm rendered Makefile contains `infra-local-workflows-*` targets

## Implementation — Slice 4: Shell scripts
- [x] T-030 Create `scripts/bin/infra/local_workflows_plan.sh`
- [x] T-031 Create `scripts/bin/infra/local_workflows_apply.sh`
- [x] T-032 Create `scripts/bin/infra/local_workflows_deploy.sh`
- [x] T-033 Create `scripts/bin/infra/local_workflows_smoke.sh`
- [x] T-034 Create `scripts/bin/infra/local_workflows_destroy.sh`
- [x] T-035 Confirm `make infra-contract-test-fast` all passing

## Implementation — Slice 5: Helm values + ArgoCD manifests
- [x] T-040 Create `infra/local/helm/workflows/airflow.values.yaml` with `LocalExecutor` + git-sync sidecar
- [x] T-041 Replace ConfigMap stub with ArgoCD `Application` manifest at `infra/gitops/argocd/optional/local/workflows.yaml`
- [x] T-042 Add `https://airflow.apache.org` to `infra/gitops/argocd/overlays/local/appproject.yaml` sourceRepos
- [x] T-043 Confirm AC-006 and AC-007 assertions green

## Implementation — Slice 6: Contract YAML + docs
- [x] T-050 Create `blueprint/modules/local-workflows/module.contract.yaml`
- [x] T-051 Update `docs/platform/modules/workflows/README.md` with Local Lane section
- [x] T-052 Run `make docs-build && make docs-smoke` — exit 0
- [x] T-053 Run `make infra-validate` — exit 0

## Test Automation
- [x] T-101 Confirm `test_local_contract.py` contains ≥ 10 passing assertions (static analysis only; no subprocess execution)
- [x] T-102 Confirm `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` absent from all state file key assertions
- [x] T-103 Confirm `WORKFLOWS_LOCAL_ENABLED` guard tested (log_fatal/log_info guard present in each script)
- [x] T-104 Confirm `dags.gitSync.enabled` pattern present in `airflow.values.yaml` assertion
- [x] T-105 Confirm `kind: Application` assertion for `workflows.yaml` ArgoCD manifest

## Accessibility Testing
- [x] T-A01 NFR-A11Y-001 declared in `spec.md` as N/A — no UI or frontend changes. Confirmed.

## Validation and Release Readiness
- [x] T-201 Run `make test-unit-all` — all passing; `test_local_contract.py` count ≥ 10 (23 passed, 2026-05-20)
- [x] T-202 Run `make infra-validate` — exit 0 (2026-05-20)
- [x] T-203 Run `make quality-hooks-fast` — all checks pass (2026-05-20)
- [x] T-204 Run `make docs-build && make docs-smoke` — exit 0 (2026-05-20)
- [x] T-205 Run `make quality-hardening-review` — no blocking findings (2026-05-20)
- [x] T-206 Run `make quality-sdd-check` — no violations (2026-05-20)

## Publish
- [x] P-001 Update `hardening_review.md` with findings from `make quality-hardening-review`
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Confirm PR description references `pr_context.md` and uses "Part of #248" (not "Closes #248")
- [x] P-004 Update `traceability.md` Validation Summary with actual command output
- [x] P-005 Regenerate `evidence_manifest.json` with updated sha256 values

## App Onboarding Minimum Targets
- [x] A-001 `apps-bootstrap` — N/A (infrastructure-only; no consumer app scope)
- [x] A-002 `apps-smoke` — N/A
- [x] A-003 `backend-test-unit` — N/A
- [x] A-004 `backend-test-integration` — N/A
- [x] A-005 `backend-test-contracts` — N/A
- [x] A-006 `backend-test-e2e` — N/A
- [x] A-007 `touchpoints-test-unit` — N/A
- [x] A-008 `touchpoints-test-integration` — N/A
- [x] A-009 `touchpoints-test-contracts` — N/A
- [x] A-010 `touchpoints-test-e2e` — N/A
- [x] A-011 `test-unit-all` — N/A (no new app tests; infra contract tests covered under T-201)
- [x] A-012 `test-integration-all` — N/A
- [x] A-013 `test-contracts-all` — N/A
- [x] A-014 `test-e2e-all-local` — N/A
- [x] A-015 `infra-port-forward-start` — N/A (local Airflow accessed via kubectl port-forward; not a make target)
- [x] A-016 `infra-port-forward-stop` — N/A
- [x] A-017 `infra-port-forward-cleanup` — N/A
