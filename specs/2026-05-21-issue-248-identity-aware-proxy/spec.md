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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-identity-aware-proxy.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-013 — identity-aware-proxy uses `oauth2-proxy/oauth2-proxy` Helm chart rather than a STACKIT managed service. No STACKIT-managed browser OIDC proxy exists; the Keycloak dependency is the STACKIT-managed identity layer. This is consistent with the pattern used by the `local-workflows` (Airflow), `langfuse`, and `neo4j` modules.

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: n/a — documentation-only deliverable; no new test automation scope
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: oauth2-proxy (CNCF project) is the de-facto standard reverse-proxy for OIDC browser session management on Kubernetes. STACKIT does not offer a managed equivalent. The OIDC identity provider (Keycloak) is STACKIT-managed.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none — module supports both local (Helm) and STACKIT (ArgoCD) lanes

## Module Enablement

- **Feature toggle:** `IDENTITY_AWARE_PROXY_ENABLED` (type: boolean, default: `false`)
- **Declared in:** `blueprint/modules/identity-aware-proxy/module.contract.yaml`
- **Runtime guard:** all 5 lifecycle scripts exit 0 without side effects when `IDENTITY_AWARE_PROXY_ENABLED=false`
- **GitOps convention:** `stackit-*` manifests live under `infra/gitops/argocd/optional/${ENV}/identity-aware-proxy.yaml`
- **To enable:** set `IDENTITY_AWARE_PROXY_ENABLED=true` in the environment profile and export all required inputs

## Objective

