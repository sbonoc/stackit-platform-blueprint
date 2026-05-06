# Work Item Context Pack

## Context Snapshot
- Work item: issue-248-object-storage-module — object-storage dual-lane implementation (MinIO local + STACKIT Terraform)
- Track: blueprint
- SPEC_READY: false
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-object-storage-module.md
- ADR status: proposed

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021

## Key Findings from Intake

### Current state (partially implemented — more complete than opensearch was)
- `module_execution.sh` already routes object-storage correctly: local → `helm`, stackit → `foundation_contract` (NOT `noop`)
- All 4 bin scripts (`plan`, `apply`, `smoke`, `destroy`) already have `helm)` and `foundation_contract)` cases
- `scripts/lib/infra/object_storage.sh` already has endpoint/bucket/access_key/secret_key getters
- `versions.sh` already has chart version pin (`17.0.21`) and image pins
- `infra/local/helm/object-storage/values.yaml` exists (materialized)

### Primary gaps
1. **Terraform standalone module** (`infra/cloud/stackit/terraform/modules/object-storage/main.tf`) is a 7-line stub — must implement `stackit_objectstorage_bucket` + credentials resources
2. **Credentials are plaintext** in values render — must migrate to `auth.existingSecret` pattern (Secret-backed, matching rabbitmq/opensearch)
3. **Zero tests** — `tests/infra/modules/object-storage/` has only a README stub
4. **REGION not in outputs** — contract has 4 outputs; issue #248 lists 5 (pending Q-1 resolution)

### Open question (Q-1)
Output naming alignment: keep current names (`ACCESS_KEY`, `SECRET_KEY`, `BUCKET_NAME`) + add REGION (Option A, recommended) vs rename to S3-standard per issue #248 (Option B, breaking). Agent recommends Option A.

### Pattern references
- Rabbitmq: `apply_optional_module_secret_from_literals` → Secret reconcile → `auth.existingSecret` (same pattern for MinIO)
- Opensearch: `security.existingSecret` / `opensearch-password` key — MinIO equivalent: `auth.existingSecret` / keys `root-user` + `root-password`
- Foundation: `stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, `stackit_objectstorage_credential` inline resources are the template for the standalone module

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`
- `pytest tests/infra/modules/object-storage/ -v`
- `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
