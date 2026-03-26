# KMS Module (Optional)

## Purpose
Provision managed key-management capability for encryption/signing operations.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `KMS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `KMS_ENABLED=true`.
- `stackit-*` profiles: Terraform module under `infra/cloud/stackit/terraform/modules/kms`.
- `local-*` profiles: no managed counterpart; module plan/apply is a no-op contract stub.

## Enable
```bash
export KMS_ENABLED=true
```

## Required Inputs
- `KMS_KEY_RING_NAME`
- `KMS_KEY_NAME`

## Commands
- `make infra-kms-plan`
- `make infra-kms-apply`
- `make infra-kms-smoke`
- `make infra-kms-destroy`

## Outputs
- `KMS_KEY_RING_NAME`
- `KMS_KEY_NAME`
- `KMS_KEY_ID`
