# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation (ordered by slice)

### Slice 1 — Tests RED
- [x] T-001 Write `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` with all unit assertions RED (AC-001–AC-003, AC-005–AC-014 excluding AC-004)
- [x] T-002 Write `tests/infra/modules/rabbitmq/test_contract.py` with contract assertions RED (AC-004, AC-012)
- [x] T-003 Register both test files in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope
- [x] T-004 Confirm `pytest tests/infra/modules/rabbitmq/ -v` is all RED

### Slice 2 — STACKIT Terraform Module + Foundation Outputs
- [x] T-005 Implement `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` (complete with `stackit_rabbitmq_instance` + `stackit_rabbitmq_credential`; `lifecycle { create_before_destroy = true }` on instance)
- [x] T-006 Implement `infra/cloud/stackit/terraform/modules/rabbitmq/variables.tf` (all contract inputs)
- [x] T-007 Implement `infra/cloud/stackit/terraform/modules/rabbitmq/outputs.tf` (all contract output keys including `rabbitmq_management_url`)
- [x] T-008 Implement `infra/cloud/stackit/terraform/modules/rabbitmq/versions.tf` (provider version pin matching foundation)
- [x] T-009 Update `infra/cloud/stackit/terraform/foundation/outputs.tf`: add `rabbitmq_management_url` from `stackit_rabbitmq_credential.foundation[0].management`

### Slice 3 — Contract + Shell Layer
- [x] T-010 Update `blueprint/modules/rabbitmq/module.contract.yaml`: add `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` to `outputs.produced`
- [x] T-011 Add `rabbitmq_vhost()` and `rabbitmq_management_url()` to `scripts/lib/infra/rabbitmq.sh`
- [x] T-012 Update `scripts/bin/infra/rabbitmq_apply.sh`: add `vhost` and `management_url` keys to `write_state_file` call
- [x] T-013 Harden `scripts/bin/infra/rabbitmq_smoke.sh`: add explicit `host`, `port`, `vhost`, `management_url` non-empty checks

### Slice 4 — Docs
- [x] T-014 Write `docs/platform/modules/rabbitmq/README.md` (both-lanes usage, credentials, vhost, management URL, smoke, destroy sections)

## Test Automation
- [x] T-101 Tests in `test_rabbitmq_module.py`: Terraform module structure (AC-001, AC-002, AC-003); foundation outputs (AC-013); shell functions `rabbitmq_vhost()` and `rabbitmq_management_url()` (AC-005, AC-006); apply state file keys (AC-007); smoke pass/fail scenarios (AC-008, AC-009, AC-010, AC-011, AC-014)
- [x] T-102 Tests in `test_contract.py`: `module.contract.yaml` outputs include `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` (AC-004); runtime state has all seven keys (AC-012)
- [x] T-103 Not applicable — no filter/payload-transform logic in scope
- [x] T-104 Not applicable — no reproducible pre-PR findings to translate
- [x] T-105 Confirm total assertion count ≥ 20 across both test files

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in `spec.md` as "N/A — no UI component; rabbitmq is an infrastructure module with no browser-facing surface"
- [x] T-A02 N/A — no browser-facing surface
- [x] T-A03 N/A — no browser-facing surface
- [x] T-A04 N/A — no browser-facing surface
- [x] T-A05 N/A — no browser-facing surface

## Validation and Release Readiness
- [x] T-201 Run `pytest tests/infra/modules/rabbitmq/ -v` (≥ 20 assertions pass) and `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast`
- [x] T-202 Attach test output evidence to `traceability.md`
- [x] T-203 Confirm no stale TODOs/dead code/drift in changed files
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets
