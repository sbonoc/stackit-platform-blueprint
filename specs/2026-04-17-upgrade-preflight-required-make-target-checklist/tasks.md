# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Update upgrade planner diagnostics for missing required consumer-owned make targets
- [x] T-002 Preserve invoker-path dependency context and add deterministic contract fallback dependency context
- [x] T-003 Update consumer-facing upgrade docs with preflight checklist guarantee and remediation location guidance
- [x] T-004 Update publish artifacts and traceability references for changed planner/test/docs scope

## Test Automation
- [x] T-101 Add red->green regression test for missing contract-required consumer make target without known invoker path
- [x] T-102 Keep existing upgrade manual-action tests green after planner changes
- [x] T-103 Positive-path filter/payload-transform unit test gate is not applicable for this work item (no filter/transform scope)
- [x] T-104 Translate reproducible pre-PR finding into failing automated test first, then green with fix in same work item
- [x] T-105 Run additional preflight report tests to confirm downstream report compatibility

## Validation and Release Readiness
- [x] T-201 Run required validation bundles for touched scope
- [x] T-202 Attach command/test evidence in `traceability.md`
- [x] T-203 Confirm no stale unresolved markers/dead code/drift in touched scope
- [x] T-204 Run documentation sync validation (`python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description references generated `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` remain available for affected app scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) remain available
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) remain available
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) remain available
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) remain available
