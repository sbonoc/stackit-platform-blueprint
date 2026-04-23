# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Create `scripts/bin/blueprint/ci_upgrade_validate.sh` with `set -euo pipefail`, `start_script_metric_trap`, and pytest invocation with `--junitxml`
- [x] T-002 Add `quality-ci-upgrade-validate` target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (definition + `.PHONY` entry)
- [x] T-003 Regenerate `make/blueprint.generated.mk` via `make blueprint-render-makefile` (identical static target, no module-variable substitution)
- [x] T-004 Extend `scripts/lib/quality/render_ci_workflow.py` with `UPGRADE_E2E_VALIDATE_LANE` constant and `upgrade-e2e-validation` job in `_render_ci()`
- [x] T-005 Re-render `.github/workflows/ci.yml` via `make quality-ci-sync`
- [x] T-006 No blueprint docs or diagram updates required
- [x] T-007 No consumer-facing docs updates required (no consumer-facing contract changes)

## Test Automation
- [x] T-101 Add `test_quality_ci_upgrade_validate_target_and_script_exist` in `tests/blueprint/contract_refactor_scripts_cases.py` asserting: (a) `ci_upgrade_validate.sh` exists in `scripts/bin/blueprint/`, (b) `quality-ci-upgrade-validate` target exists in `make/blueprint.generated.mk`
- [x] T-102 No new contract tests required (no new contract surfaces)
- [x] T-103 No filter/payload-transform logic — gate not applicable
- [x] T-104 Pre-PR finding (no dedicated upgrade CI gate) is a structural gap; structural test (T-101) asserts the required artifacts exist before implementation; implementation turns the test green
- [x] T-105 No boundary/integration tests required beyond T-101

## Validation and Release Readiness
- [x] T-201 Run `shellcheck --severity=error scripts/bin/blueprint/ci_upgrade_validate.sh` and `make quality-hooks-fast`
- [x] T-202 Attach validation evidence to `traceability.md`
- [x] T-203 Confirm no stale TODOs, dead code, or drift in modified files
- [x] T-204 Run `make docs-build` and `make docs-smoke`
- [x] T-205 Run `make quality-hardening-review`

## Publish
- [x] P-001 Update `hardening_review.md`
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 PR description references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; blueprint CI lane target only
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact
