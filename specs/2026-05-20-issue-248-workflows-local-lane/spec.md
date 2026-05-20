# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-workflows-local-lane.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015
- Control exception rationale: none — this work item resolves the SDD-C-014 exception recorded in the STACKIT workflows module spec (PR #314). The local lane added here satisfies the local-first baseline requirement for the workflows module.

## Implementation Stack Profile (Normative)
- Backend stack profile: shell_plus_bash
- Frontend stack profile: none
- Test automation profile: pytest_static_analysis
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: This work item provisions Apache Airflow on local Docker Desktop Kubernetes for DAG development purposes. There is no STACKIT-managed equivalent for the local lane; the local lane is explicitly self-hosted by design.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Engineers can develop, test, and iterate on Apache Airflow DAGs locally on Docker Desktop Kubernetes without a STACKIT account, using the same DAG repository as the STACKIT lane.
- Success metric: `make infra-local-workflows-smoke` exits 0 on Docker Desktop Kubernetes with `WORKFLOWS_LOCAL_ENABLED=true` and a valid DAG repository configured.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 `WORKFLOWS_LOCAL_ENABLED` feature toggle MUST guard all `infra-local-workflows-*` make targets; when `WORKFLOWS_LOCAL_ENABLED=false` every target MUST exit 0 with a log message and skip all provisioning.

- FR-002 `workflows_local_init_env()` in `scripts/lib/infra/workflows_local.sh` MUST validate that `WORKFLOWS_LOCAL_DAGS_REPO_URL` ends with `.git`, set defaults for `WORKFLOWS_LOCAL_NAMESPACE` (`data`), `WORKFLOWS_LOCAL_HELM_RELEASE` (`blueprint-workflows-local`), `WORKFLOWS_LOCAL_HELM_CHART` (`apache-airflow/airflow`), and call `require_env_vars` for all required inputs.

  DAG env var namespace: new `WORKFLOWS_LOCAL_DAGS_REPO_URL / _BRANCH / _TOKEN` (Option A) — separate vars prevent accidental cross-lane credential sharing and allow independent repo and branch configuration during local development. Decision by PR #316 comment 2026-05-20.

- FR-003 `scripts/bin/infra/local_workflows_plan.sh` MUST call `resolve_optional_module_execution "local-workflows" "plan"` (driver: `argocd_optional_manifest`), verify the manifest exists via `optional_module_require_manifest_present`, and write a plan state file via `write_state_file "workflows_local_plan"` containing `provision_driver`, `provision_path`, `public_url`, and `chart_version` keys.

- FR-004 `scripts/bin/infra/local_workflows_apply.sh` MUST call `resolve_optional_module_execution "local-workflows" "apply"`, defer to `argocd_optional_manifest` driver, and write an apply state file via `write_state_file "workflows_local_apply"` with `provision_status=deferred_to_deploy`.

- FR-005 `scripts/bin/infra/local_workflows_deploy.sh` MUST apply the ArgoCD Application manifest (`kubectl apply -f`) and write a deploy state file via `write_state_file "workflows_local_deploy"` with `provision_status=deployed`.

- FR-006 `scripts/bin/infra/local_workflows_smoke.sh` MUST perform an HTTP health check against the Airflow webserver (`/health` endpoint via port-forward or ingress), assert `status=healthy` in the response body, and write a smoke state file via `write_state_file "workflows_local_smoke"` with `status=passed` on success.

- FR-007 `scripts/bin/infra/local_workflows_destroy.sh` MUST delete the ArgoCD Application manifest (`kubectl delete -f`) and call `remove_state_files_by_prefix "workflows_local"` to remove all local lane state files.

- FR-008 `infra/local/helm/workflows/airflow.values.yaml` MUST configure Apache Airflow with: `executor: LocalExecutor`, git-sync sidecar enabled (`dags.gitSync.enabled: true`) with `repo`, `branch`, and `credentialsSecret` fields, resource requests/limits appropriate for Docker Desktop Kubernetes (≤ 1 CPU, ≤ 1Gi memory per component).

  Chart version `1.20.0` MUST be pinned in `versions.sh` as `WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN` (app version: Airflow 3.1.8 — the latest chart release supporting the 3.1 line, matching the Airflow version available in STACKIT Managed Workflows). Decision by PR #316 comment 2026-05-20.

- FR-009 `infra/gitops/argocd/optional/local/workflows.yaml` MUST be replaced with an ArgoCD `Application` manifest (not a `ConfigMap` stub) that sources the `apache-airflow/airflow` chart from `https://airflow.apache.org` with the pinned chart version and references `infra/local/helm/workflows/airflow.values.yaml`.

- FR-010 `infra/gitops/argocd/overlays/local/appproject.yaml` MUST include `https://airflow.apache.org` in `sourceRepos`. `scripts/lib/infra/module_execution.sh` MUST add a `local-workflows:plan | local-workflows:apply | local-workflows:deploy | local-workflows:destroy` dispatch case returning `argocd_optional_manifest`.

- FR-011 `scripts/bin/blueprint/render_makefile.sh` MUST register the `local-workflows` module section with targets `infra-local-workflows-plan`, `infra-local-workflows-apply`, `infra-local-workflows-deploy`, `infra-local-workflows-smoke`, `infra-local-workflows-destroy` mapped to the corresponding `local_workflows_*.sh` scripts.

- FR-012 `scripts/lib/quality/test_pyramid_contract.json` MUST register `tests/infra/modules/workflows/test_local_contract.py` under the `unit` scope. The test file MUST contain ≥ 10 static-analysis assertions (source-reading only; no subprocess execution).

  Airflow OIDC wiring: `webserverConfig.py` override in Helm values (Option A) — Airflow-native Flask-AppBuilder OIDC; no extra pod or IAP module dependency. `airflow.values.yaml` MUST include a `webserver.webserverConfig` block referencing `WORKFLOWS_LOCAL_OIDC_ISSUER_URL`, `WORKFLOWS_LOCAL_OIDC_CLIENT_ID`, and `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET`. Decision by PR #316 comment 2026-05-20.

- FR-013 `blueprint/modules/local-workflows/module.contract.yaml` MUST define the `local-workflows` module contract with `enable_flag: WORKFLOWS_LOCAL_ENABLED`, `make_targets`, `inputs.required_env`, and `outputs.produced`.

- FR-014 `docs/platform/modules/workflows/README.md` MUST be updated with a Local Lane section documenting `WORKFLOWS_LOCAL_ENABLED`, required env vars, make targets, DAG git-sync configuration, and Keycloak OIDC wiring.

  OIDC env var scope: new `WORKFLOWS_LOCAL_OIDC_CLIENT_ID / _CLIENT_SECRET / _ISSUER_URL` env vars (Option A) — Airflow requires its own Keycloak confidential client (`airflow-local`) with specific redirect URIs (`http://localhost:8080/*`); reusing realm defaults would mutate a shared client. `require_env_vars` in `workflows_local_init_env()` MUST include all three. Decision by PR #316 comment 2026-05-20.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` and `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET` MUST NOT appear as keys in any `.env` state file (`artifacts/infra/workflows_local_*.env`) or CI log.

- NFR-OPS-001 `WORKFLOWS_LOCAL_ENABLED=false` MUST cause every `infra-local-workflows-*` make target to exit 0 without error, logging a skip message.

- NFR-REL-001 ArgoCD sync retry behavior for the local Airflow Application is covered by the platform ArgoCD defaults in `application-platform-local.yaml`; no custom retry policy is required for this module.

- NFR-A11Y-001 N/A — no UI or frontend changes; this work item adds shell scripts, Helm values, ArgoCD manifests, and contract YAML only.

## Normative Option Decision
- Option A: Add `local-workflows:*` to `module_execution.sh` with `argocd_optional_manifest` driver (consistent with langfuse/neo4j pattern; centralized dispatch).
- Option B: Bypass `module_execution.sh` in local lane scripts and call ArgoCD pattern directly (consistent with how `stackit_workflows_*.sh` bypasses dispatch for the STACKIT lane).
- Selected option: OPTION_A
- Rationale: Centralized dispatch via `module_execution.sh` is the established pattern for ArgoCD-backed local modules (neo4j, langfuse). Option A provides consistent profile-aware routing and allows future profiles to override the driver without changing the scripts. The STACKIT lane uses `api_contract` which has no equivalent in `module_execution.sh`; the local lane has a direct analogue (`argocd_optional_manifest`).

## Contract Changes (Normative)
- Config/Env contract: New `WORKFLOWS_LOCAL_ENABLED` (boolean), `WORKFLOWS_LOCAL_DAGS_REPO_URL` (`.git` suffix required), `WORKFLOWS_LOCAL_DAGS_REPO_BRANCH`, `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN`, `WORKFLOWS_LOCAL_OIDC_ISSUER_URL`, `WORKFLOWS_LOCAL_OIDC_CLIENT_ID`, `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET`, `WORKFLOWS_LOCAL_ADMIN_USERNAME`, `WORKFLOWS_LOCAL_ADMIN_PASSWORD` env vars added to platform env contract.
- API contract: none — local lane uses Helm/ArgoCD; no STACKIT REST API calls.
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: New targets `infra-local-workflows-plan`, `infra-local-workflows-apply`, `infra-local-workflows-deploy`, `infra-local-workflows-smoke`, `infra-local-workflows-destroy` registered via `render_makefile.sh`.
- Docs contract: `docs/platform/modules/workflows/README.md` gains a Local Lane section; `make docs-build && make docs-smoke` MUST exit 0.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 Plan state file `artifacts/infra/workflows_local_plan.env` MUST contain keys `provision_driver=argocd_optional_manifest`, `provision_path`, `public_url`, and `chart_version`.

- AC-002 Apply state file `artifacts/infra/workflows_local_apply.env` MUST contain keys `provision_status=deferred_to_deploy`, `provision_driver`, and `provision_path`.

- AC-003 Deploy state file `artifacts/infra/workflows_local_deploy.env` MUST contain key `provision_status=deployed`.

- AC-004 Smoke state file `artifacts/infra/workflows_local_smoke.env` MUST contain key `status=passed`.

- AC-005 `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` MUST be absent from all `artifacts/infra/workflows_local_*.env` state files.

- AC-006 `infra/local/helm/workflows/airflow.values.yaml` MUST contain `dags.gitSync.enabled: true` (or equivalent git-sync sidecar configuration under the chart's DAGs section).

- AC-007 `infra/gitops/argocd/optional/local/workflows.yaml` MUST be an ArgoCD `Application` resource (not a `ConfigMap`); `kind: Application` MUST be present in the file.

- AC-008 `make infra-validate` MUST exit 0 with `blueprint/modules/local-workflows/module.contract.yaml` present and valid.

- AC-009 `make docs-build && make docs-smoke` MUST exit 0 after README is updated with the Local Lane section.

- AC-010 `test_local_contract.py` MUST register in the test pyramid under `unit` scope and MUST contain ≥ 10 passing assertions.

## Informative Notes (Non-Normative)
- Context: PR #314 added the STACKIT lane for workflows (managed Airflow). This work item adds the local lane so engineers can develop DAGs without cloud access. The existing SDD-C-014 exception recorded in PR #314's spec.md is resolved by this work item.
- Tradeoffs: `LocalExecutor` chosen over `CeleryExecutor` to avoid Redis dependency on Docker Desktop Kubernetes. git-sync sidecar chosen over `hostPath` volume for parity with STACKIT lane DAG loading behavior.
- Clarifications: The parked backlog proposal "Python version split strategy" (coexistence of blueprint tooling Python with Airflow runtime-constrained Python) is deferred — it is a separate concern that does not block the local lane deployment.

## Explicit Exclusions
- Excluded: STACKIT Workflows `WORKFLOWS_ENABLED` make targets are unaffected by this work item.
- Excluded: Python version coexistence strategy (parked proposal — separate work item).
- Excluded: Terraform provider-backed migration for STACKIT lane (parked proposal — separate work item).
- Excluded: CeleryExecutor and KubernetesExecutor support for the local lane — `LocalExecutor` only.
- Excluded: Production-grade Airflow tuning (resource limits, connection pools, autoscaling) — local lane defaults are sized for Docker Desktop Kubernetes only.
