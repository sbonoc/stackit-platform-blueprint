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
1. Slice 1: add red tests for repo-mode fast-lane selection behavior and template-source fail-fast behavior.
2. Slice 2: implement repo-mode selector and required-path validation in `contract_test_fast.sh`.
3. Slice 3: run fast-lane validation commands and update governance artifacts (backlog + decisions).
4. Slice 4: complete Document/Operate/Publish artifacts for this work item.

## Change Strategy
- Migration/rollout sequence:
  - write/execute failing tests first
  - implement selector in shell wrapper
  - validate template-source lane and targeted contract tests
  - finalize SDD artifacts and publish context
- Backward compatibility policy:
  - keep `make infra-contract-test-fast` entrypoint unchanged
  - preserve existing template-source strict behavior for selected tests
- Rollback plan:
  - revert selector + contract tests
  - rerun `make infra-contract-test-fast` and `make quality-hooks-fast`

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_includes_template_source_only_tests_in_template_source_mode tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_skips_template_source_only_tests_in_generated_consumer_mode tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing -v`
- Contract checks:
  - `make infra-contract-test-fast`
  - `make infra-validate`
  - `make quality-hooks-fast`
- Integration checks:
  - none (scope is wrapper contract behavior)
- E2E checks:
  - none

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
- Notes: no app lane behavior changed.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - SDD artifact updates + decision/backlog synchronization.
- Consumer docs updates:
  - none.
- Mermaid diagrams updated:
  - ADR component and timeline diagrams for Issue #103.
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
  - emit deterministic selection metrics (`infra_contract_test_fast_test_selection_total`) for selected and skipped groups.
- Alerts/ownership:
  - fast-lane failures are owned by blueprint maintainers.
- Runbook updates:
  - none.

## Risks and Mitigations
- Risk 1: accidental broad skipping could hide true regressions.
  - Mitigation: skip set is explicit and limited to template-source-only tests; shared infra tests still execute in generated-consumer mode.
- Risk 2: contract-runtime mode resolution drift.
  - Mitigation: use canonical runtime helpers (`blueprint_repo_mode`, `blueprint_repo_mode_from`, `blueprint_repo_mode_to`) and dedicated tests.
