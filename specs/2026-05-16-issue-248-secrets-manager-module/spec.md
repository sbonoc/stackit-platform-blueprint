# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-secrets-manager-module.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: STACKIT Secrets Manager has no local-lane equivalent; the local driver is `noop` by design, consistent with all other STACKIT-only optional modules

## Objective
- Business outcome: Blueprint consumers can provision a STACKIT Secrets Manager instance and obtain ESO-compatible credentials (endpoint, namespace, username/password K8s Secret) through the standard optional-module flow, eliminating manual STACKIT console steps and credential drift.
- Success metric: `make infra-provision MODULE=secrets-manager` succeeds on the STACKIT lane, writes all required state keys, and the smoke check exits 0. `test_contract.py` passes with ≥ 10 assertions.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST implement the following files in `infra/cloud/stackit/terraform/modules/secrets-manager/`: `main.tf` with `stackit_secretsmanager_instance` and `stackit_secretsmanager_user` resources (including `lifecycle { create_before_destroy = true }` on the instance resource), `variables.tf`, `outputs.tf`, and `versions.tf` (declaring the `stackitcloud/stackit` required provider with the pinned version constraint matching all other modules), mirroring the foundation pattern.
- FR-002 MUST implement `infra/cloud/stackit/terraform/modules/secrets-manager/variables.tf` declaring: `stackit_project_id`, `stackit_region`, `secrets_manager_instance_name`, `secrets_manager_user_description`, `secrets_manager_user_write_enabled`, `secrets_manager_acl`.
- FR-003 MUST implement `infra/cloud/stackit/terraform/modules/secrets-manager/outputs.tf` declaring: `instance_id` (from `stackit_secretsmanager_instance.this.instance_id`), `username` (from `stackit_secretsmanager_user.this.username`), `password` (sensitive; from `stackit_secretsmanager_user.this.password`).
- FR-004 MUST add `SECRETS_MANAGER_NAMESPACE` and `SECRETS_MANAGER_AUTH_METHOD_DETAILS` to `blueprint/modules/secrets-manager/module.contract.yaml` under `outputs.produced`.
- FR-005 MUST implement `secrets_manager_namespace()` in `scripts/lib/infra/secrets_manager.sh` returning `"$SECRETS_MANAGER_INSTANCE_NAME"` (the namespace equals the instance name per STACKIT SM URL structure).
- FR-006 MUST implement `secrets_manager_auth_method_details()` in `scripts/lib/infra/secrets_manager.sh` returning the username (non-sensitive string) from the runtime state file.
- FR-007 MUST implement both `secrets_manager_reconcile_runtime_secret()` and `secrets_manager_delete_runtime_secret()` in `scripts/lib/infra/secrets_manager.sh`, following the pattern of all credential-bearing modules. `reconcile_runtime_secret()` writes a K8s Secret named `blueprint-secrets-manager-auth` containing the username and password. `delete_runtime_secret()` removes the K8s Secret on destroy.
- FR-008 MUST update `scripts/bin/infra/secrets_manager_apply.sh` to: call `secrets_manager_reconcile_runtime_secret()` after the provision step; write `namespace` and `auth_method_details` keys to the state file.
- FR-009 MUST update `scripts/bin/infra/secrets_manager_plan.sh` to write `namespace` to the state file output (dry-run safe).
- FR-010 MUST update `scripts/bin/infra/secrets_manager_smoke.sh` to add non-empty existence checks for both `namespace` and `auth_method_details` keys in the runtime state file.
- FR-011 MUST implement `tests/infra/modules/secrets-manager/test_contract.py` with ≥ 10 assertions covering the contract, state structure, smoke logic, and security invariants.
- FR-012 MUST update `scripts/bin/infra/secrets_manager_destroy.sh` to call `secrets_manager_delete_runtime_secret()` so the `blueprint-secrets-manager-auth` K8s Secret is removed on destroy, consistent with all credential-bearing modules.
- FR-013 MUST add `tests/infra/modules/secrets-manager/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope before creating the test file, so the pre-commit pyramid gate does not block the commit.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST ensure the password value NEVER appears in the state file (`artifacts/infra/secrets_manager_runtime.env`), CI logs, or any non-sensitive artifact. `auth_method_details` MUST contain only the username (non-sensitive). The password MUST be delivered exclusively via the `blueprint-secrets-manager-auth` K8s Secret through `secrets_manager_reconcile_runtime_secret()`.
- NFR-OBS-001 MUST ensure `namespace` and `auth_method_details` are present in the runtime state artifact and that `secrets_manager_smoke.sh` validates both `namespace` and `auth_method_details` keys are non-empty. All script output MUST be prefixed with `[secrets-manager]`.
- NFR-REL-001 MUST include `lifecycle { create_before_destroy = true }` on `stackit_secretsmanager_instance.this` to minimise downtime during instance replacement.
- NFR-OPS-001 MUST write `namespace` and `auth_method_details` to the runtime state file so operators can derive the ESO SecretStore endpoint and credential lookup without manual console access.
- NFR-A11Y-001 N/A — no UI or frontend changes in this work item.

## Normative Option Decision

### Option Decision 1: STACKIT SM instance `plan_name` attribute

- Option A: Omit `plan_name` from `stackit_secretsmanager_instance.this` — consistent with the foundation pattern which has no `plan_name` on this resource.
- Option B: Add `plan_name` as a variable and resource attribute.
- Selected option: OPTION_A
- Rationale: The `stackit_secretsmanager_instance` STACKIT Terraform resource does not support a `plan_name` attribute (confirmed from foundation `main.tf` and STACKIT provider source). Adding it would cause a Terraform validation error.

### Option Decision 2: `SECRETS_MANAGER_NAMESPACE` value source

- Option A: Namespace equals `SECRETS_MANAGER_INSTANCE_NAME` — derived from STACKIT SM URL structure (`https://secrets.{region}.onstackit.cloud/{instance_name}`).
- Option B: Expose `instance_id` as namespace.
- Selected option: OPTION_A
- Rationale: The STACKIT SM Vault-compatible API uses the instance name as the namespace path component in the URL. Using `instance_name` directly is consistent with the endpoint already computed in `secrets_manager_endpoint()` and requires no additional Terraform output.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/modules/secrets-manager/module.contract.yaml` — add `SECRETS_MANAGER_NAMESPACE` and `SECRETS_MANAGER_AUTH_METHOD_DETAILS` to `outputs.produced`
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — no new Make targets; `infra-provision MODULE=secrets-manager` already exists
- Docs contract: module documentation updated to reflect new outputs and K8s Secret

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `infra/cloud/stackit/terraform/modules/secrets-manager/main.tf` declares `stackit_secretsmanager_instance.this` with `project_id`, `name`, `acls`, and `lifecycle { create_before_destroy = true }`.
- AC-002 `infra/cloud/stackit/terraform/modules/secrets-manager/main.tf` declares `stackit_secretsmanager_user.this` with `project_id`, `instance_id`, `description`, `write_enabled`.
- AC-003 `infra/cloud/stackit/terraform/modules/secrets-manager/variables.tf` declares all six required variables: `stackit_project_id`, `stackit_region`, `secrets_manager_instance_name`, `secrets_manager_user_description`, `secrets_manager_user_write_enabled`, `secrets_manager_acl`.
- AC-004 `infra/cloud/stackit/terraform/modules/secrets-manager/outputs.tf` declares `instance_id`, `username`, and `password` (sensitive).
- AC-004b `infra/cloud/stackit/terraform/modules/secrets-manager/versions.tf` exists and declares the `stackitcloud/stackit` required provider with the pinned version constraint (`= 0.88.0` or the current pinned version used by all other modules).
- AC-005 `blueprint/modules/secrets-manager/module.contract.yaml` includes `SECRETS_MANAGER_NAMESPACE` and `SECRETS_MANAGER_AUTH_METHOD_DETAILS` under `outputs.produced`.
- AC-006 `secrets_manager_namespace()` returns `"$SECRETS_MANAGER_INSTANCE_NAME"` when called with a valid env.
- AC-007 `secrets_manager_auth_method_details()` returns the username string from the runtime state (non-sensitive).
- AC-008 Both `secrets_manager_reconcile_runtime_secret()` and `secrets_manager_delete_runtime_secret()` exist in `secrets_manager.sh`. The former writes a K8s Secret named `blueprint-secrets-manager-auth`; the latter removes it.
- AC-009 `secrets_manager_apply.sh` writes `namespace` and `auth_method_details` to the state file and calls `secrets_manager_reconcile_runtime_secret()`.
- AC-010 `secrets_manager_plan.sh` writes `namespace` to the plan state output.
- AC-011 `secrets_manager_smoke.sh` exits non-zero if `namespace` or `auth_method_details` is absent or empty in the runtime state file.
- AC-012 The runtime state file (`artifacts/infra/secrets_manager_runtime.env`) MUST NOT contain the password value at any point (NFR-SEC-001).
- AC-013 `tests/infra/modules/secrets-manager/test_contract.py` passes with ≥ 10 assertions, all green.
- AC-014 `scripts/bin/infra/secrets_manager_destroy.sh` calls `secrets_manager_delete_runtime_secret()` to remove the `blueprint-secrets-manager-auth` K8s Secret on destroy.
- AC-015 `tests/infra/modules/secrets-manager/test_contract.py` has an entry in `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope.

## Informative Notes (Non-Normative)
- Context: This is one of 6 remaining stub modules under issue #248. The other 5 (dns, public-endpoints, observability, workflows, identity-aware-proxy) will be implemented in separate work items. All are STACKIT-only (local lane = noop).
- Tradeoffs: The standalone TF module provides isolated provisioning capability. The foundation layer continues to manage its own inline resources. The execution driver routing (`foundation_contract` for STACKIT, `noop` for local) is unchanged.
- Clarifications: The `secrets_manager_reconcile_runtime_secret()` function follows the same pattern as `rabbitmq_reconcile_runtime_secret()` and other modules — it uses the shared `reconcile_runtime_secret()` helper from `scripts/lib/infra/runtime_secret.sh` (or equivalent shared lib), writing the password to a K8s Secret only. No password in env files or logs.

## Explicit Exclusions
- DNS, public-endpoints, observability, workflows, and identity-aware-proxy modules — separate work items.
- Local-lane Helm chart for secrets-manager — STACKIT-only module; local lane remains `noop`.
- Consumer-side ESO SecretStore configuration — out of scope; only the credential material (K8s Secret) is delivered.
- Foundation Terraform refactoring — the foundation layer is unchanged; only the standalone module is implemented.
