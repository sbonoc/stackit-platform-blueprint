# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `version_contract_checker.py` (`scripts/lib/platform/apps/`) with `parse_lock_file`, `check_versions_lock`, `check_manifest_yaml`, `check_catalog_consistency`, and `main()` supporting `catalog-check` and `consistency` modes
- [x] T-002 Extend `scripts/bin/platform/apps/audit_versions.sh` with catalog-check invocation and `apps_version_contract_check_total` metric; update `apps_version_audit_summary_total` with contract fields
- [x] T-003 Extend `scripts/bin/platform/apps/audit_versions_cached.sh` to conditionally include `apps/catalog/versions.lock` and `apps/catalog/manifest.yaml` in `fingerprint_files[]`
- [x] T-004 Extend `scripts/bin/platform/apps/smoke.sh` with consistency-check invocation (catalog-enabled branch); add ADR at `docs/blueprint/architecture/decisions/ADR-20260423-issue-56-app-version-contract-checks.md`

## Test Automation
- [x] T-101 Add 22 unit tests in `tests/infra/test_version_contract_checker.py` covering parse, lock check, manifest check, consistency check, main() integration
- [x] T-102 No contract tests required; no new make targets or env var contracts added
- [x] T-103 Positive-path coverage: `test_all_vars_match_returns_all_passed`, `test_consistent_lock_and_manifest_returns_all_passed`, `test_catalog_check_mode_exits_zero_when_all_pass`
- [x] T-104 Pre-PR finding translated to test: `test_catalog_check_mode_exits_nonzero_when_lock_stale` (stale FASTAPI_VERSION in lock → non-zero exit); `test_consistency_mode_exits_nonzero_when_stale_lock`
- [x] T-105 `MainTests` covers full `main()` path for both modes with temp dirs

## Validation and Release Readiness
- [x] T-201 `make quality-hooks-fast` green; `python3 -m pytest tests/infra/test_version_contract_checker.py` 22/22 pass
- [x] T-202 Traceability matrix updated in `traceability.md`
- [x] T-203 No stale TODOs or dead code introduced
- [x] T-204 `make docs-build` and `make docs-smoke` pass
- [x] T-205 `make quality-hardening-review` pass

## Publish
- [x] P-001 `hardening_review.md` updated with findings and proposals
- [x] P-002 `pr_context.md` updated with requirement coverage, reviewer files, validation evidence, rollback notes
- [x] P-003 PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` unaffected; `apps-smoke` extended with consistency check (catalog-enabled only)
- [x] A-002 Backend lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` verified unaffected — blueprint governance tooling only
- [x] A-003 Frontend lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` verified unaffected — blueprint governance tooling only
- [x] A-004 Aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` verified unaffected — blueprint governance tooling only
- [x] A-005 Port-forward wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` verified unaffected — blueprint governance tooling only
