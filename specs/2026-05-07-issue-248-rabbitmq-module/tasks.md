# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Implement STACKIT Terraform module: `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` (complete with resources), `variables.tf`, `outputs.tf`
- [ ] T-002 Update foundation outputs: add `rabbitmq_management_url` to `infra/cloud/stackit/terraform/foundation/outputs.tf`
- [ ] T-003 Update `blueprint/modules/rabbitmq/module.contract.yaml`: add `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` to `outputs.produced`
- [ ] T-004 Add `rabbitmq_vhost()` and `rabbitmq_management_url()` to `scripts/lib/infra/rabbitmq.sh`
- [ ] T-005 Update `scripts/bin/infra/rabbitmq_apply.sh`: add `vhost` and `management_url` keys to `write_state_file` call
- [ ] T-006 Harden `scripts/bin/infra/rabbitmq_smoke.sh`: add explicit `host`, `port`, `vhost`, `management_url` non-empty checks
- [ ] T-007 Write `docs/platform/modules/rabbitmq/README.md` (both-lanes usage, credentials, vhost, management URL, smoke, destroy sections)

## Test Automation
- [ ] T-101 Write unit tests for STACKIT Terraform module structure (AC-001, AC-002, AC-003)
- [ ] T-102 Write contract test confirming `module.contract.yaml` outputs include `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` (AC-004)
- [ ] T-103 Not applicable — no filter/payload-transform logic in scope
- [ ] T-104 Not applicable — no reproducible pre-PR findings to translate
- [ ] T-105 Write unit tests for `rabbitmq_vhost()` and `rabbitmq_management_url()` (AC-005, AC-006); write state file and smoke pass/fail tests (AC-007 through AC-012); write foundation outputs test (AC-013)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in `spec.md` as "N/A — no UI component; rabbitmq is an infrastructure module with no browser-facing surface"
- [x] T-A02 N/A — no browser-facing surface
- [x] T-A03 N/A — no browser-facing surface
- [x] T-A04 N/A — no browser-facing surface
- [x] T-A05 N/A — no browser-facing surface

## Validation and Release Readiness
- [ ] T-201 Run `pytest tests/infra/modules/rabbitmq/ -v` (≥ 20 assertions pass) and `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast`
- [ ] T-202 Attach test output evidence to `traceability.md`
- [ ] T-203 Confirm no stale TODOs/dead code/drift in changed files
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets
