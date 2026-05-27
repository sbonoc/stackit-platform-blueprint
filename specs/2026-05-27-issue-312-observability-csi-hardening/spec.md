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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-312-observability-csi-hardening.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-012 — no frontend surface. SDD-C-013 — Secrets Store CSI Driver is a CNCF project; STACKIT does not offer a managed equivalent. The OIDC identity provider and the secret store backend (STACKIT Secrets Manager) are STACKIT-managed.

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — no frontend surface
- Test automation profile: pytest (unit assertions on shell scripts and Helm values)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: Secrets Store CSI Driver is a CNCF cluster component; no STACKIT-managed equivalent. STACKIT Secrets Manager (Vault-compatible) is the managed backend.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: Change is STACKIT-lane-only. STACKIT Secrets Manager and the CSI driver have no local-lane equivalent within scope. Local lane retains the existing K8s Secret path.

## Objective
- Business outcome: Eliminate etcd as a credential store for the observability module on STACKIT lanes. Credentials (username, password, push URLs) are fetched directly from STACKIT Secrets Manager at OTC pod start via the Secrets Store CSI Driver and delivered as tmpfs-mounted files — never written to a K8s Secret object. Enables credential rotation without pod restart and full audit trail via Secrets Manager access logs.
- Success metric: After deployment on a STACKIT profile, `kubectl get secret blueprint-observability-auth -n observability` returns "NotFound"; `make infra-observability-smoke` passes; OTC pod writes telemetry to all three STACKIT push URLs; all unit assertions pass.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST install the Secrets Store CSI Driver (Helm chart `secrets-store-csi-driver/secrets-store-csi-driver`) as a cluster-level ArgoCD Application on STACKIT lanes. Installation MUST be part of core STACKIT runtime bootstrap, not the observability module.
- FR-002 MUST configure the Vault provider for the CSI driver so it can authenticate against STACKIT Secrets Manager's Vault-compatible API.
- FR-003 MUST create a `SecretProviderClass` resource in the `observability` namespace that maps STACKIT Secrets Manager secret paths to the five keys consumed at `/etc/otel/secrets`: `username`, `password`, `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL`.
- FR-004 MUST replace the `extraVolumes.secret` block in `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` with a `csi` volume referencing the `SecretProviderClass`. The mount path (`/etc/otel/secrets`) and all OTC `${file:...}` references MUST remain unchanged.
- FR-005 MUST remove the `observability_reconcile_runtime_secret()` call from the STACKIT-profile branch of `scripts/bin/infra/observability_apply.sh`. The function MUST remain in `observability.sh` for the local-lane path and MUST emit a deprecation log when called on a STACKIT profile.
- FR-006 MUST remove the `observability_delete_runtime_secret()` call from the STACKIT-profile branch of `scripts/bin/infra/observability_destroy.sh`. The function MUST remain for the local-lane path.
- FR-007 MUST store the observability credential values in STACKIT Secrets Manager after TF provisioning. The Terraform observability module MUST write `username`, `password`, `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL` to Secrets Manager using the STACKIT Secrets Manager Terraform resources or the Vault Terraform provider pointed at the Secrets Manager endpoint.
- FR-008 MUST update `blueprint/modules/observability/module.contract.yaml` to declare the Secrets Store CSI Driver as a `required_core_capabilities` prerequisite on STACKIT profiles.
- FR-009 MUST update the five affected unit test assertions in `tests/infra/modules/observability/test_contract.py` — removing or rewriting `test_reconcile_runtime_secret_function_exists`, `test_reconcile_targets_blueprint_observability_auth`, `test_apply_calls_reconcile_runtime_secret`, `test_destroy_calls_delete_runtime_secret`, and the `extraVolumes` K8s Secret assertion — to reflect the CSI volume pattern.
- FR-010 MUST add replacement unit assertions confirming: (a) the CSI volume block is present in STACKIT OTC values, (b) the `SecretProviderClass` name is referenced, (c) no `secretName: blueprint-observability-auth` remains in STACKIT values.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST ensure credentials are never written to a K8s Secret object on STACKIT lanes after this change. The `blueprint-observability-auth` Secret MUST NOT exist post-deploy on any STACKIT profile.
- NFR-SEC-002 MUST ensure `OBSERVABILITY_USERNAME` password/credential values are never written to any state file or shell log. The constraint already exists; this NFR confirms it is preserved after removing the reconcile function call.
- NFR-SEC-003 MUST ensure the `SecretProviderClass` is namespace-scoped to `observability`. No cross-namespace secret access is permitted.
- NFR-OBS-001 Credential reads from STACKIT Secrets Manager MUST be auditable via Secrets Manager access logs. The audit trail is a primary motivator for this change; no additional in-repo instrumentation is required.
- NFR-REL-001 CSI driver mount failure MUST prevent OTC pod start (Kubernetes default behaviour for required CSI volumes — no additional configuration needed). Document this fail-safe explicitly in the README.
- NFR-OPS-001 Credential rotation MUST be achievable without OTC pod restart by updating the secret value in STACKIT Secrets Manager and relying on the CSI driver's rotation polling interval. Document the rotation procedure in `docs/platform/modules/observability/README.md`.
- NFR-A11Y-001 N/A — no UI surfaces introduced or modified.

## Normative Option Decision

- Selected option: **Option A — STACKIT Secrets Manager + Vault provider**. STACKIT Secrets Manager exposes a Vault-compatible API; the CSI driver's Vault provider connects to it directly. Credentials are written to Secrets Manager by Terraform after the observability instance is provisioned using the Vault Terraform provider. No new STACKIT service is introduced — Secrets Manager is already a blueprint module. Decision confirmed by @sbonoc (PR #329 comment, 2026-05-27).

## Contract Changes (Normative)
- Config/Env contract: No new env vars introduced. `OBSERVABILITY_ENABLED` toggle unchanged. New implicit prerequisite: `SECRETS_MANAGER_ENABLED=true` on STACKIT profiles when `OBSERVABILITY_ENABLED=true`.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `make infra-observability-apply` on STACKIT profiles no longer creates the `blueprint-observability-auth` K8s Secret. `make infra-observability-destroy` no longer deletes it. This is a breaking change for any consumer that depends on the Secret object existing post-apply.
- Docs contract: `docs/platform/modules/observability/README.md` MUST be updated to document the CSI driver prerequisite, credential rotation procedure, and removal of the K8s Secret lifecycle.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: after `make infra-observability-deploy` on a STACKIT profile, `kubectl get secret blueprint-observability-auth -n observability` returns error "not found".
- AC-002 MUST: OTC pod starts successfully and the `/etc/otel/secrets/` tmpfs mount contains all five credential files (`username`, `password`, `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL`).
- AC-003 MUST: `make infra-observability-smoke` passes on a STACKIT profile with the CSI-backed configuration.
- AC-004 MUST: `python3 -m pytest tests/infra/modules/observability/ -x -q` passes with updated assertions — no references to `blueprint-observability-auth` as a K8s Secret in the STACKIT values, and CSI volume block assertions present.
- AC-005 MUST: Local-lane (`local-full`, `local-minimal`) `make infra-observability-apply` behaviour is unchanged — `blueprint-observability-auth` K8s Secret is still created and the smoke passes.

## Informative Notes (Non-Normative)
- Context: PR #308 introduced the projected volume mount pattern as an interim hardening step. This work item closes the remaining gap by removing the K8s Secret from the credential delivery path entirely on STACKIT lanes.
- Context: The STACKIT Secrets Manager Terraform provider resources (`stackit_secretsmanager_instance`, `stackit_secretsmanager_user`) are already wired in the blueprint foundation TF. Writing secret values requires the Vault Terraform provider (pointed at the Secrets Manager Vault-compatible API) or a `null_resource` with a local-exec provisioner calling the Secrets Manager API. The preferred approach is the Vault provider.
- Tradeoffs: The CSI driver adds a cluster-level dependency. If the driver is unavailable, the OTC pod will not start. This is the desired fail-safe behaviour (NFR-REL-001), but operators must ensure the driver is running before deploying the observability module.
- Tradeoffs: Credential rotation with the CSI driver is asynchronous — the driver polls for changes on a configurable interval (default 2 minutes). Immediate rotation requires a pod restart.

## Explicit Exclusions
- Local-lane credential delivery — local lane retains the K8s Secret path; CSI driver on Docker Desktop is out of scope.
- KMS-based credential encryption at rest inside Secrets Manager — envelope encryption of stored secrets is a Secrets Manager configuration concern, not a blueprint module concern.
- Rotation automation (automated trigger on credential expiry) — manual rotation procedure is documented; automated rotation trigger is parked.
- ESO `ExternalSecret` for the observability credential — ESO still creates a K8s Secret object, defeating the purpose; CSI driver is the correct approach.
