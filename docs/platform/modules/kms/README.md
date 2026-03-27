# KMS Module (Optional)

## Purpose
Provision managed key-management capability for encryption/signing operations.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `KMS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `KMS_ENABLED=true`.
- `stackit-*` profiles: STACKIT foundation provisions managed KMS through `stackit_kms_keyring` plus `stackit_kms_key`.
- `local-*` profiles: no managed counterpart; module plan/apply is a no-op contract stub.

## Enable
```bash
export KMS_ENABLED=true
```

## Required Inputs
- `KMS_KEY_RING_NAME`
- `KMS_KEY_NAME`

## Optional Inputs
- `KMS_KEY_RING_DESCRIPTION`
- `KMS_KEY_DESCRIPTION`
- `KMS_KEY_ALGORITHM`
- `KMS_KEY_PURPOSE`
- `KMS_KEY_PROTECTION`
- `KMS_KEY_ACCESS_SCOPE`
- `KMS_KEY_IMPORT_ONLY`

## Commands
- `make infra-kms-plan`
- `make infra-kms-apply`
- `make infra-kms-smoke`
- `make infra-kms-destroy`

## Outputs
- `KMS_KEY_RING_NAME`
- `KMS_KEY_NAME`
- `KMS_KEY_RING_ID`
- `KMS_KEY_ID`

Destroy semantics follow the official provider contract: keyrings are removed from Terraform state without API deletion, and keys are scheduled for deletion rather than being deleted immediately.
