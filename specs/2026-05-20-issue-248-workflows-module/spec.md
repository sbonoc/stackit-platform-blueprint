# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-workflows-module.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015
- Control exception rationale: SDD-C-014 (local-first runtime baseline) — STACKIT Workflows is a cloud-only managed service (Apache Airflow) with no viable local equivalent at this time; local lane is explicitly skipped by design per issue #248 requirements table. Exception recorded here and in AGENTS.decisions.md as part of this work item.

## Implementation Stack Profile (Normative)
- Backend stack profile: bash_shell_contract
- Frontend stack profile: none
- Test automation profile: pytest_unit
- Managed service: STACKIT Workflows (managed Apache Airflow) — provisioned via `https://workflows.api.stackit.cloud/v1alpha` REST API (no Terraform provider resource available as of v0.96.0 latest)
- Local-first baseline: STACKIT-lane only; no local lane — see SDD-C-014 exception above
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: STACKIT Workflows is a cloud-only managed Apache Airflow service; no local lane equivalent is provided. The REST API contract pattern is used as the bridge until a Terraform provider resource becomes available.
- Runtime profile: stackit-managed-runtime
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: STACKIT Workflows is a cloud-only managed service with no viable local equivalent. SDD-C-014 exception recorded in spec.md and AGENTS.decisions.md. Local Airflow via Helm chart is a plausible future extension tracked separately.

## Module Enablement
- **Feature toggle:** `WORKFLOWS_ENABLED` (type: boolean, default: `false`)
- **Declared in:** `blueprint/modules/workflows/module.contract.yaml` — `enable_flag: WORKFLOWS_ENABLED`
- **Runtime guard:** all `stackit_workflows_*.sh` scripts exit early when `WORKFLOWS_ENABLED=false`; `workflows_init_env()` calls `log_fatal` if `BLUEPRINT_PROFILE` is not a `stackit-*` profile
- **GitOps convention:** metadata ConfigMap lives at `infra/gitops/argocd/optional/${ENV}/workflows.yaml`; no ArgoCD Application is deployed because the workflows instance is API-provisioned (not Helm-deployed)
- **TF guard:** `infra/cloud/stackit/terraform/modules/workflows/main.tf` is a stub only — no STACKIT Terraform provider resource exists for Workflows as of provider v0.96.0; provisioning uses the REST API contract
- **To enable:** set `WORKFLOWS_ENABLED=true` in the environment profile before running `make infra-stackit-workflows-plan && make infra-stackit-workflows-apply`

## Objective
- Business outcome: Blueprint consumers can provision a STACKIT Workflows (managed Apache Airflow) instance on the STACKIT lane, configure Keycloak OIDC authentication, deploy DAGs from a git repository, and smoke-validate the deployment. The module contract exposes `STACKIT_WORKFLOWS_INSTANCE_FQDN`, `STACKIT_WORKFLOWS_WEB_URL`, and `STACKIT_WORKFLOWS_HEALTH_STATUS` so consumers can integrate Airflow into their platform tooling without reimplementing STACKIT API client logic.
- Success metric: `make infra-stackit-workflows-apply` succeeds on the STACKIT lane, writes all required state keys, Keycloak OIDC client is reconciled, DAGs are deployed, and `make infra-stackit-workflows-smoke` exits 0. `test_contract.py` passes with ≥ 15 assertions. `make infra-validate` exits 0.

## Open Questions

