# ADR: Issue #248 — Secrets Manager Module Implementation (STACKIT-Only)

- **Status**: approved
- **ADR technical decision sign-off**: approved
- **Date**: 2026-05-16
- **Issue**: #248
- **Work item**: `specs/2026-05-16-issue-248-secrets-manager-module/`

## Context

The `infra/cloud/stackit/terraform/modules/secrets-manager/main.tf` is a 7-line stub (no provider resources declared). The shell orchestration layer (`secrets_manager.sh`, `secrets_manager_apply.sh`, `secrets_manager_plan.sh`, `secrets_manager_smoke.sh`) is missing:

1. A standalone Terraform module with `stackit_secretsmanager_instance` and `stackit_secretsmanager_user` resources.
2. Two contract outputs: `SECRETS_MANAGER_NAMESPACE` and `SECRETS_MANAGER_AUTH_METHOD_DETAILS`.
3. A `reconcile_runtime_secret` call to deliver the password via a K8s Secret (`blueprint-secrets-manager-auth`).
4. Smoke validation for the new state keys.
5. Automated test coverage (`test_contract.py` with ≥ 10 assertions).

Unlike rabbitmq, opensearch, and postgres, STACKIT Secrets Manager has no local-lane equivalent. The local driver is `noop` by design, consistent with other STACKIT-only modules (e.g., kms, object-storage).

## Decisions

### D-1: Standalone Terraform module mirroring the foundation pattern (no `plan_name`)

Implement `infra/cloud/stackit/terraform/modules/secrets-manager/` with `stackit_secretsmanager_instance.this` and `stackit_secretsmanager_user.this`, mirroring the foundation pattern in `infra/cloud/stackit/terraform/foundation/main.tf`. The `stackit_secretsmanager_instance` resource does NOT support a `plan_name` attribute (confirmed from foundation usage and STACKIT provider source). The `lifecycle { create_before_destroy = true }` block is included on the instance resource to minimise downtime during replacement.

The foundation layer retains its own inline resources unchanged. The standalone module is for isolated provisioning only.

**Rejected alternative:** Add `plan_name` as a variable and resource attribute — rejected because the `stackit_secretsmanager_instance` resource does not expose this attribute; doing so would cause a Terraform validation error.

### D-2: `SECRETS_MANAGER_NAMESPACE` = instance name (derived from STACKIT SM URL structure)

The STACKIT Secrets Manager Vault-compatible API URL has the form `https://secrets.{region}.onstackit.cloud/{instance_name}`. The namespace path component is the instance name. `secrets_manager_namespace()` returns `"$SECRETS_MANAGER_INSTANCE_NAME"` directly — no additional Terraform output is needed, and the value is already present in the env at runtime.

**Rejected alternative:** Use `instance_id` as the namespace — rejected because the STACKIT SM URL uses the human-readable instance name, not the UUID; using the UUID would break ESO SecretStore configuration.

### D-3: `SECRETS_MANAGER_AUTH_METHOD_DETAILS` = username only (password via K8s Secret)

`auth_method_details` in the state file contains only the non-sensitive username string. The password is never written to the state file, CI logs, or any non-sensitive artifact. It is delivered exclusively via `secrets_manager_reconcile_runtime_secret()` which writes a K8s Secret named `blueprint-secrets-manager-auth` using the shared `reconcile_runtime_secret()` helper pattern (consistent with rabbitmq, opensearch, postgres modules).

This satisfies NFR-SEC-001: password-in-state-file is an explicit security exclusion.

**Rejected alternative:** Include password hash or masked password in `auth_method_details` — rejected; any password representation in the state file violates NFR-SEC-001 and creates audit risk.

### D-4: Execution driver routing unchanged (`foundation_contract` / `noop`)

The `module_execution.sh` routing for `secrets-manager` remains:
- STACKIT lane: `foundation_contract` (plan/apply), `foundation_reconcile_apply` (destroy)
- Local lane: `noop`

No new driver type is needed. The standalone TF module files implement the provisioning capability; the execution routing continues through the foundation contract.

**Rejected alternative:** Route the standalone module directly (bypass foundation contract) — rejected because no active consumer needs this and introducing a new driver type adds complexity without benefit in this work item scope.

## Consequences

- STACKIT standalone Terraform module enables isolated Secrets Manager provisioning outside the foundation deployment pattern.
- `SECRETS_MANAGER_NAMESPACE` is consistently the instance name on the STACKIT lane; the local (noop) lane produces an empty/placeholder value.
- `SECRETS_MANAGER_AUTH_METHOD_DETAILS` exposes the username for ESO SecretStore reference; the password is available only via `blueprint-secrets-manager-auth` K8s Secret.
- Module contract gains two new outputs — additive, no breaking change to existing consumers.
- Runtime state file gains `namespace` and `auth_method_details` keys — additive, fully backward compatible.
- Password is never in any state artifact — security posture matches all other credential-bearing modules.
