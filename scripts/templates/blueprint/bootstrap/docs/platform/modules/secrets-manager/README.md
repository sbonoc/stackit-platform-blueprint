# Secrets Manager Module (Optional)

## Purpose
Provision managed secrets-manager capability for runtime secret storage and controlled retrieval.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `SECRETS_MANAGER_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `SECRETS_MANAGER_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `SECRETS_MANAGER_ENABLED` contract flag.
  - `SECRETS_MANAGER_INSTANCE_NAME` is passed through as the canonical managed instance name.
- `local-*` profiles: no managed counterpart; module plan/apply is a no-op contract stub.

## Enable
```bash
export SECRETS_MANAGER_ENABLED=true
```

## Required Inputs
- `SECRETS_MANAGER_INSTANCE_NAME`

## Commands
- `make infra-secrets-manager-plan`
- `make infra-secrets-manager-apply`
- `make infra-secrets-manager-smoke`
- `make infra-secrets-manager-destroy`

## Outputs
- `SECRETS_MANAGER_INSTANCE_NAME`
- `SECRETS_MANAGER_ENDPOINT`
