# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate:
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate:
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate:
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices
1. Slice 1: implement validate required-file reconciliation and coupled generated-reference checks.
2. Slice 2: implement preflight required-surface-at-risk enrichment and schema/metrics/test updates.

## Change Strategy
- Migration/rollout sequence:
  - add validate logic and schema fields
  - add preflight enrichment fields
  - add metrics extraction keys and wrapper emission
  - add/adjust fixture-backed tests
- Backward compatibility policy:
  - existing report fields and existing required validation targets remain unchanged
  - new report fields are additive in JSON payloads while schema is updated in the same change
- Rollback plan:
  - revert changed validate/preflight/metrics/schema/test files to previous baseline
  - rerun `make infra-validate` and `make quality-hooks-fast`

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer`
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight`
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer_wrapper`
- Contract checks:
  - `python3 -m unittest tests.blueprint.test_quality_contracts`
  - `make infra-validate`
- Integration checks: not required for this script-only work item.
- E2E checks: not required for this script-only work item.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact | impacted (select one)
- App onboarding impact: no-impact
- Notes: no `apps/**` scope change; app onboarding targets remain unchanged.

## Documentation Plan (Document Phase)
- Blueprint docs updates: update work-item SDD artifacts and ADR.
- Consumer docs updates: none.
- Mermaid diagrams updated: ADR decision/context diagrams only.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - For work that touches HTTP route handlers, query/filter logic, or new API endpoints, run local smoke before PR publication.
  - Execute local smoke with deterministic wrappers (`make infra-provision`, `make infra-deploy`, `make infra-port-forward-start`), then run positive-path `curl` assertions per changed endpoint.
  - Positive-path filter assertions MUST use non-empty fixture/request values; empty-result-only assertions MUST NOT satisfy this gate.
  - Record evidence in `pr_context.md` as `Endpoint | Method | Auth | Result`.
  - Stop/cleanup wrappers after smoke (`make infra-port-forward-stop`, `make infra-port-forward-cleanup`).
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces:
  - add validate summary counters for required files and generated-reference checks
  - emit wrapper metrics from `upgrade_consumer_validate.sh`
- Alerts/ownership:
  - no new alert contract; existing CI gate status covers this scope
- Runbook updates:
  - remediation hints are embedded in validation report and stderr diagnostics

## Risks and Mitigations
- Risk 1: false positives in generated-consumer repos from source-only required paths.
  - Mitigation: explicit repo-mode gating and fixture-backed tests for generated-consumer/template-source behavior.
- Risk 2: schema/report drift when adding new payload fields.
  - Mitigation: update schema and schema-validated tests in the same change.
