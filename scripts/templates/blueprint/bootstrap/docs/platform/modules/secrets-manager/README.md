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
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `SECRETS_MANAGER_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `SECRETS_MANAGER_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `SECRETS_MANAGER_ENABLED` contract flag.
  - `SECRETS_MANAGER_INSTANCE_NAME` is passed through as the canonical managed instance name.
- `local-*` profiles: no managed counterpart; module plan/apply is a no-op contract stub.
