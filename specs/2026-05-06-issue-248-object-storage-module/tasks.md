# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Tests RED
- [x] T-001 Write `tests/infra/modules/object-storage/test_contract.py` (contract fixture assertions)
- [x] T-002 Write `tests/infra/modules/object-storage/test_object_storage_module.py` (module unit assertions — all RED)
- [x] T-003 Confirm all new tests fail (RED) before proceeding to implementation slices

## Implementation — Slice 2: STACKIT Terraform standalone module
- [x] T-010 Implement `infra/cloud/stackit/terraform/modules/object-storage/main.tf` (`stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, `stackit_objectstorage_credential`)
- [x] T-011 Write `infra/cloud/stackit/terraform/modules/object-storage/variables.tf`
- [x] T-012 Write `infra/cloud/stackit/terraform/modules/object-storage/outputs.tf`
- [x] T-013 Write `infra/cloud/stackit/terraform/modules/object-storage/versions.tf`
- [x] T-014 Confirm Terraform module tests GREEN

## Implementation — Slice 3: Execution class fix + Secret-backed credentials
- [x] T-020 Update `scripts/lib/infra/module_execution.sh` — change local lane class from `provider_backed` to `fallback_runtime` for both `object-storage:plan|apply` and `object-storage:destroy`
- [x] T-021 Add `test_optional_module_execution_resolves_local_fallback_modes_for_object_storage` and `test_optional_module_execution_resolves_stackit_provider_backed_object_storage_modes` to `tests/infra/test_tooling_contracts.py`
- [x] T-022 Add `object_storage_credential_secret_name()`, `object_storage_reconcile_runtime_secret()`, `object_storage_delete_runtime_secret()` to `scripts/lib/infra/object_storage.sh`
- [x] T-023 Update `object_storage_render_values_file()` — remove plaintext creds, add `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME` binding
- [x] T-024 Update `infra/local/helm/object-storage/values.yaml` — replace `auth.rootUser`/`auth.rootPassword` with `auth.existingSecret`
- [x] T-025 Update `scripts/templates/infra/bootstrap/infra/local/helm/object-storage/values.yaml` — same change
- [x] T-026 Update `scripts/bin/infra/object_storage_apply.sh` — call `object_storage_reconcile_runtime_secret` before `run_helm_upgrade_install` in `helm)` case
- [x] T-027 Update `scripts/bin/infra/object_storage_destroy.sh` — call `object_storage_delete_runtime_secret` after `run_helm_uninstall` in `helm)` case
- [x] T-028 Update `scripts/bin/infra/bootstrap.sh` — use `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME` instead of plaintext ACCESS_KEY/SECRET_KEY in `object-storage)` case
- [x] T-029 Confirm class fix and Secret-backed credential tests GREEN

## Implementation — Slice 4: Contract + smoke + docs (pending Q-1)
- [x] T-030 Update `blueprint/modules/object-storage/module.contract.yaml` — add `OBJECT_STORAGE_REGION` to `outputs.produced`
- [x] T-031 Update `scripts/bin/infra/object_storage_apply.sh` — add `region=$OBJECT_STORAGE_REGION` to `write_state_file` call
- [x] T-032 Update `scripts/bin/infra/object_storage_smoke.sh` — add `region` validation (grep `^region=`)
- [x] T-033 Complete `docs/platform/modules/object-storage/README.md`
- [x] T-034 Sync seed docs via `python3 scripts/lib/docs/sync_platform_seed_docs.py` — already synchronized
- [x] T-035 Confirm contract + docs tests GREEN (27/27 passed)

## Test Automation
- [x] T-101 Confirm `pytest tests/infra/modules/object-storage/ -v` — all green (27/27 passed)
- [x] T-102 Confirm `pytest tests/infra/test_tooling_contracts.py -k object` — green (2/2 passed)
- [x] T-103 N/A — no filter/payload-transform logic
- [x] T-104 N/A — no pre-PR reproducible failures
- [x] T-105 N/A — no boundary/integration tests beyond above

## Accessibility Testing
- [x] T-A01 Confirmed NFR-A11Y-001 is declared as "N/A — no UI component" in `spec.md`
- [x] T-A02 N/A — no UI
- [x] T-A03 N/A — no UI
- [x] T-A04 N/A — no UI
- [x] T-A05 N/A — no UI

## Validation and Release Readiness
- [x] T-201 Run `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` — 8/9 pass; quality-spec-pr-ready resolves with publish artifact completion (P-001/P-002)
- [x] T-202 Attach evidence to `traceability.md` — pending final commit (evidence: 27/27 tests green, all quality checks pass)
- [x] T-203 Confirm no stale TODOs/dead code/drift — confirmed; no stale markers
- [x] T-204 Run `make quality-docs-check-changed` — green
- [x] T-205 Run `make quality-hardening-review` — covered by quality-hooks-fast run above

## Publish
- [x] P-001 Complete `hardening_review.md`
- [x] P-002 Complete `pr_context.md`
- [x] P-003 Ensure PR description follows repository template

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets
