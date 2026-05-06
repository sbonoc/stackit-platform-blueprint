# ADR: Issue #248 — Object Storage Module Implementation (Dual-Lane)

- **Status**: proposed
- **Date**: 2026-05-06
- **Issue**: #248
- **Work item**: `specs/2026-05-06-issue-248-object-storage-module/`

## Context

The `infra/cloud/stackit/terraform/modules/object-storage/main.tf` is a 7-line stub. The STACKIT lane routes through the `foundation_contract` driver (inline resources in `infra/cloud/stackit/terraform/foundation/main.tf`): `stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, `stackit_objectstorage_credential`. The local lane is wired in `module_execution.sh` and the bin scripts but passes MinIO credentials as plaintext into the Helm values render (`auth.rootUser`/`auth.rootPassword`) rather than using the Secret-backed pattern established by rabbitmq and opensearch. No automated tests exist.

Issue #248 requires first-class implementation with:
1. A standalone Terraform module for STACKIT (additive; foundation inline resources unchanged)
2. Secret-backed credentials for local lane (security alignment with rabbitmq/opensearch pattern)
3. Execution class alignment (`provider_backed` → `fallback_runtime` for local lane, matching rabbitmq/opensearch)
4. Comprehensive unit tests

A separate inconsistency was discovered during intake: `module_execution.sh` classifies object-storage and postgres local lanes as `provider_backed`, while rabbitmq and opensearch local lanes use `fallback_runtime`. All four use Bitnami Helm charts locally. This is a pre-existing inconsistency; this work item corrects it for object-storage only. Postgres is out of scope here.

## Decisions

### D-1: Additive standalone Terraform module (no foundation migration)

Implement `infra/cloud/stackit/terraform/modules/object-storage/` as a standalone module that mirrors the three foundation inline resources (`stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, `stackit_objectstorage_credential`). The foundation layer continues to manage its own inline resources; the standalone module is available for isolated use outside the foundation deployment pattern. No Terraform state migration is required.

**Rejected alternative:** Have the foundation call `module "object_storage" { source = "../modules/object-storage" }` — rejected due to Terraform state migration risk and no active consumer driver for the refactor.

### D-2: Secret-backed credentials for local lane

Replace `auth.rootUser`/`auth.rootPassword` plaintext fields in the MinIO Helm values with `auth.existingSecret` referencing Kubernetes Secret `blueprint-object-storage-auth`. The Secret is reconciled on every apply via `apply_optional_module_secret_from_literals` (same pattern as rabbitmq and opensearch). Keys in the Secret are `root-user` and `root-password` (confirmed from Bitnami MinIO chart 17.x templates).

This means `object_storage_render_values_file()` no longer passes `OBJECT_STORAGE_ACCESS_KEY` or `OBJECT_STORAGE_SECRET_KEY` as rendering variables, and `scripts/bin/infra/bootstrap.sh` passes `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME` instead.

**Rejected alternative:** Keep plaintext credentials in values — rejected due to NFR-SEC-001 (credentials must not appear in checked-in artifacts).

### D-3: Execution class — `fallback_runtime` for local lane

Change `OPTIONAL_MODULE_EXECUTION_CLASS` from `provider_backed` to `fallback_runtime` for the object-storage local lane in `module_execution.sh`, consistent with rabbitmq and opensearch. The STACKIT lane remains `provider_backed`. The local MinIO Helm chart is a development approximation of STACKIT Object Storage, not the actual managed service — `fallback_runtime` is the correct classification. This affects the metric label (`class=`) emitted by `optional_module_execution_emit_metric` and the tooling contract tests.

**Rejected alternative:** Keep `provider_backed` for local lane — rejected because it is semantically incorrect (MinIO is not the STACKIT-managed service) and inconsistent with the established pattern for rabbitmq and opensearch.

### D-4: Output naming — keep current convention, add REGION (Q-1 pending)

Issue #248 lists output names `OBJECT_STORAGE_ACCESS_KEY_ID`, `OBJECT_STORAGE_SECRET_ACCESS_KEY`, `OBJECT_STORAGE_BUCKET_LIST`, `OBJECT_STORAGE_REGION`. The current implementation uses `OBJECT_STORAGE_ACCESS_KEY`, `OBJECT_STORAGE_SECRET_KEY`, `OBJECT_STORAGE_BUCKET_NAME`. Renaming is a breaking contract change.

**Recommended decision (pending Q-1 sign-off):** Keep current naming; add `OBJECT_STORAGE_REGION` as a new non-breaking additive output. The S3-standard naming from issue #248 is aspirational and would require a separate breaking-change work item with a consumer migration plan.

**Rejected alternative:** Rename to S3-standard naming in this work item — rejected due to breaking impact on existing consumers and foundation Terraform outputs that already use current key names.

## Consequences

- `infra/cloud/stackit/terraform/modules/object-storage/`: new standalone module (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`).
- `scripts/lib/infra/object_storage.sh`: add `object_storage_credential_secret_name()`, `object_storage_reconcile_runtime_secret()`, `object_storage_delete_runtime_secret()`; update `object_storage_render_values_file()`.
- `infra/local/helm/object-storage/values.yaml` (seed) + template: replace `auth.rootUser`/`auth.rootPassword` with `auth.existingSecret`.
- `scripts/bin/infra/object_storage_apply.sh`: call `object_storage_reconcile_runtime_secret` before Helm install.
- `scripts/bin/infra/object_storage_destroy.sh`: call `object_storage_delete_runtime_secret` after Helm uninstall.
- `scripts/bin/infra/bootstrap.sh`: pass `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME` instead of plaintext creds.
- `blueprint/modules/object-storage/module.contract.yaml`: add `OBJECT_STORAGE_REGION` output (pending Q-1).
- `tests/infra/modules/object-storage/`: new `test_contract.py` + `test_object_storage_module.py`.
- `docs/platform/modules/object-storage/README.md`: complete dual-lane docs.
- `scripts/lib/infra/module_execution.sh`: local lane class changed from `provider_backed` to `fallback_runtime` for object-storage plan/apply/destroy.
- `tests/infra/test_tooling_contracts.py`: two new assertions for object-storage local (`class=fallback_runtime`) and STACKIT (`class=provider_backed`).
- No changes to Make target names, `module_execution.sh` routing logic, or foundation inline resources.
- No Terraform state migration required.
