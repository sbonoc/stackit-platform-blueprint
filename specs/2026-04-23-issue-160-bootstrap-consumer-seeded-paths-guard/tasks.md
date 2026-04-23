# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `infra_bootstrap_consumer_seeded_skip_count=0` counter in `scripts/bin/infra/bootstrap.sh`
- [x] T-002 Add `blueprint_path_is_consumer_seeded` guard (with `log_info` + counter increment) to `ensure_infra_template_file`
- [x] T-003 Add `blueprint_path_is_consumer_seeded` guard (with `log_info` + counter increment) to `ensure_infra_rendered_file`
- [x] T-004 Emit `infra_consumer_seeded_skip_count` metric at end of bootstrap

## Test Automation
- [x] T-101 Add `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` in `tests/blueprint/contract_refactor_scripts_cases.py`
- [x] T-102 No contract tests required; no new make targets or env var contracts added
- [x] T-103 No filter/payload-transform logic; positive-path gate not applicable
- [x] T-104 Pre-PR finding (placeholder files recreated on `make infra-bootstrap`) translated to structural test asserting guard exists in both functions
- [x] T-105 No boundary/integration tests required; fix is within a single shell function

## Validation and Release Readiness
- [x] T-201 `make quality-hooks-fast` green; `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k infra_bootstrap` 2/2 pass
- [x] T-202 Traceability matrix updated in `traceability.md`
- [x] T-203 No stale TODOs or dead code introduced
- [x] T-204 `make docs-build` and `make docs-smoke` pass
- [x] T-205 `make quality-hardening-review` pass

## Publish
- [x] P-001 `hardening_review.md` updated with findings and proposals
- [x] P-002 `pr_context.md` updated with requirement coverage, reviewer files, validation evidence, rollback notes
- [x] P-003 PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` unaffected — blueprint governance tooling only
- [x] A-002 Backend lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` verified unaffected — blueprint governance tooling only
- [x] A-003 Frontend lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` verified unaffected — blueprint governance tooling only
- [x] A-004 Aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` verified unaffected — blueprint governance tooling only
- [x] A-005 Port-forward wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` verified unaffected — blueprint governance tooling only