> **[Q-1 — resolved 2026-05-20, PR #314]** STACKIT Terraform provider upgrade v0.88.0 → v0.96.0.
>
> **Decision: Option A (defer).** Provider upgrade is a cross-cutting concern affecting all foundation TF resources; dedicated work item required. No functional impact for this PR since workflows uses the REST API contract, not TF. Recorded in `AGENTS.backlog.md` (STACKIT platform expansion) and `ADR-issue-248-workflows-module.md`.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST ensure `WORKFLOWS_ENABLED` is the sole feature toggle for all workflows make targets; all `stackit_workflows_*.sh` scripts MUST exit 0 immediately when `WORKFLOWS_ENABLED=false` and MUST call `log_fatal` when invoked on a non-STACKIT profile.
- FR-002 MUST ensure `workflows_init_env()` in `scripts/lib/infra/workflows.sh` validates all required env vars (`STACKIT_PROJECT_ID`, `STACKIT_REGION`, `STACKIT_WORKFLOWS_DAGS_REPO_URL`, `STACKIT_WORKFLOWS_DAGS_REPO_BRANCH`, `STACKIT_WORKFLOWS_DAGS_REPO_USERNAME`, `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN`, `STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL`, `STACKIT_WORKFLOWS_OIDC_CLIENT_ID`, `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET`, `STACKIT_OBSERVABILITY_INSTANCE_ID`) and MUST call `log_fatal` if `STACKIT_WORKFLOWS_DAGS_REPO_URL` does not end with `.git`.
- FR-003 MUST ensure `workflows_payload_json()` generates a valid JSON payload for the STACKIT Workflows API `POST /projects/{projectId}/regions/{region}/instances` endpoint containing all required fields: `displayName`, `version`, `dagsRepository.url/branch/auth`, `identityProvider.*`, and `observabilityId`.
- FR-004 MUST ensure `scripts/bin/infra/stackit_workflows_plan.sh` generates the API request payload JSON file and writes a plan state file to `artifacts/infra/workflows_plan.env` containing `provision_driver=api_contract`, `provision_path`, `payload_file`, and `display_name` keys.
- FR-005 MUST ensure `scripts/bin/infra/stackit_workflows_apply.sh` runs Keycloak reconciliation first, then POSTs to the STACKIT Workflows API, handles HTTP 409 (instance already exists) by fetching and resolving the existing instance, and writes an instance state file to `artifacts/infra/workflows_instance.env` containing `instance_id`, `instance_name`, `instance_fqdn`, `web_url`, and `health_status` keys.
- FR-006 MUST ensure `scripts/bin/infra/stackit_workflows_keycloak_reconcile.sh` reconciles a confidential OIDC client in the configured Keycloak realm with roles `Admin,User,Viewer,Op`, redirect URI pattern `https://*.workflows.${STACKIT_REGION}.stackit.cloud/*`, and the resolved instance `web_url` added to redirect URIs once the instance state is available.
- FR-007 MUST ensure `scripts/bin/infra/stackit_workflows_dag_deploy.sh` PATCHes the `/instances/{id}/dags-repository` endpoint with the DAG repository URL, branch, and auth credentials, and writes a deploy state file to `artifacts/infra/workflows_dag_deploy.env` containing `status=synced`, `dags_repo_url`, and `dag_file_count` keys.
- FR-008 MUST ensure `scripts/bin/infra/stackit_workflows_reconcile.sh` counts active instances via the API when `tooling_is_execution_enabled`, calls `log_fatal` when `STACKIT_WORKFLOWS_REQUIRE_SINGLE_ACTIVE_INSTANCE=true` and the count is not exactly 1, and runs `stackit_workflows_keycloak_reconcile.sh` to converge the OIDC client contract.
- FR-009 MUST ensure `scripts/bin/infra/stackit_workflows_destroy.sh` DELETEs the instance via the STACKIT Workflows API (accepting HTTP 200/202/204/404), removes all `workflows_*` state files, and writes a destroy state file.
- FR-010 MUST ensure `scripts/bin/infra/stackit_workflows_dag_parse_smoke.sh` validates that no `*dag*.py` files exist under `apps/` (DAG entrypoints MUST live under repository-root `dags/`) and writes a smoke state file with `status=passed` and `violations=0`.
- FR-011 MUST ensure `scripts/bin/infra/stackit_workflows_smoke.sh` validates the instance `health_status=Active` in the instance state file; when `tooling_is_execution_enabled`, MUST also fetch live instance status from the API, confirm the DAG repository URL and branch match, and call `make infra-stackit-workflows-dag-parse-smoke`. MUST write a smoke state file with `status=passed`.
- FR-012 MUST add `tests/infra/modules/workflows/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope before creating the test file so the pre-commit pyramid gate does not block the commit.
- FR-013 MUST implement `tests/infra/modules/workflows/test_contract.py` with ≥ 15 assertions covering: plan state key structure, apply state key structure, instance state security properties (`STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` absent from state), destroy state structure, DAG parse smoke state structure, smoke state structure, Keycloak reconcile state structure, module contract YAML required inputs and outputs, `workflows_init_env` guard against non-STACKIT profiles, `workflows_default_display_name` length constraint (≤ 16 chars), `workflows_payload_json` required fields, `workflows_api_init_env` env var defaults, and make target registration in `render_makefile.sh`.
- FR-014 MUST update `docs/platform/modules/workflows/README.md` to document: the provisioning flow (plan → apply → dag-deploy → smoke → destroy), the Keycloak OIDC contract, the DAG repository requirements, API contract approach and why TF is not used, state file outputs, troubleshooting guidance, and consumer usage examples.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST ensure `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` and `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET` NEVER appear in any state file (`artifacts/infra/workflows_*.env`), CI log, or non-sensitive artifact. These credentials MUST be consumed only at runtime by the shell scripts and MUST NOT be persisted to disk beyond the scope of the API call.
- NFR-OPS-001 MUST ensure all `stackit_workflows_*.sh` scripts fail fast with `log_fatal` when invoked outside a `stackit-*` profile. No local lane is provided or required for this module.
- NFR-A11Y-001: N/A — no UI or frontend changes in this work item.

## Explicit Exclusions
- Local lane support for STACKIT Workflows — STACKIT Workflows is a cloud-only managed Airflow service; no local equivalent is deployed.
- Terraform provider resource for `stackit_workflows_instance` — no such resource exists in provider v0.96.0 (latest); REST API contract is the intentional approach.
- STACKIT Terraform provider version upgrade from 0.88.0 — separate work item; deferred per Q-1.
- DAG authoring or DAG content — the module wires the DAG repository; DAG content is consumer-owned.
- ArgoCD Application deployment — Workflows is API-provisioned; no Helm chart is deployed; the ArgoCD ConfigMap is metadata-only.

## Normative Acceptance Criteria

- AC-001 MUST verify that after `make infra-stackit-workflows-plan` on STACKIT profile, `artifacts/infra/workflows_plan.env` contains `provision_driver=api_contract` and a valid `payload_file` path.
- AC-002 MUST verify that after `make infra-stackit-workflows-apply` on STACKIT profile, `artifacts/infra/workflows_instance.env` contains non-empty `instance_id`, `instance_fqdn`, `web_url`, and `health_status=Active` keys.
- AC-003 MUST verify that `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` does not appear in any `artifacts/infra/workflows_*.env` state file.
- AC-004 MUST verify that `make infra-stackit-workflows-smoke` exits 0 on STACKIT profile after apply and dag-deploy.
- AC-005 MUST verify that after `make infra-stackit-workflows-destroy`, all `artifacts/infra/workflows_instance.env` and `artifacts/infra/workflows_plan.env` state files are removed.
- AC-006 MUST verify that `artifacts/infra/workflows_keycloak_reconcile.env` contains `realm`, `client_id`, and `redirect_uris` keys after Keycloak reconciliation.
- AC-007 MUST verify that `test_contract.py` passes with ≥ 15 assertions and is registered in `test_pyramid_contract.json` under the `unit` scope.
- AC-008 MUST verify that `make infra-validate` exits 0 (module contract + make target consistency).
- AC-009 MUST verify that `make docs-build && make docs-smoke` exits 0.
- AC-010 MUST verify that `workflows_default_display_name()` returns a string of ≤ 16 characters containing only `a-z0-9-`.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none — REST API contract is the intentional provisioning path, not a workaround
- Replacement trigger: when `stackit_workflows_instance` Terraform provider resource becomes available in a future provider version
- Workaround review date: none

## Informative Notes (Non-Normative)
- Context: The STACKIT Workflows module is substantially implemented — all shell scripts (plan, apply, keycloak-reconcile, dag-deploy, dag-parse-smoke, reconcile, smoke, destroy), API helpers (`workflows.sh`, `workflows_api.sh`), module.contract.yaml, and make targets exist. The missing quality gate items are: automated tests (`test_contract.py`), test pyramid registration, and a complete module README. This spec closes those gaps without changing the existing implementation.
- Tradeoffs: Option A (REST API contract, selected) allows immediate delivery without blocking on TF provider availability. The plan state file (`provision_driver=api_contract`) provides the same auditability as a Terraform plan step. When a TF provider resource becomes available, the apply script can be migrated to a foundation TF module with `provision_driver=terraform_foundation`.
- Clarifications: The `observabilityId` field in the API payload links the Workflows instance to the STACKIT Observability instance for metrics/logs emission. The Keycloak OIDC client reconciliation is a pre-condition to the API create call — the `identityProvider.discoveryEndpoint` and `clientId` must match the Keycloak configuration before the instance is provisioned.

## Sign-off Tracking (Normative)
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
