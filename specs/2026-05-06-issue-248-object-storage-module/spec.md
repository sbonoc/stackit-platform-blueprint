# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-object-storage-module.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale:
  - SDD-C-015: No app onboarding make-target contract changes — this work item affects only infra module wrappers, not app delivery workflows.
  - SDD-C-018: No blueprint upstream defect escalation — this is a blueprint-internal implementation.
  - SDD-C-022: Not applicable — no HTTP route handlers or new API endpoints in scope.
  - SDD-C-023: Not applicable — no filter or payload-transform logic in scope.
  - SDD-C-024: Not applicable — no pre-PR smoke/curl/deterministic-check findings to translate; no reproducible failures exist at intake time.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: local lane uses Bitnami MinIO (S3-compatible open-source) as the approved local-first equivalent per blueprint pattern; STACKIT Object Storage has no local emulator equivalent in the STACKIT provider
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Consumers can provision managed object storage on both local (MinIO on Docker Desktop) and STACKIT lanes with identical S3-compatible endpoint + credential outputs, enabling independent object storage lifecycle management without bundling inside application Helm releases.
- Success metric: `infra-object-storage-apply` is non-noop on both lanes; smoke passes; all 5 contract outputs populated (endpoint, bucket, access_key, secret_key, region); 0 plaintext credentials in checked-in values files; local lane execution class is `fallback_runtime` (consistent with rabbitmq/opensearch).

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST implement `infra/cloud/stackit/terraform/modules/object-storage/main.tf` as a standalone Terraform module declaring `stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, and `stackit_objectstorage_credential` resources. The module MUST expose outputs matching the 5-key contract declared in `blueprint/modules/object-storage/module.contract.yaml` (including `OBJECT_STORAGE_REGION`).
- FR-002 MUST expose an S3-compatible endpoint on both lanes at `OBJECT_STORAGE_ENDPOINT`: on local via MinIO Helm (`http://<release>.<namespace>.svc.cluster.local:9000`); on STACKIT via `https://object-storage.<region>.onstackit.cloud`.
- FR-003 MUST provision credentials (`OBJECT_STORAGE_ACCESS_KEY`, `OBJECT_STORAGE_SECRET_KEY`) on both lanes that authenticate to the S3-compatible endpoint with read/write access to the provisioned bucket `OBJECT_STORAGE_BUCKET_NAME`.
- FR-004 Local lane MUST store MinIO credentials in Kubernetes Secret `blueprint-object-storage-auth` (keys: `root-user`, `root-password`) via `apply_optional_module_secret_from_literals` on every apply, and reference the secret from the Helm values via `auth.existingSecret`. Credentials MUST NOT be embedded in the rendered values artifact (`artifacts/infra/rendered/object-storage.values.yaml`).
- FR-005 MUST write `artifacts/infra/object_storage_runtime.env` after every successful apply, containing at minimum: `profile`, `stack`, `provision_driver`, `provision_path`, `endpoint`, `bucket`, `access_key`, `secret_key`, `region`, `timestamp_utc`.
- FR-006 `infra-object-storage-smoke` MUST validate: runtime state file exists; `endpoint` matches `^https?://`; `bucket` is non-empty. Smoke MUST write `artifacts/infra/object_storage_smoke.env` on success.
- FR-007 `infra-object-storage-destroy` on local lane MUST run Helm uninstall (`--ignore-not-found`) and MUST delete the Kubernetes Secret `blueprint-object-storage-auth` after uninstall. On STACKIT lane destroy MUST route to `foundation_reconcile_apply`.
- FR-008 The local lane execution class in `module_execution.sh` MUST be `fallback_runtime` (not `provider_backed`) for both plan/apply and destroy actions, consistent with the rabbitmq and opensearch modules. The STACKIT lane MUST remain `provider_backed`.

Output naming: Option A selected — keep current naming (`OBJECT_STORAGE_ACCESS_KEY`, `OBJECT_STORAGE_SECRET_KEY`, `OBJECT_STORAGE_BUCKET_NAME`) and add `OBJECT_STORAGE_REGION` as a new additive output in `module.contract.yaml` and runtime state file. S3-standard naming (`ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`, `BUCKET_LIST`) from issue #248 is deferred to a separate breaking-change work item. Decision by owner PR comment 2026-05-06.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST NOT embed MinIO credentials (`OBJECT_STORAGE_ACCESS_KEY`, `OBJECT_STORAGE_SECRET_KEY`) in any checked-in file. Local lane credentials MUST be reconciled into Kubernetes Secret `blueprint-object-storage-auth` on every apply call. STACKIT credentials are provider-generated via `stackit_objectstorage_credential` and MUST be masked in logs (no `set -x` in credential-emitting sections).
- NFR-OBS-001 Each wrapper script MUST call `start_script_metric_trap` with the canonical metric name (`infra_object_storage_{plan,apply,smoke,destroy}`). Apply MUST log the runtime state file path. Smoke MUST log a pass/fail summary line.
- NFR-REL-001 Local Helm uninstall MUST be idempotent (`--ignore-not-found`). The Secret delete MUST also be idempotent (tolerate Secret-not-found). STACKIT lane Terraform destroy is idempotent by provider contract.
- NFR-OPS-001 Runtime state schema MUST include all 5 keys (`endpoint`, `bucket`, `access_key`, `secret_key`, `region`). Destroy MUST clean up all state files via `remove_state_files_by_prefix "object_storage_"`.
- NFR-A11Y-001 N/A — no UI component; this work item produces only infra provisioning scripts and a Terraform module.

