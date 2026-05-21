# PR Context

## Summary

This PR adds the `local-workflows` module, deploying Apache Airflow 1.20.0 (Airflow 3.1.8) on
Docker Desktop Kubernetes via ArgoCD + Helm. Engineers can now develop and test DAGs locally
without STACKIT cloud access, using the same DAG Git repository as the STACKIT lane. The
implementation follows the `argocd_optional_manifest` pattern established by the langfuse and
neo4j local lanes: `WORKFLOWS_LOCAL_ENABLED` (default: false) guards all five make targets
(`plan → apply → deploy → smoke → destroy`), DAGs are mounted via the git-sync sidecar,
OIDC SSO is wired via a `webserverConfig.py` Flask-AppBuilder override pointing to a local
Keycloak realm, and all secrets (`DAGS_REPO_TOKEN`, `OIDC_CLIENT_SECRET`) are excluded from
all state files. This closes the SDD-C-014 exception recorded in the STACKIT workflows module
(PR #314). Part of #248.

## Requirement Coverage

| Requirement ID | Implementation File(s) | Test Evidence |
|---|---|---|
| FR-001 `WORKFLOWS_LOCAL_ENABLED` toggle | `local_workflows_plan/apply/deploy/smoke.sh` | `ScriptContractTests::test_plan_script_checks_enabled_flag`; `test_apply_script_checks_enabled_flag` |
| FR-002 `workflows_local_init_env()` + `.git` URL guard | `scripts/lib/infra/workflows_local.sh` | `LibContractTests::test_workflows_local_init_env_function_defined`; `test_workflows_local_init_env_rejects_non_git_dags_url` |
| FR-003 plan script + plan state file | `local_workflows_plan.sh` | `PlanStateContractTests` — 4 key assertions |
| FR-004 apply script + deferred apply state | `local_workflows_apply.sh` | `ApplyStateContractTests::test_apply_state_has_deferred_status` |
| FR-005 deploy script + deploy state | `local_workflows_deploy.sh` | `DeployStateContractTests::test_deploy_state_has_deployed_status` |
| FR-006 smoke HTTP `/health` + smoke state | `local_workflows_smoke.sh` | `SmokeStateContractTests::test_smoke_state_has_status_passed` |
| FR-007 destroy + `remove_state_files_by_prefix` | `local_workflows_destroy.sh` | `ScriptContractTests::test_destroy_script_calls_remove_state_files_by_prefix` |
| FR-008 `airflow.values.yaml` — LocalExecutor + git-sync | `infra/local/helm/workflows/airflow.values.yaml` | `HelmValuesContractTests::test_airflow_values_has_gitsync_enabled`; `test_airflow_values_uses_local_executor` |
| FR-009 ArgoCD Application manifest (not ConfigMap stub) | `infra/gitops/argocd/optional/local/workflows.yaml` | `ArgoCDManifestContractTests::test_workflows_argocd_manifest_is_application` |
| FR-010 appproject sourceRepos + module_execution dispatch | `appproject.yaml`; `module_execution.sh` | `test_appproject_includes_airflow_repo`; `ModuleExecutionContractTests::test_module_execution_registers_local_workflows_case` |
| FR-011 render_makefile.sh five targets | `render_makefile.sh`; `profile.sh` | `ModuleExecutionContractTests::test_render_makefile_registers_local_workflows_targets` |
| FR-012 test pyramid registration ≥ 10 assertions | `test_pyramid_contract.json`; `test_local_contract.py` | 23 assertions pass; pyramid pre-commit gate |
| FR-013 `module.contract.yaml` + `infra-validate` | `blueprint/modules/local-workflows/module.contract.yaml` | `test_local_contract_yaml_exists`; `make infra-validate` exit 0 |
| FR-014 standalone local-workflows README | `docs/platform/modules/local-workflows/README.md` | `make docs-build && make docs-smoke` exit 0 |
| NFR-SEC-001 token/secret absent from state files | `local_workflows_plan.sh` | `SecurityContractTests::test_dags_repo_token_absent_from_plan_state_keys`; `test_oidc_client_secret_absent_from_plan_state_keys` |
| NFR-OPS-001 ENABLED=false → exit 0 | all four guarded scripts | `ScriptContractTests` guard assertions |
| AC-001–AC-010 | See traceability.md | 23 tests pass; `make infra-validate` exit 0; docs-build/smoke exit 0 |

## Key Reviewer Files

| File | Why it matters |
|---|---|
| `scripts/lib/infra/workflows_local.sh` | New library: `workflows_local_init_env()` validates all required env vars, enforces `.git` URL constraint, sets defaults; `workflows_local_public_url()` and `workflows_local_chart_version()` helpers |
| `scripts/lib/infra/module_execution.sh` | Added `local-workflows:plan\|apply\|deploy\|destroy` dispatch case — security-relevant routing to `argocd_optional_manifest` driver; missed entries here would silently fall to default |
| `scripts/lib/infra/profile.sh` | Added `local-workflows` → `WORKFLOWS_LOCAL_ENABLED` mapping in `module_flag_name()`; incorrect here breaks make target guard and rendered Makefile |
| `scripts/bin/infra/local_workflows_plan.sh` | First lifecycle script; verifies manifest exists, writes plan state; NFR-SEC-001 critical path — DAGS_REPO_TOKEN must not appear as a state key |
| `infra/local/helm/workflows/airflow.values.yaml` | All Airflow deployment decisions: `LocalExecutor`, git-sync sidecar (`dags.gitSync.enabled: true`), Docker Desktop resource limits (≤ 1 CPU / ≤ 1Gi per component), `webserverConfig.py` OIDC block |
| `infra/gitops/argocd/optional/local/workflows.yaml` | Replaced ConfigMap stub with ArgoCD multi-source Application; `sourceRepos` impact on `appproject.yaml` flows from this; chart version pin visible here |
| `blueprint/modules/local-workflows/module.contract.yaml` | Formal module contract: `enable_flag`, required env vars, five make targets, failure modes, cleanup contract |
| `tests/infra/modules/workflows/test_local_contract.py` | 23-assertion static analysis suite; verifies all four contract surfaces (lib, state keys, scripts, manifests/Helm values) without subprocess execution |

## Validation Evidence

```
$ python3 -m pytest tests/infra/modules/workflows/test_local_contract.py -q
.......................                       [100%]
23 passed in 0.06s
(2026-05-20)

$ make infra-validate
[infra-validate] contract validation passed
exit 0 (2026-05-20)

$ make quality-hooks-fast
check for merge conflicts................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
check yaml...............................................................Passed
check for added large files..............................................Passed
bash syntax check........................................................Passed
quality docs lint (markdown targets and links)...........................Passed
quality test-pyramid classification check................................Passed
quality bootstrap template drift check...................................Passed
exit 0 (2026-05-20)

$ make quality-hardening-review
[quality-sdd-check] validated SDD assets, readiness gates, and language policy
[quality-hardening-review gate completed]
exit 0 (2026-05-20)

$ make docs-build && make docs-smoke
exit 0 (2026-05-20)
```

## Risk and Rollback

**Feature flag (default off):** `WORKFLOWS_LOCAL_ENABLED=false` (default) causes all five
make targets to exit 0 with a log message and skip all provisioning. Zero risk to existing
modules or the STACKIT lane when the flag is unset.

**Blast radius:**
- Local lane only; no STACKIT API calls and no mutations to `WORKFLOWS_*` (STACKIT lane)
  state files.
- `infra/gitops/argocd/overlays/local/appproject.yaml` gains `https://airflow.apache.org`
  in `sourceRepos` — backward-compatible; existing Applications are unaffected.
- Bootstrap template `scripts/templates/…/blueprint/contract.yaml` updated in lock-step;
  bootstrap template drift check passes.

**Rollback steps:**
1. `make infra-local-workflows-destroy` — deletes ArgoCD Application; ArgoCD automated sync
   prunes the Helm release; `remove_state_files_by_prefix "local_workflows_"` clears all
   state artifacts.
2. Remove `https://airflow.apache.org` from `appproject.yaml` if desired (safe to revert
   without cluster impact when no Application references the chart).
3. Revert branch or cherry-pick the revert commit — no database migrations, no external
   state mutations.

## Deferred Proposals

**Proposal 1: Automate port-forward within smoke script**
`local_workflows_smoke.sh` requires the user to start `kubectl port-forward` manually before
`make infra-local-workflows-smoke`. A future improvement would embed a transient port-forward
(background process, trap-based cleanup) to make the target fully self-contained.
— Outcome: Parked — trigger: on-scope: workflows — low urgency; README documents the step;
automating requires signal handling out of scope for this work item.

**Proposal 2: Automate `airflow-git-credentials` Kubernetes secret creation**
The `airflow-git-credentials` secret must be created manually before
`make infra-local-workflows-deploy`. A future `infra-local-workflows-init-secrets` target
(following the `langfuse_keycloak_reconcile.sh` pattern) could automate this.
— Outcome: Parked — trigger: on-scope: workflows — one-time operation; complexity deferred
until a reconcile-style init-secrets pattern is needed across multiple modules.
