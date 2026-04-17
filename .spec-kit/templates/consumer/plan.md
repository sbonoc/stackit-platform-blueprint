# Plan

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

## Work Slices
1. Slice 1
2. Slice 2

## Validation Plan
- Unit:
- Contract:
- Integration:
- E2E:

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
- Notes:

## Documentation Plan (Document Phase)
- Platform docs updates:
- Mermaid diagrams updated:
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
  - Execute local smoke with deterministic wrappers (`make infra-provision`, `make infra-deploy`, `make infra-port-forward-start`), or explicit equivalent profile-specific wrappers when the repository defines them.
  - Positive-path filter assertions MUST use non-empty fixture/request values; empty-result-only assertions MUST NOT satisfy this gate.
  - Record evidence in `pr_context.md` as `Endpoint | Method | Auth | Result`.
  - Stop/cleanup wrappers after smoke (`make infra-port-forward-stop`, `make infra-port-forward-cleanup`).
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operability Plan
- Runbook updates:
- Monitoring/alerting updates:
