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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-kms-module.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale:
  - SDD-C-015: No app onboarding make-target contract changes — this work item affects only infra module wrappers, not app delivery workflows.
  - SDD-C-018: No blueprint upstream defect escalation — this is a blueprint-internal implementation.
  - SDD-C-022: Not applicable — no HTTP route handlers or new API endpoints in scope.
  - SDD-C-023: Not applicable — no filter or payload-transform logic in scope.
  - SDD-C-024: Not applicable — no reproducible pre-PR smoke/curl/deterministic-check findings to translate at intake time.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: local lane uses HashiCorp Vault Transit Secrets Engine (dev mode, Helm chart) — provides encryption-as-a-service with identical conceptual operations to STACKIT KMS; this is the established blueprint pattern for local lane provisioning where no STACKIT managed-service equivalent is deployable on docker-desktop.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Elevate the kms module from a partial scaffold (STACKIT-only, local lane is a no-op) to a production-grade optional module with both lanes: a complete STACKIT standalone Terraform module (`stackit_kms_keyring` + `stackit_kms_key` resources), a first-class local lane via HashiCorp Vault Transit Secrets Engine, a new contract output `KMS_ENDPOINT` added to `module.contract.yaml`, updated `kms.sh` shell functions for both lanes, hardened smoke validations, expanded state file, tests, and complete module documentation.
- Success metric: `pytest tests/infra/modules/kms/ -v` passes (≥ 18 assertions); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` passes; local lane state file contains all five contract output keys (`key_ring_id`, `key_id`, `key_ring_name`, `key_name`, `endpoint`); STACKIT Terraform module passes `terraform validate`.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST implement the STACKIT standalone Terraform module at `infra/cloud/stackit/terraform/modules/kms/` with two resources: `stackit_kms_keyring` and `stackit_kms_key`; the module MUST mirror the foundation pattern already in `infra/cloud/stackit/terraform/foundation/main.tf`.
- FR-002 MUST add `KMS_ENDPOINT` to the `outputs.produced` list in `blueprint/modules/kms/module.contract.yaml`, bringing the total produced outputs to five.
- FR-003 MUST add `kms_endpoint()` to `scripts/lib/infra/kms.sh`; on the STACKIT lane it MUST return the STACKIT KMS REST API base URL constructed from the active region (pattern: `https://kms.api.${region}.stackit.cloud`); on the local lane it MUST return the Vault Transit API path `http://blueprint-vault.${KMS_NAMESPACE}.svc.cluster.local:8200/v1/transit`.
- FR-004 MUST add `kms_render_values_file()`, `kms_reconcile_runtime_secret()`, and `kms_enable_vault_transit()` to `scripts/lib/infra/kms.sh` to support the Vault-backed local lane provisioning flow.
- FR-005 MUST update `scripts/bin/infra/kms_apply.sh` to add a `helm` provision driver case that installs the Vault Helm chart, enables the Transit secrets engine, and writes all five contract keys to the runtime state file including `endpoint=$(kms_endpoint)`.
- FR-006 MUST update `scripts/bin/infra/kms_plan.sh` to add a `helm` provision driver case that logs a dry-run note and writes the plan state artifact on the local lane.
- FR-007 MUST update `scripts/bin/infra/kms_destroy.sh` to add a `helm` provision driver case that uninstalls the Vault release and cleans up runtime state files on the local lane.
- FR-008 MUST harden `scripts/bin/infra/kms_smoke.sh`: add explicit non-empty validations for `key_ring_id`, `key_id`, and `endpoint` state file keys in addition to the existing `key_id` presence check.
- FR-009 MUST implement `variables.tf` and `outputs.tf` for the STACKIT standalone Terraform module; `variables.tf` MUST declare all inputs (`stackit_project_id`, `stackit_region`, `kms_key_ring_name`, `kms_key_name`, and all optional inputs from `module.contract.yaml`); `outputs.tf` MUST expose `kms_keyring_id`, `kms_keyring_display_name`, `kms_key_id`, `kms_key_display_name`.
- FR-010 MUST implement `infra/local/helm/kms/values.yaml` with Vault Helm chart values; chart MUST use dev mode (`server.dev.enabled: true`) with a configurable root token; `fullnameOverride` MUST be set to `"blueprint-vault"`; resource limits MUST be ≤ 512 Mi RAM.
- FR-011 MUST update `scripts/lib/infra/module_execution.sh` to change the local-profile driver for `kms:plan`, `kms:apply`, and `kms:destroy` from `noop` to `helm`, pointing at the rendered Vault values file path.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST NOT store the Vault root token in plaintext in `values.yaml` or any rendered artifact; the root token MUST be delivered to consumers via a K8s Secret created by `kms_reconcile_runtime_secret()`; the `kms_render_values_file()` function MUST use `server.dev.devRootToken` sourced from an environment variable, not hardcoded.
- NFR-OBS-001 All four scripts (`kms_{plan,apply,smoke,destroy}.sh`) already emit metric events via `start_script_metric_trap`; no new metric emitters are required.
- NFR-REL-001 The Terraform module MUST include `lifecycle { create_before_destroy = true }` on the `stackit_kms_keyring` resource; STACKIT KMS destroy semantics MUST follow the provider contract (keyrings removed from Terraform state without API deletion; keys scheduled for deletion rather than immediately deleted).
- NFR-OPS-001 The runtime state file MUST contain all five contract output keys (`key_ring_id`, `key_id`, `key_ring_name`, `key_name`, `endpoint`) after apply; `kms_smoke.sh` MUST validate non-empty `key_ring_id`, `key_id`, and `endpoint`.
- NFR-A11Y-001 N/A — no UI component; kms is an infrastructure module with no browser-facing surface.

## Normative Option Decisions

Q-1 resolved: `KMS_INSTANCE_NAME` in issue #248 maps to the existing `KMS_KEY_RING_NAME` contract input — Decision at intake 2026-05-07.

STACKIT KMS uses a keyring/key model (`stackit_kms_keyring` + `stackit_kms_key` Terraform resources). The issue used "instance" as a generic abstraction, but the concrete STACKIT provider API uses "keyring" terminology. The existing `module.contract.yaml` with `KMS_KEY_RING_NAME` + `KMS_KEY_NAME` correctly maps to the STACKIT provider resources and MUST remain the canonical input contract.

- Option A: Rename `KMS_KEY_RING_NAME` → `KMS_INSTANCE_NAME` to match issue wording.
- Option B: Keep existing `KMS_KEY_RING_NAME` + `KMS_KEY_NAME` contract inputs; document that they correspond to the issue's `KMS_INSTANCE_NAME` concept.
- Selected option: OPTION_B
- Rationale: The STACKIT provider exposes `stackit_kms_keyring` (not "instance"). Renaming to `KMS_INSTANCE_NAME` would obscure the provider model, break the established naming convention, and require a breaking change to an already-distributed contract. The existing naming is correct and MUST remain. Decision by owner at intake 2026-05-07.

Q-2 resolved: `KMS_KEY_ROTATION_PERIOD` is not supported by `stackit_kms_key` in provider v0.88.0 — out of scope for this work item.

The `stackit_kms_key` resource at provider version 0.88.0 does not expose a `rotation_period` attribute (confirmed from the foundation `main.tf` implementation). Adding this input would create a false contract promise. A follow-up work item will add it if/when the STACKIT provider exposes rotation period support.

- Option A: Add `KMS_KEY_ROTATION_PERIOD` to `module.contract.yaml` as optional input even though the provider ignores it (document as no-op).
- Option B: Omit `KMS_KEY_ROTATION_PERIOD` from this work item; add a backlog entry for when provider support lands.
- Selected option: OPTION_B
- Rationale: Shipping a no-op contract input would mislead consumers into believing rotation is configured. Provider limitation is a documented constraint; backlog entry ensures it surfaces when provider support ships. Decision by owner at intake 2026-05-07.

