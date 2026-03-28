# Object Storage Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed object storage and expose canonical S3-compatible upload/download contract.
- Enable flag: `OBJECT_STORAGE_ENABLED` (default: `false`)
- Required inputs:
  - `OBJECT_STORAGE_BUCKET_NAME`
- Make targets:
  - `infra-object-storage-plan`
  - `infra-object-storage-apply`
  - `infra-object-storage-smoke`
  - `infra-object-storage-destroy`
- Outputs:
  - `OBJECT_STORAGE_ENDPOINT`
  - `OBJECT_STORAGE_BUCKET_NAME`
  - `OBJECT_STORAGE_ACCESS_KEY`
  - `OBJECT_STORAGE_SECRET_KEY`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `OBJECT_STORAGE_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `OBJECT_STORAGE_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `OBJECT_STORAGE_ENABLED` contract flag.
  - `OBJECT_STORAGE_BUCKET_NAME` is passed through as the canonical bucket contract.
  - Access keys are provider-generated and resolved into runtime artifacts from foundation outputs after apply.
- `local-*` profiles: Helm chart (`bitnami/minio`) using `infra/local/helm/object-storage/values.yaml`.
  - The local fallback uses explicit pinned `docker.io/bitnamilegacy/*` images instead of relying on drifting chart defaults; that registry name is a vendor namespace quirk, while the pinned tags still track the latest stable supported multi-arch line we validate in this repo.
  - Because those pinned legacy images are outside Bitnami's default registry allowlist, the values contract explicitly enables `global.security.allowInsecureImages=true` for this local-only fallback path.
- The pinned legacy images are multi-arch, so the same fallback version contract runs on amd64 CI nodes and arm64 Docker Desktop clusters.
  - STACKIT Object Storage does not expose a provider-side runtime version line in the contract today, so the local MinIO fallback tracks the latest stable compatible chart release rather than a managed-service version number.
