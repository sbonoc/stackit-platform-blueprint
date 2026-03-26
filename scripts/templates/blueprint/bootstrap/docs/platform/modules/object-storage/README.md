# Object Storage Module (Optional)

## Purpose
Provision managed object storage and publish canonical S3-compatible contracts for ingestion and secure downloads.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `OBJECT_STORAGE_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `OBJECT_STORAGE_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `OBJECT_STORAGE_ENABLED` contract flag.
- `local-*` profiles: Helm chart (`bitnami/minio`) using `infra/local/helm/object-storage/values.yaml`.

## Enable
```bash
export OBJECT_STORAGE_ENABLED=true
```

## Required Inputs
- `OBJECT_STORAGE_BUCKET_NAME`

## Commands
- `make infra-object-storage-plan`
- `make infra-object-storage-apply`
- `make infra-object-storage-smoke`
- `make infra-object-storage-destroy`

## Outputs
- `OBJECT_STORAGE_ENDPOINT`
- `OBJECT_STORAGE_BUCKET_NAME`
- `OBJECT_STORAGE_ACCESS_KEY`
- `OBJECT_STORAGE_SECRET_KEY`
