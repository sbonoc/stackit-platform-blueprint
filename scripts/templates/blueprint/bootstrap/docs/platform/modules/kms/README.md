# KMS Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed key-management capability for encryption/signing workloads.
- Enable flag: `KMS_ENABLED` (default: `false`)
- Required inputs:
  - `KMS_KEY_RING_NAME`
  - `KMS_KEY_NAME`
- Make targets:
  - `infra-kms-plan`
  - `infra-kms-apply`
  - `infra-kms-smoke`
  - `infra-kms-destroy`
- Outputs:
  - `KMS_KEY_RING_NAME`
  - `KMS_KEY_NAME`
  - `KMS_KEY_RING_ID`
  - `KMS_KEY_ID`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `KMS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `KMS_ENABLED=true`.
- `stackit-*` profiles: STACKIT foundation provisions managed KMS through `stackit_kms_keyring` plus `stackit_kms_key`.
- `local-*` profiles: no managed counterpart; module plan/apply is a no-op contract stub.

## Optional Inputs
- `KMS_KEY_RING_DESCRIPTION`
- `KMS_KEY_DESCRIPTION`
- `KMS_KEY_ALGORITHM`
- `KMS_KEY_PURPOSE`
- `KMS_KEY_PROTECTION`
- `KMS_KEY_ACCESS_SCOPE`
- `KMS_KEY_IMPORT_ONLY`

Destroy semantics follow the official provider contract: keyrings are removed from Terraform state without API deletion, and keys are scheduled for deletion rather than being deleted immediately.
