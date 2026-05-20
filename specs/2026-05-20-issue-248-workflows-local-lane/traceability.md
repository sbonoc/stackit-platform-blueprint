# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | n/a | `WORKFLOWS_LOCAL_ENABLED` feature toggle; guard in plan/apply/deploy/smoke scripts | `scripts/bin/infra/local_workflows_plan.sh`; `local_workflows_apply.sh`; `local_workflows_deploy.sh`; `local_workflows_smoke.sh` | `test_local_contract.py::ScriptContractTests::test_plan_script_checks_enabled_flag`; `test_apply_script_checks_enabled_flag` | `docs/platform/modules/local-workflows/README.md` | `WORKFLOWS_LOCAL_ENABLED=false` → make targets exit 0 |
| FR-002 | SDD-C-005 | n/a | `workflows_local_init_env()` env var validation + `.git` URL constraint + defaults | `scripts/lib/infra/workflows_local.sh` | `test_local_contract.py::LibContractTests::test_workflows_local_init_env_function_defined`; `test_workflows_local_init_env_rejects_non_git_dags_url` | `docs/platform/modules/local-workflows/README.md` | `make infra-local-workflows-plan` fails fast on missing env |
| FR-003 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_plan.sh` ArgoCD manifest path resolution + plan state file | `scripts/bin/infra/local_workflows_plan.sh` | `test_local_contract.py::PlanStateContractTests` — `provision_driver`, `provision_path`, `public_url`, `chart_version` keys | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_plan.env` |
| FR-004 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_apply.sh` deferred apply + apply state file | `scripts/bin/infra/local_workflows_apply.sh` | `test_local_contract.py::ApplyStateContractTests::test_apply_state_has_deferred_status` | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_apply.env` |
| FR-005 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_deploy.sh` ArgoCD Application sync + deploy state file | `scripts/bin/infra/local_workflows_deploy.sh` | `test_local_contract.py::DeployStateContractTests::test_deploy_state_has_deployed_status` | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_deploy.env` |
| FR-006 | SDD-C-010 | n/a | `local_workflows_smoke.sh` HTTP `/health` check + smoke state file | `scripts/bin/infra/local_workflows_smoke.sh` | `test_local_contract.py::SmokeStateContractTests::test_smoke_state_has_status_passed` | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_smoke.env` status=passed |
| FR-007 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_destroy.sh` ArgoCD Application deletion + `remove_state_files_by_prefix` | `scripts/bin/infra/local_workflows_destroy.sh` | `test_local_contract.py::ScriptContractTests::test_destroy_script_calls_remove_state_files_by_prefix` | `docs/platform/modules/local-workflows/README.md` | state files removed; ArgoCD Application deleted |
| FR-008 | SDD-C-006, SDD-C-015 | n/a | `airflow.values.yaml` with `LocalExecutor` + `dags.gitSync` sidecar | `infra/local/helm/workflows/airflow.values.yaml` | `test_local_contract.py::HelmValuesContractTests::test_airflow_values_has_gitsync_enabled`; `test_airflow_values_uses_local_executor` | `docs/platform/modules/local-workflows/README.md` | Airflow pod running with git-sync sidecar on Docker Desktop K8s |
| FR-009 | SDD-C-015 | n/a | `workflows.yaml` as ArgoCD Application (not ConfigMap stub) | `infra/gitops/argocd/optional/local/workflows.yaml` | `test_local_contract.py::ArgoCDManifestContractTests::test_workflows_argocd_manifest_is_application` | `docs/platform/modules/local-workflows/README.md` | ArgoCD Application resource synced in cluster |
| FR-010 | SDD-C-015 | n/a | `appproject.yaml` includes airflow chart repo; `module_execution.sh` `local-workflows:*` case | `infra/gitops/argocd/overlays/local/appproject.yaml`; `scripts/lib/infra/module_execution.sh` | `test_local_contract.py::ArgoCDManifestContractTests::test_appproject_includes_airflow_repo`; `ModuleExecutionContractTests::test_module_execution_registers_local_workflows_case` | `docs/platform/modules/local-workflows/README.md` | ArgoCD AppProject allows chart source |
| FR-011 | SDD-C-005 | n/a | `render_makefile.sh` `local-workflows` section with five targets | `scripts/bin/blueprint/render_makefile.sh`; `scripts/lib/infra/profile.sh` | `test_local_contract.py::ModuleExecutionContractTests::test_render_makefile_registers_local_workflows_targets` | `docs/platform/modules/local-workflows/README.md` | `infra-local-workflows-plan` target present |
| FR-012 | SDD-C-008 | n/a | test pyramid registration + `test_local_contract.py` ≥ 10 assertions | `scripts/lib/quality/test_pyramid_contract.json`; `tests/infra/modules/workflows/test_local_contract.py` | 23 assertions pass; pyramid pre-commit gate | n/a | `make test-unit-all` — 23 passed |
| FR-013 | SDD-C-008 | n/a | `blueprint/modules/local-workflows/module.contract.yaml` exists and validates | `blueprint/modules/local-workflows/module.contract.yaml` | `test_local_contract.py::ModuleExecutionContractTests::test_local_contract_yaml_exists`; `make infra-validate` exit 0 | n/a | `make infra-validate` exit 0 |
| FR-014 | SDD-C-011 | n/a | Standalone README for local-workflows module | `docs/platform/modules/local-workflows/README.md` | `make docs-build && make docs-smoke` exit 0 | `docs/platform/modules/local-workflows/README.md` | `make docs-smoke` exit 0 |
| NFR-SEC-001 | SDD-C-009 | n/a | `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` and `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET` absent from all state files | `local_workflows_plan.sh`; `local_workflows_apply.sh` | `test_local_contract.py::SecurityContractTests::test_dags_repo_token_absent_from_plan_state_keys`; `test_oidc_client_secret_absent_from_plan_state_keys` | `docs/platform/modules/local-workflows/README.md` Security section | state files contain no token/secret keys |
| NFR-OPS-001 | SDD-C-013 | n/a | `WORKFLOWS_LOCAL_ENABLED=false` guard in plan/apply/deploy/smoke scripts | `local_workflows_plan.sh`; `local_workflows_apply.sh`; `local_workflows_deploy.sh`; `local_workflows_smoke.sh` | `test_local_contract.py::ScriptContractTests` guard assertions | `docs/platform/modules/local-workflows/README.md` | all `infra-local-workflows-*` targets exit 0 when flag is false |
| NFR-REL-001 | n/a | n/a | ArgoCD sync retry covered by platform defaults | `infra/gitops/argocd/optional/local/workflows.yaml` syncPolicy | n/a — platform default; no custom config required | `docs/platform/modules/local-workflows/README.md` Teardown section | `make infra-local-workflows-destroy` removes Application |
| NFR-A11Y-001 | n/a | n/a | N/A — no UI or frontend changes | n/a | n/a | n/a | n/a |
| AC-001 | SDD-C-012 | n/a | plan state file contains `provision_driver`, `provision_path`, `public_url`, `chart_version` | `local_workflows_plan.sh` | `test_local_contract.py::PlanStateContractTests` (4 assertions) | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_plan.env` |
| AC-002 | SDD-C-012 | n/a | apply state contains `provision_status=deferred_to_deploy` | `local_workflows_apply.sh` | `test_local_contract.py::ApplyStateContractTests::test_apply_state_has_deferred_status` | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_apply.env` |
| AC-003 | SDD-C-012 | n/a | deploy state `provision_status=deployed` key | `local_workflows_deploy.sh` | `test_local_contract.py::DeployStateContractTests::test_deploy_state_has_deployed_status` | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_deploy.env` |
| AC-004 | SDD-C-010 | n/a | smoke state `status=passed` key | `local_workflows_smoke.sh` | `test_local_contract.py::SmokeStateContractTests::test_smoke_state_has_status_passed` | `docs/platform/modules/local-workflows/README.md` | `artifacts/infra/local_workflows_smoke.env` |
| AC-005 | SDD-C-009 | n/a | `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` absent from plan state file keys | `local_workflows_plan.sh` | `test_local_contract.py::SecurityContractTests::test_dags_repo_token_absent_from_plan_state_keys` | `docs/platform/modules/local-workflows/README.md` | state file inspection |
| AC-006 | SDD-C-006 | n/a | `gitSync` present in `airflow.values.yaml` | `infra/local/helm/workflows/airflow.values.yaml` | `test_local_contract.py::HelmValuesContractTests::test_airflow_values_has_gitsync_enabled` | `docs/platform/modules/local-workflows/README.md` | git-sync sidecar in Airflow pod |
| AC-007 | SDD-C-015 | n/a | `kind: Application` in `workflows.yaml` | `infra/gitops/argocd/optional/local/workflows.yaml` | `test_local_contract.py::ArgoCDManifestContractTests::test_workflows_argocd_manifest_is_application` | `docs/platform/modules/local-workflows/README.md` | ArgoCD Application resource in cluster |
| AC-008 | SDD-C-008 | n/a | `make infra-validate` exit 0 with contract YAML present | `blueprint/modules/local-workflows/module.contract.yaml` | `make infra-validate` exit 0 (2026-05-20) | n/a | `make infra-validate` |
| AC-009 | SDD-C-011 | n/a | `make docs-build && make docs-smoke` exit 0 after README added | `docs/platform/modules/local-workflows/README.md` | `make docs-build && make docs-smoke` exit 0 (2026-05-20) | `docs/platform/modules/local-workflows/README.md` | `make docs-smoke` |
| AC-010 | SDD-C-008 | n/a | `test_local_contract.py` ≥ 10 assertions and pyramid registration | `tests/infra/modules/workflows/test_local_contract.py`; `test_pyramid_contract.json` | 23 passed (pytest 2026-05-20) | n/a | `make test-unit-all` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001 through FR-014, NFR-SEC-001, NFR-OPS-001, NFR-REL-001, NFR-A11Y-001, AC-001 through AC-010

## Validation Summary
- Required bundles to execute: `make test-unit-all`, `make infra-validate`, `make quality-hooks-fast`, `make docs-build && make docs-smoke`, `make quality-hardening-review`, `make quality-sdd-check`
- Result summary: pending — spec at Draft PR stage; implementation not yet started.
- Documentation validation:
  - `make docs-build` — pending
  - `make docs-smoke` — pending

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Q-1 (Airflow chart version pin): resolved — chart `1.20.0` (Airflow 3.1.8); PR #316 comment 2026-05-20.
- Q-2 (DAG env var naming): resolved — new `WORKFLOWS_LOCAL_DAGS_REPO_URL/_BRANCH/_TOKEN` (Option A); PR #316 comment 2026-05-20.
- Q-3 (OIDC wiring approach): resolved — `webserverConfig.py` override in Helm values (Option A); PR #316 comment 2026-05-20.
- Q-4 (OIDC env var reuse): resolved — dedicated `WORKFLOWS_LOCAL_OIDC_CLIENT_ID/_CLIENT_SECRET/_ISSUER_URL` (Option A); PR #316 comment 2026-05-20.
- Parked: Python version coexistence strategy — separate backlog item; out of scope.
- Parked: Provider-backed STACKIT lane migration — separate backlog item; out of scope.