## Contract Changes (Normative)
- Config/Env contract: `KMS_ENDPOINT` added to `module.contract.yaml` `outputs.produced`; corresponding runtime state file key `endpoint` added to `artifacts/infra/kms_runtime.env`; no existing keys renamed; no consumer-visible env var changes to previously produced outputs.
- API contract: none.
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new make targets; existing `infra-kms-{plan,apply,smoke,destroy}` targets now backed by Vault Helm chart on local profile instead of noop.
- Docs contract: `docs/platform/modules/kms/README.md` updated from generated scaffold to production-grade documentation.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 MUST: Terraform `main.tf` declares `stackit_kms_keyring` and `stackit_kms_key` resources; `stackit_kms_keyring` has `lifecycle { create_before_destroy = true }`.
- AC-002 MUST: `variables.tf` declares `stackit_project_id`, `stackit_region`, `kms_key_ring_name`, `kms_key_name`, and all optional inputs from `module.contract.yaml`.
- AC-003 MUST: `outputs.tf` exposes `kms_keyring_id`, `kms_keyring_display_name`, `kms_key_id`, `kms_key_display_name`.
- AC-004 MUST: `module.contract.yaml` `outputs.produced` includes `KMS_ENDPOINT`.
- AC-005 MUST: `kms_endpoint()` on local lane returns a string containing `vault` and `transit` and port `8200`.
- AC-006 MUST: `kms_apply.sh` `write_state_file` includes `endpoint=$(kms_endpoint)` alongside existing keys.
- AC-007 MUST: `kms_smoke.sh` passes when `key_ring_id`, `key_id`, and `endpoint` are all present and non-empty in the runtime state file.
- AC-008 MUST: `kms_smoke.sh` fails when `key_id` is empty or absent.
- AC-009 MUST: `kms_smoke.sh` fails when `key_ring_id` is empty or absent.
- AC-010 MUST: `kms_smoke.sh` fails when `endpoint` is empty or absent.
- AC-011 MUST: Local lane runtime state fixture contains all five contract output keys: `key_ring_id`, `key_id`, `key_ring_name`, `key_name`, `endpoint`.
- AC-012 MUST: `infra/local/helm/kms/values.yaml` sets `fullnameOverride: "blueprint-vault"` and `server.dev.enabled: true`.
- AC-013 MUST: `kms_plan.sh` `helm` driver case writes a plan state artifact on local profile.
- AC-014 MUST: `module_execution.sh` kms local-profile driver for plan/apply/destroy is `helm`, not `noop`.

## Informative Notes (Non-Normative)
- Context: The kms module previously had STACKIT-only support via the foundation layer and a no-op local lane stub. The foundation pattern already provisions `stackit_kms_keyring` + `stackit_kms_key`; the standalone module mirrors that pattern for teams using module-scoped provisioning. Vault Transit provides cryptographically equivalent envelope-encryption semantics locally (create key, encrypt, decrypt, rotate) without requiring STACKIT credentials on developer machines.
- Tradeoffs: Vault in dev mode uses ephemeral in-memory storage — keys do not persist across pod restarts. This is intentional for local dev; a `destroy` + `apply` cycle recovers the key. The alternative (Vault in standalone mode with raft storage) adds operational complexity disproportionate to local dev needs.
- Clarifications: `KMS_KEY_ROTATION_PERIOD` from issue #248 is deferred because `stackit_kms_key` v0.88.0 does not expose this attribute. A backlog entry tracks this for when provider support ships.

## Explicit Exclusions
- `KMS_KEY_ROTATION_PERIOD` input — provider v0.88.0 does not support; deferred to follow-up work item.
- Vault HA or persistent storage for the local lane — dev-mode ephemeral storage is sufficient for local development.
- Consumer-specific key names, indices, or use cases — module is generic; consumers configure their own key names via `KMS_KEY_NAME`.
- Changes to consumer repositories — out of scope per original prompt.
- `langfuse`, `neo4j` modules — explicitly deferred per issue #248.