- Business outcome: Blueprint consumers have a complete, accurate reference for deploying `oauth2-proxy` as a browser-facing identity-aware proxy wired to Keycloak OIDC. The module was implemented in pre-SDD commits; this work item supplies the SDD compliance layer — README environment-variable table, make-target descriptions, provisioning lifecycle steps, security contract documentation, teardown guide, and bootstrap template mirror — closing the last remaining module under issue #248.
- Success metric: `make quality-hooks-fast` and `make quality-docs-check-changed` both exit 0 on the updated branch. The live README contains all required sections. The bootstrap template mirror is consistent with the live README.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST add an **Environment Variables** table to `docs/platform/modules/identity-aware-proxy/README.md` listing all required inputs (`IAP_UPSTREAM_URL`, `IAP_COOKIE_SECRET`, `KEYCLOAK_ISSUER_URL`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`) and all optional inputs (`IAP_PUBLIC_HOST`, `IAP_NAMESPACE`, `IAP_HELM_RELEASE`, `IAP_HELM_CHART`, `IAP_HELM_CHART_VERSION`, `PUBLIC_ENDPOINTS_NAMESPACE`, `PUBLIC_ENDPOINTS_GATEWAY_NAME`) with their defaults and descriptions.
- FR-002 MUST add a **Make Targets** table to the README documenting all five lifecycle targets (`infra-identity-aware-proxy-plan`, `infra-identity-aware-proxy-apply`, `infra-identity-aware-proxy-deploy`, `infra-identity-aware-proxy-smoke`, `infra-identity-aware-proxy-destroy`) with one-line descriptions derived from each script's actual behavior.
- FR-003 MUST add a **Provisioning Lifecycle** section to the README with step-by-step commands: (a) enable the module flag; (b) create the Keycloak OIDC client with redirect URL `https://${IAP_PUBLIC_HOST}/oauth2/callback`; (c) export all required env vars; (d) run the make lifecycle in order (plan → apply → deploy → smoke).
- FR-004 MUST add a **Security** section documenting: (a) `IAP_COOKIE_SECRET` MUST be a raw 16, 24, or 32 byte string (validated at plan time; any other length is a hard failure); (b) `KEYCLOAK_CLIENT_SECRET` and `IAP_COOKIE_SECRET` SHALL NEVER be written to any state file or log output; (c) on the local lane, credentials are delivered via Kubernetes Secret `${IAP_HELM_RELEASE}-config` in `${IAP_NAMESPACE}`; (d) on the STACKIT lane, credentials are delivered via ESO-issued `security/iap-runtime-credentials` Secret.
- FR-005 MUST add a **Teardown** section documenting `make infra-identity-aware-proxy-destroy` and enumerating what the destroy script removes: the ArgoCD Application or Helm release (profile-dependent), the Kubernetes credential Secret, and all `identity_aware_proxy_*` state files.
- FR-006 MUST mirror all new and updated README sections to `scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md` so consumer-bootstrapped projects receive an identical reference.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST NOT write `IAP_COOKIE_SECRET` or `KEYCLOAK_CLIENT_SECRET` to any state file or log output. The Security section MUST document this contract explicitly. Verification: grep state file keys in the plan and smoke scripts; neither secret key appears.
- NFR-A11Y-001 N/A — no UI or frontend changes in this work item.
- NFR-OBS-001 N/A — no new observability surfaces introduced. All lifecycle scripts already emit metric telemetry via `start_script_metric_trap`.
- NFR-REL-001 MUST confirm that `IDENTITY_AWARE_PROXY_ENABLED=false` exits 0 without side effects on all five lifecycle scripts. Pre-existing behavior; AC-007 provides explicit skip-path coverage.
- NFR-OPS-001 MUST document the state file key contract in the Make Targets table: plan writes `provision_driver`, `provision_path`, `public_host`, `public_url`, `upstream_url`, `gateway_name`, `gateway_namespace`, `keycloak_issuer`, `keycloak_client_id`; apply writes `identity_aware_proxy_runtime` adding `provision_status`, `auth_mode=browser_oidc_proxy`, `route_mode=gateway_api`; smoke writes `status=passed`.

## Normative Option Decision
- Option A: Full README rewrite using the public-endpoints module README as the structural template.
- Option B: Incremental patch — add only the missing sections, preserving existing prose.
- Selected option: OPTION_B — the existing Stack Execution Model, Optional Inputs, and OIDC Contract sections contain accurate, non-redundant content and MUST be preserved. Only the missing sections (env var table, make targets table, lifecycle, security, teardown) are added.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `make quality-hooks-fast` exits 0 after all changes (docs lint, bootstrap drift check, shellcheck, SDD check all pass).
- AC-002 `make quality-docs-check-changed` exits 0: the bootstrap template at `scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md` is in sync with the live README.
- AC-003 `docs/platform/modules/identity-aware-proxy/README.md` contains an **Environment Variables** table with columns Variable / Required / Default / Description, listing all 5 required and at least 7 optional inputs.
- AC-004 The README contains a **Make Targets** table with all 5 lifecycle targets and their one-line descriptions.
- AC-005 The README contains a **Provisioning Lifecycle** section with the Keycloak client prerequisite step, env var export block, and the four make commands in order.
- AC-006 The README contains a **Security** section documenting the `IAP_COOKIE_SECRET` 16/24/32-byte constraint and the non-persistence of `KEYCLOAK_CLIENT_SECRET` in state files.
- AC-007 The README contains a **Teardown** section with `make infra-identity-aware-proxy-destroy` and a list of what is removed.
- AC-008 `IDENTITY_AWARE_PROXY_ENABLED=false make infra-identity-aware-proxy-plan` exits 0 without side effects.
- AC-009 `IDENTITY_AWARE_PROXY_ENABLED=false make infra-identity-aware-proxy-smoke` exits 0 without side effects.

## Informative Notes (Non-Normative)
- Context: This is a retroactive SDD compliance PR for the last remaining module under issue #248. The implementation was built in pre-SDD commits; the sole deliverable is documentation and spec artifacts.
- Tradeoffs: OPTION_B (incremental patch) was selected to preserve accurate existing prose in the Stack Execution Model and OIDC Contract sections. A full rewrite would enforce a standard section order but would rewrite correct content for no functional gain.
- Clarifications: The `infra/cloud/stackit/terraform/modules/identity-aware-proxy/main.tf` is intentionally a stub — IAP is Helm/ArgoCD-managed, not provider-backed. The `main.tf` satisfies the module contract path declaration without introducing a TF resource.

## Explicit Exclusions
- No new IAP features, Keycloak realm automation, ArgoCD manifest changes, or Terraform resources.
- Automated test contract for `tests/infra/modules/identity-aware-proxy/` is out of scope (the test README placeholder is pre-existing; full test contract is deferred).
