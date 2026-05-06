# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | N/A | STACKIT standalone Terraform module | `infra/cloud/stackit/terraform/modules/object-storage/main.tf` | `test_object_storage_module.py::test_terraform_module_declares_bucket_resource` | `docs/platform/modules/object-storage/README.md § STACKIT lane` | `artifacts/infra/object_storage_runtime.env` |
| FR-002 | SDD-C-005, SDD-C-014 | N/A | Dual-lane endpoint resolution | `scripts/lib/infra/object_storage.sh::object_storage_endpoint()` | `test_object_storage_module.py::test_endpoint_resolution_*` | `docs/platform/modules/object-storage/README.md § Env-var reference` | `artifacts/infra/object_storage_runtime.env::endpoint` |
| FR-003 | SDD-C-005 | N/A | Credential provisioning on both lanes | `scripts/lib/infra/object_storage.sh::object_storage_access_key()`, `object_storage_secret_key()` | `test_object_storage_module.py::test_apply_*_credentials` | `docs/platform/modules/object-storage/README.md § Credentials` | `artifacts/infra/object_storage_runtime.env::access_key,secret_key` |
| FR-004 | SDD-C-005, SDD-C-009 | N/A | Secret-backed local credentials | `scripts/lib/infra/object_storage.sh::object_storage_reconcile_runtime_secret()`, `infra/local/helm/object-storage/values.yaml::auth.existingSecret` | `test_object_storage_module.py::test_local_values_uses_existing_secret`, `test_apply_reconciles_secret_before_helm` | `docs/platform/modules/object-storage/README.md § Credentials` | K8s Secret `blueprint-object-storage-auth` |
| FR-005 | SDD-C-010, SDD-C-012 | N/A | Runtime state file write | `scripts/bin/infra/object_storage_apply.sh::write_state_file` | `test_contract.py::test_object_storage_runtime_state_keys` | `docs/platform/modules/object-storage/README.md § State` | `artifacts/infra/object_storage_runtime.env` |
| FR-006 | SDD-C-005 | N/A | Smoke validation | `scripts/bin/infra/object_storage_smoke.sh` | `test_object_storage_module.py::test_smoke_*` | `docs/platform/modules/object-storage/README.md § Smoke` | `artifacts/infra/object_storage_smoke.env` |
| FR-007 | SDD-C-005, SDD-C-009 | N/A | Destroy with Secret cleanup | `scripts/bin/infra/object_storage_destroy.sh::helm)` case | `test_object_storage_module.py::test_destroy_deletes_runtime_secret` | `docs/platform/modules/object-storage/README.md § Destroy` | helm release removed; K8s Secret deleted |
| NFR-SEC-001 | SDD-C-009 | N/A | No plaintext creds in values | `scripts/lib/infra/object_storage.sh::object_storage_render_values_file()` (no ACCESS_KEY/SECRET_KEY binding); `infra/local/helm/object-storage/values.yaml` (auth.existingSecret only) | `test_object_storage_module.py::test_lib_does_not_pass_credentials_to_values_render`, `test_local_values_does_not_contain_plaintext_credentials` | `docs/platform/modules/object-storage/README.md § Credentials` | Rendered `artifacts/infra/rendered/object-storage.values.yaml` has no `rootPassword` |
| NFR-OBS-001 | SDD-C-010 | N/A | Metric trap per script | `scripts/bin/infra/object_storage_{plan,apply,smoke,destroy}.sh::start_script_metric_trap` | `test_object_storage_module.py::test_*_script_emits_metric_trap` | N/A | metric events emitted to observability backend |
| NFR-REL-001 | SDD-C-007 | N/A | Idempotent destroy | `scripts/bin/infra/object_storage_destroy.sh::run_helm_uninstall --ignore-not-found`; `object_storage_delete_runtime_secret` tolerates missing Secret | `test_object_storage_module.py::test_destroy_is_idempotent_helm` | `docs/platform/modules/object-storage/README.md § Destroy` | Re-run destroy exits 0 when resources absent |
| NFR-OPS-001 | SDD-C-010 | N/A | State schema completeness | `scripts/bin/infra/object_storage_apply.sh::write_state_file` keys | `test_contract.py::test_object_storage_runtime_state_keys` | `docs/platform/modules/object-storage/README.md § State` | `artifacts/infra/object_storage_runtime.env` |
| AC-001 | SDD-C-012 | N/A | Local apply produces runtime env | `scripts/bin/infra/object_storage_apply.sh::helm)` | `test_object_storage_module.py::test_apply_script_has_helm_case` | README § Local lane | `artifacts/infra/object_storage_runtime.env` |
| AC-002 | SDD-C-012 | N/A | STACKIT apply produces runtime env | `scripts/bin/infra/object_storage_apply.sh::foundation_contract)` | `test_object_storage_module.py::test_apply_script_has_foundation_contract_case` | README § STACKIT lane | `artifacts/infra/object_storage_runtime.env` |
| AC-003 | SDD-C-012 | N/A | Smoke passes with valid state | `scripts/bin/infra/object_storage_smoke.sh` | `test_object_storage_module.py::test_smoke_passes_with_valid_state` | README § Smoke | `artifacts/infra/object_storage_smoke.env` |
| AC-004 | SDD-C-012 | N/A | Smoke fails without state | `scripts/bin/infra/object_storage_smoke.sh` | `test_object_storage_module.py::test_smoke_fails_missing_runtime_state` | README § Smoke | non-zero exit, log_fatal message |
| AC-005 | SDD-C-009 | N/A | Local Secret-backed creds | `object_storage.sh`, `values.yaml`, `object_storage_apply.sh` | `test_object_storage_module.py::test_local_values_uses_existing_secret`, `test_apply_reconciles_secret_before_helm` | README § Credentials | K8s Secret `blueprint-object-storage-auth` exists post-apply |
| AC-006 | SDD-C-013 | N/A | Terraform module resources | `infra/cloud/stackit/terraform/modules/object-storage/main.tf` | `test_object_storage_module.py::test_terraform_module_declares_*` | README § STACKIT lane | `terraform validate` |
| AC-007 | SDD-C-012 | N/A | Contract test keys | `tests/infra/modules/object-storage/test_contract.py` | `test_contract.py` all assertions | N/A | N/A |
| AC-008 | SDD-C-008, SDD-C-012 | N/A | Full unit test coverage | `tests/infra/modules/object-storage/test_object_storage_module.py` | all assertions green | N/A | N/A |
| FR-008 | SDD-C-005, SDD-C-007 | N/A | Execution class alignment | `scripts/lib/infra/module_execution.sh` local lane `object-storage:plan\|apply` and `object-storage:destroy` | `test_tooling_contracts.py::test_optional_module_execution_resolves_local_fallback_modes_for_object_storage` | N/A | metric label `class=fallback_runtime` emitted for local lane |
| AC-009 | SDD-C-012 | N/A | Tooling contract test for class | `tests/infra/test_tooling_contracts.py` | both new assertions green | N/A | N/A |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009

## Validation Summary
- Required bundles executed: (to be filled at Step 7 — Publish)
- Result summary: (to be filled at Step 7 — Publish)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-docs-check-changed`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Q-1 naming alignment — once answered, update `module.contract.yaml`, state schema, smoke, and contract test to add REGION or rename keys (if Option B chosen, requires separate breaking-change work item).
- Follow-up 2: Per-bucket credential scoping (STACKIT `credentials_group` allows bucket-scoped credentials) — deferred to a separate work item when a consumer needs scoped keys.
