# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Rename `POSTGRES_DB` → `POSTGRES_DB_NAME` in `blueprint/modules/postgres/module.contract.yaml` `spec.outputs.produced` (Issue #137)
- [x] T-002 Add `_MODULE_MAKE_TARGETS` static mapping and `_collect_stale_module_target_actions` helper in `scripts/lib/blueprint/upgrade_consumer.py` (Issue #118)
- [x] T-003 Add `_file_content_references_make_target` helper in `scripts/lib/blueprint/upgrade_consumer.py`
- [x] T-004 Wire `_collect_stale_module_target_actions` into plan assembly block in `upgrade_consumer.py`
- [x] T-005 Run `make quality-docs-sync-all` — synced `docs/platform/modules/postgres/README.md`, bootstrap template copy, and `docs/reference/generated/contract_metadata.generated.md`
- [x] T-006 Create ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-118-137-preflight-module-targets-postgres-eso-key.md`

## Test Automation
- [x] T-101 Add `PostgresContractKeyParityTests::test_postgres_module_contract_outputs_uses_postgres_db_name` in `tests/infra/test_tooling_contracts.py` (AC-001)
- [x] T-102 Add `PostgresContractKeyParityTests::test_postgres_eso_manifest_uses_postgres_db_name_as_secret_key` in `tests/infra/test_tooling_contracts.py` (AC-002)
- [x] T-103 N/A — no filter/payload-transform logic
- [x] T-104 Issue #137 translated into `PostgresContractKeyParityTests` assertions; Issue #118 translated into `StaleModuleTargetDetectionTests` positive-path assertions
- [x] T-105 Add `StaleModuleTargetDetectionTests` (5 tests) in `tests/blueprint/test_upgrade_consumer.py` (AC-003, AC-004, AC-005)
- [x] T-106 All 35 existing `test_upgrade_consumer.py` tests still pass; total `quality-hooks-fast` test count 105

## Validation and Release Readiness
- [x] T-201 `make quality-hooks-fast` passes (105 tests)
- [x] T-202 Traceability document updated with all requirement-to-delivery mappings
- [x] T-203 No stale TODOs, dead code, or drift; `make quality-sdd-check` passes
- [x] T-204 `make docs-build` and `make docs-smoke` pass
- [x] T-205 `make quality-hardening-review` passes

## Publish
- [x] P-001 `hardening_review.md` updated with findings and proposals
- [x] P-002 `pr_context.md` updated with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 PR #156 description follows repository template and references spec artifacts

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected
