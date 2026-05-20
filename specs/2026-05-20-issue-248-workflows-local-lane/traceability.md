# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | n/a | `WORKFLOWS_LOCAL_ENABLED` feature toggle; guard in each `local_workflows_*.sh` script | `scripts/bin/infra/local_workflows_plan.sh`; all `local_workflows_*.sh` scripts | `test_local_contract.py` — `WORKFLOWS_LOCAL_ENABLED` guard present in each script | `docs/platform/modules/workflows/README.md` Local Lane section | `WORKFLOWS_LOCAL_ENABLED=false` → make targets exit 0 |
| FR-002 | SDD-C-005 | n/a | `workflows_local_init_env()` env var validation + `.git` URL constraint + defaults | `scripts/lib/infra/workflows_local.sh` | `test_local_contract.py` — `test_workflows_local_init_env_function_defined`, `test_workflows_local_init_env_rejects_non_git_dags_url` | README Local Lane section | `make infra-local-workflows-plan` fails fast on missing env |
| FR-003 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_plan.sh` ArgoCD manifest path resolution + plan state file | `scripts/bin/infra/local_workflows_plan.sh` | `test_local_contract.py` — `provision_driver`, `provision_path`, `public_url`, `chart_version` keys in plan state | README | `artifacts/infra/workflows_local_plan.env` |
| FR-004 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_apply.sh` deferred apply + apply state file | `scripts/bin/infra/local_workflows_apply.sh` | `test_local_contract.py` — `provision_status=deferred_to_deploy` key in apply state | README | `artifacts/infra/workflows_local_apply.env` |
| FR-005 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_deploy.sh` ArgoCD Application sync + deploy state file | `scripts/bin/infra/local_workflows_deploy.sh` | `test_local_contract.py` — `provision_status=deployed` key in deploy state | README | `artifacts/infra/workflows_local_deploy.env` |
| FR-006 | SDD-C-010 | n/a | `local_workflows_smoke.sh` HTTP `/health` check + smoke state file | `scripts/bin/infra/local_workflows_smoke.sh` | `test_local_contract.py` — `test_smoke_state_has_status_passed` (`status=passed` key in smoke state) | README | `artifacts/infra/workflows_local_smoke.env` status=passed |
| FR-007 | SDD-C-005, SDD-C-012 | n/a | `local_workflows_destroy.sh` ArgoCD Application deletion + `remove_state_files_by_prefix` | `scripts/bin/infra/local_workflows_destroy.sh` | `test_local_contract.py` — `test_destroy_script_calls_remove_state_files_by_prefix` | README | state files removed; ArgoCD Application deleted |
| FR-008 | SDD-C-006, SDD-C-015 | n/a | `airflow.values.yaml` with `LocalExecutor` + git-sync sidecar | `infra/local/helm/workflows/airflow.values.yaml` | `test_local_contract.py` — `test_airflow_values_has_gitsync_enabled`, `test_airflow_values_uses_local_executor` | README | Airflow pod running with git-sync sidecar on Docker Desktop K8s |
| FR-009 | SDD-C-015 | n/a | `workflows.yaml` as ArgoCD Application (not ConfigMap stub) | `infra/gitops/argocd/optional/local/workflows.yaml` | `test_local_contract.py` — `test_workflows_argocd_manifest_is_application` (`kind: Application` present) | README | ArgoCD Application resource synced in cluster |
| FR-010 | SDD-C-015 | n/a | `appproject.yaml` includes airflow chart repo; `module_execution.sh` `local-workflows:*` case | `infra/gitops/argocd/overlays/local/appproject.yaml`; `scripts/lib/infra/module_execution.sh` | `test_local_contract.py` — `test_appproject_includes_airflow_repo`, `test_module_execution_registers_local_workflows_case` | README | ArgoCD AppProject allows chart source |
| FR-011 | SDD-C-005 | n/a | `render_makefile.sh` `local-workflows` section with five targets | `scripts/bin/blueprint/render_makefile.sh` | `test_local_contract.py` — `test_render_makefile_registers_local_workflows_targets` | README | `infra-local-workflows-plan` target present |
| FR-012 | SDD-C-008 | n/a | test pyramid registration + `test_local_contract.py` ≥ 10 assertions | `scripts/lib/quality/test_pyramid_contract.json`; `tests/infra/modules/workflows/test_local_contract.py` | pytest output ≥ 10 passed; pyramid pre-commit gate | n/a | `make test-unit-all` |
| FR-013 | SDD-C-008 | n/a | `blueprint/modules/local-workflows/module.contract.yaml` | `blueprint/modules/local-workflows/module.contract.yaml` | `make infra-validate` exit 0 | n/a | `make infra-validate` |
| FR-014 | SDD-C-011 | n/a | README Local Lane section | `docs/platform/modules/workflows/README.md` | `make docs-build && make docs-smoke` exit 0 | README itself | `make docs-smoke` exit 0 |
| NFR-SEC-001 | SDD-C-009 | n/a | `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` and `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET` absent from all state files | `local_workflows_plan.sh`; `local_workflows_apply.sh`; `local_workflows_deploy.sh` | `test_local_contract.py` — `test_dags_repo_token_absent_from_all_state_files`, `test_oidc_client_secret_absent_from_all_state_files` (script-reading) | README — security note | state files contain no token/secret keys |
| NFR-OPS-001 | SDD-C-013 | n/a | `WORKFLOWS_LOCAL_ENABLED=false` guard in each `local_workflows_*.sh` script | all `local_workflows_*.sh` scripts | `test_local_contract.py` — `WORKFLOWS_LOCAL_ENABLED` guard present in each script | README | all `infra-local-workflows-*` targets exit 0 when flag is false |
| NFR-REL-001 | n/a | n/a | ArgoCD sync retry covered by platform defaults | `infra/gitops/argocd/overlays/local/application-platform-local.yaml` | n/a — platform default; no custom config required | README — rollback section | `make infra-local-workflows-destroy` removes Application |
| NFR-A11Y-001 | n/a | n/a | N/A — no UI or frontend changes | n/a | n/a | n/a | n/a |
| AC-001 | SDD-C-012 | n/a | plan state file structure | `local_workflows_plan.sh` | `test_local_contract.py` | README | `artifacts/infra/workflows_local_plan.env` |
| AC-002 | SDD-C-012 | n/a | apply state key structure | `local_workflows_apply.sh` | `test_local_contract.py` | README | `artifacts/infra/workflows_local_apply.env` |
| AC-003 | SDD-C-012 | n/a | deploy state `provision_status=deployed` key | `local_workflows_deploy.sh` | `test_local_contract.py` | README | `artifacts/infra/workflows_local_deploy.env` |
| AC-004 | SDD-C-010 | n/a | smoke state `status=passed` key | `local_workflows_smoke.sh` | `test_local_contract.py` | README | `artifacts/infra/workflows_local_smoke.env` |
| AC-005 | SDD-C-009 | n/a | token absent from all state files | all `local_workflows_*.sh` | `test_local_contract.py` | README | state file inspection |
| AC-006 | SDD-C-006 | n/a | `dags.gitSync.enabled` in `airflow.values.yaml` | `infra/local/helm/workflows/airflow.values.yaml` | `test_local_contract.py` | README | git-sync sidecar in Airflow pod |
| AC-007 | SDD-C-015 | n/a | `kind: Application` in `workflows.yaml` | `infra/gitops/argocd/optional/local/workflows.yaml` | `test_local_contract.py` | README | ArgoCD Application resource in cluster |
| AC-008 | SDD-C-008 | n/a | `make infra-validate` exit 0 | `blueprint/modules/local-workflows/module.contract.yaml` | `make infra-validate` | n/a | `make infra-validate` |
| AC-009 | SDD-C-011 | n/a | README completeness | `docs/platform/modules/workflows/README.md` | `make docs-build && make docs-smoke` | README itself | `make docs-smoke` |
| AC-010 | SDD-C-008 | n/a | `test_local_contract.py` ≥ 10 assertions and pyramid registration | `test_local_contract.py`; `test_pyramid_contract.json` | pytest output | n/a | `make test-unit-all` |

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
