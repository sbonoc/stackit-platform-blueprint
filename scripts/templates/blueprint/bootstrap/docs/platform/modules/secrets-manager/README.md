# Secrets Manager Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed secrets manager capability for runtime secret distribution.
- Enable flag: `SECRETS_MANAGER_ENABLED` (default: `false`)
- Required inputs:
  - `SECRETS_MANAGER_INSTANCE_NAME`
- Make targets:
  - `infra-secrets-manager-plan`
  - `infra-secrets-manager-apply`
  - `infra-secrets-manager-smoke`
  - `infra-secrets-manager-destroy`
- Outputs:
  - `SECRETS_MANAGER_INSTANCE_NAME`
  - `SECRETS_MANAGER_ENDPOINT`
  - `SECRETS_MANAGER_NAMESPACE`
  - `SECRETS_MANAGER_AUTH_METHOD_DETAILS`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Overview

The Secrets Manager module provisions a STACKIT-managed secrets store and delivers runtime credentials to the cluster:

- **Local lane (`local-*` profiles):** no managed counterpart — plan/apply/smoke/destroy are no-op contract stubs that exit 0. No in-cluster service is deployed.
- **STACKIT lane (`stackit-*` profiles):** provisions a `stackit_secretsmanager_instance` and `stackit_secretsmanager_user` via the STACKIT Terraform foundation layer. After provisioning, `infra-secrets-manager-apply` writes the username as `auth_method_details` to the runtime state and delivers the password as a Kubernetes Secret (`blueprint-secrets-manager-auth`). The password never appears in any state file or CI log.

## Stack Execution Model

Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `SECRETS_MANAGER_ENABLED=true`. Scaffolding paths are materialized by `make infra-bootstrap` only when `SECRETS_MANAGER_ENABLED=true`.

| Action | Local (`local-*`) | STACKIT (`stackit-*`) |
|---|---|---|
| `infra-secrets-manager-plan` | No-op stub | Warns missing foundation Terraform diff; writes `namespace` to plan state |
| `infra-secrets-manager-apply` | No-op stub | Applies STACKIT foundation Terraform; writes `namespace` + `auth_method_details` to runtime state; creates `blueprint-secrets-manager-auth` K8s Secret |
| `infra-secrets-manager-smoke` | No-op stub | Validates non-empty `namespace` and `auth_method_details` in runtime state |
| `infra-secrets-manager-destroy` | No-op stub | Removes `blueprint-secrets-manager-auth` K8s Secret; delegates destroy to foundation layer |

## STACKIT Lane

On STACKIT profiles, the foundation Terraform layer provisions:

- `stackit_secretsmanager_instance`: named by `SECRETS_MANAGER_INSTANCE_NAME`, with optional ACL ranges.
- `stackit_secretsmanager_user`: linked to the instance, with write access enabled by default.

`SECRETS_MANAGER_ENDPOINT` resolves to the STACKIT Secrets Manager REST API URL for the active region:

```
https://secrets.<region>.onstackit.cloud/<instance-name>
```

`SECRETS_MANAGER_NAMESPACE` is the STACKIT Secrets Manager namespace, which equals the instance name (the path component of the endpoint URL).

## Runtime State

Apply writes `artifacts/infra/secrets_manager_runtime.env` with the following contract output keys:

| Key | Description |
|---|---|
| `instance_name` | Canonical SM instance name (`SECRETS_MANAGER_INSTANCE_NAME`) |
| `endpoint` | Full STACKIT Secrets Manager API endpoint URL |
| `namespace` | SM namespace (equals instance name; STACKIT URL path component) |
| `auth_method_details` | Runtime username (non-sensitive; STACKIT lane reads foundation TF output) |

State file keys follow the strict prefix-strip convention: `SECRETS_MANAGER_AUTH_METHOD_DETAILS` → `auth_method_details`. Consumers reading `artifacts/infra/secrets_manager_runtime.env` directly must use the stripped key names.

> **Security:** The password is never written to the state file or any runtime artifact. It is delivered exclusively via the `blueprint-secrets-manager-auth` Kubernetes Secret — see [Credentials](#credentials) below.

## Credentials

Credentials are delivered via a Kubernetes Secret named `blueprint-secrets-manager-auth` in namespace `secrets-manager` (controlled by `SECRETS_MANAGER_K8S_NAMESPACE`, default `secrets-manager`).

| Secret key | Value |
|---|---|
| `username` | Runtime username (from STACKIT foundation TF output `secrets_manager_username`) |
| `password` | Runtime password (from STACKIT foundation TF output `secrets_manager_password`) |

**Apply sequence (STACKIT lane):**

1. Foundation Terraform provisions `stackit_secretsmanager_instance` and `stackit_secretsmanager_user`.
2. `secrets_manager_reconcile_runtime_secret()` creates or updates Secret `blueprint-secrets-manager-auth` in namespace `secrets-manager` with the provider-generated username and password.
3. Runtime state is written with `namespace` and `auth_method_details` (username only).

**Destroy sequence (STACKIT lane):**

1. Foundation Terraform layer tears down the STACKIT SM instance.
2. `secrets_manager_delete_runtime_secret()` removes Secret `blueprint-secrets-manager-auth`.
3. Runtime state files are removed.

## Standalone STACKIT Terraform Module

A standalone Terraform module is available at `infra/cloud/stackit/terraform/modules/secrets-manager/` for isolated Secrets Manager provisioning outside the foundation deployment pattern.

Resources declared:
- `stackit_secretsmanager_instance.this` — with `lifecycle { create_before_destroy = true }`
- `stackit_secretsmanager_user.this` — linked to the instance with write access

Key variables:

| Variable | Description | Default |
|---|---|---|
| `stackit_project_id` | STACKIT project ID | required |
| `stackit_region` | STACKIT region | `eu01` |
| `secrets_manager_instance_name` | SM instance name | required |
| `secrets_manager_acl` | List of allowed CIDR ranges; empty disables IP restriction | `[]` |
| `secrets_manager_user_description` | User credential description | `blueprint-managed` |
| `secrets_manager_user_write_enabled` | Whether the user has write access | `true` |

Key outputs: `instance_id`, `username`, `password` (sensitive).

Provider pin: `stackitcloud/stackit = 0.88.0`.

Validate: `terraform validate` from `infra/cloud/stackit/terraform/modules/secrets-manager/`.

## Smoke Checks

`make infra-secrets-manager-smoke` validates the runtime state file. Checks performed:

- `endpoint` starts with `https://secrets.`
- `namespace` is non-empty
- `auth_method_details` is non-empty

Smoke writes `artifacts/infra/secrets_manager_smoke.env` with `status=passed` on success.

## Destroy

`make infra-secrets-manager-destroy` removes the provisioned credentials and delegates to the foundation Terraform layer.

**STACKIT lane destroy sequence:**

1. Foundation Terraform removes `stackit_secretsmanager_instance` and `stackit_secretsmanager_user` from state.
2. `secrets_manager_delete_runtime_secret()` removes Secret `blueprint-secrets-manager-auth` (idempotent — tolerates missing Secret).
3. `remove_state_files_by_prefix secrets_manager_` removes all local runtime artifacts.

Re-running destroy when resources are already absent exits 0.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRETS_MANAGER_INSTANCE_NAME` | `marketplace-secrets` | Canonical SM instance name (required) |
| `SECRETS_MANAGER_K8S_NAMESPACE` | `secrets-manager` | Kubernetes namespace for the `blueprint-secrets-manager-auth` Secret |