## Normative Option Decision
- Option A: Keep current output naming (`ACCESS_KEY`, `SECRET_KEY`, `BUCKET_NAME`); add `OBJECT_STORAGE_REGION` as a new output.
- Option B: Rename all outputs to S3-standard naming per issue #248 spec.
- Selected option: OPTION_A
- Rationale: Keeps current naming convention (`ACCESS_KEY`, `SECRET_KEY`, `BUCKET_NAME`); adds `OBJECT_STORAGE_REGION` as a new additive output only. Preserves backward compatibility with existing consumer `ExternalSecret` refs and foundation Terraform outputs. S3-standard renaming deferred to a separate work item. Decision by owner PR comment 2026-05-06.

## Contract Changes (Normative)
- Config/Env contract: `OBJECT_STORAGE_REGION` added to runtime state schema and `module.contract.yaml` outputs; `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME` added as internal rendering variable for bootstrap (replaces plaintext `OBJECT_STORAGE_ACCESS_KEY`/`OBJECT_STORAGE_SECRET_KEY` in Helm values render).
- API contract: none — S3-compatible endpoint contract unchanged.
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `infra-object-storage-{plan,apply,smoke,destroy}` targets unchanged; no new targets.
- Module execution contract: `OPTIONAL_MODULE_EXECUTION_CLASS` changes from `provider_backed` to `fallback_runtime` for the local lane; STACKIT lane class unchanged (`provider_backed`). Test contract `test_tooling_contracts.py` gains a new assertion for object-storage local `class=fallback_runtime`.
- Docs contract: `docs/platform/modules/object-storage/README.md` updated; template seed `scripts/templates/blueprint/bootstrap/docs/platform/modules/object-storage/README.md` synced.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `infra-object-storage-apply` on `local-*` profile provisions the MinIO Helm release in the `data` namespace and writes `artifacts/infra/object_storage_runtime.env` containing lines: `endpoint=http://...`, `bucket=...`, `access_key=...`, `secret_key=...`.
- AC-002 `infra-object-storage-apply` on `stackit-*` profile (with valid STACKIT credentials) applies the standalone Terraform module and writes the same-schema runtime env file.
- AC-003 `infra-object-storage-smoke` exits 0 when runtime state file exists with `endpoint=https?://` and non-empty `bucket=`.
- AC-004 `infra-object-storage-smoke` exits non-zero when runtime state file is absent.
- AC-005 After `infra-object-storage-apply` on local lane, Kubernetes Secret `blueprint-object-storage-auth` exists with keys `root-user` and `root-password`; the rendered values artifact `artifacts/infra/rendered/object-storage.values.yaml` contains `auth.existingSecret: blueprint-object-storage-auth` and MUST NOT contain `auth.rootPassword`.
- AC-006 `infra/cloud/stackit/terraform/modules/object-storage/main.tf` declares `stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, and `stackit_objectstorage_credential` resources.
- AC-007 `tests/infra/modules/object-storage/test_contract.py` asserts all 5 contract output keys are present in the runtime state fixture: `endpoint`, `bucket`, `access_key`, `secret_key`, `region`.
- AC-008 `tests/infra/modules/object-storage/test_object_storage_module.py` passes for: script presence (plan/apply/smoke/destroy); values seed uses `auth.existingSecret`, not `auth.rootPassword`; credentials not passed to values render; apply script reconciles secret before Helm install; destroy script deletes secret after uninstall; versions pinned in `versions.sh`.
- AC-009 `tests/infra/test_tooling_contracts.py` includes a test asserting that object-storage local lane resolves to `class=fallback_runtime` and `driver=helm`; and a test asserting STACKIT lane resolves to `class=provider_backed` and `driver=foundation_contract`.

## Informative Notes (Non-Normative)
- Context: Unlike opensearch (which was a full noop for local), the object-storage local lane is already wired in `module_execution.sh` and the bin scripts — the primary work is the Terraform standalone module, Secret-backed credentials, and tests. The STACKIT lane currently runs through the foundation inline resources, which remain untouched; the standalone module is additive (mirrors foundation resources for standalone consumption).
- Tradeoffs: Option A (keep current naming, add REGION only) preserves backward compatibility but diverges from the S3-standard names in issue #248. This is an explicit scoping decision confirmed by the owner; S3-standard renaming is deferred to a separate work item.
- Clarifications:
  - The Bitnami MinIO chart uses `auth.existingSecret` with keys `root-user` and `root-password` (confirmed from chart templates at 17.x line).
  - STACKIT Object Storage does not expose a version number in the provider; the chart version pin (`OBJECT_STORAGE_HELM_CHART_VERSION_PIN`) already exists in `versions.sh` at `17.0.21`.
  - The `foundation_reconcile_apply` destroy route is already correctly wired in `module_execution.sh` and `object_storage_destroy.sh` — no changes needed for destroy routing.

## Explicit Exclusions
- Renaming `OBJECT_STORAGE_ACCESS_KEY`/`SECRET_KEY`/`BUCKET_NAME` to S3-standard names — requires separate breaking-change work item.
- Multi-bucket (`BUCKET_LIST`) provisioning pattern — separate work item.
- ESO `SecretStore` / `ExternalSecret` wiring for object storage credentials — consumer-side work.
- Migrating foundation inline resources to call the standalone module — Terraform state migration risk; additive-only approach per ADR.
