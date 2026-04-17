# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Update contract/governance surfaces
- [x] T-002 Implement runtime/code changes
- [x] T-003 Update blueprint docs/diagrams
- [x] T-004 Update consumer-facing docs/diagrams when contracts/behavior change

## Test Automation
- [x] T-101 Add or update unit tests
- [x] T-102 Add or update contract tests
- [x] T-103 Add boundary/integration tests where required

## Validation and Release Readiness
- [x] T-201 Run required Make validation bundles
- [x] T-202 Attach evidence to traceability document
- [x] T-203 Confirm no stale markers/dead code/drift in touched scope
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` remain available for affected app scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) remain available
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) remain available
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) remain available
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) remain available
