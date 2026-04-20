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
1. Slice 1: add fast parity tests that assert optional-module contract `required_env` coverage by fixture helper output.
2. Slice 2: refactor `module_flags_env` to derive required env defaults for enabled modules through canonical resolver logic.
3. Slice 3: include parity tests in `infra-contract-test-fast` and run fast quality bundles.
4. Slice 4: finalize docs-phase operational/publish artifacts and backlog/decision synchronization.

## Change Strategy
- Migration/rollout sequence:
  - write failing parity test assertions
  - update helper hydration logic to satisfy parity
  - wire fast lane execution path
  - run required validation commands and update SDD artifacts
- Backward compatibility policy:
  - maintain existing `module_flags_env` call signature and existing env flag keys
  - preserve explicit caller overrides (`env.setdefault`) semantics
- Rollback plan:
  - revert helper + parity-test + fast-lane script edits
  - rerun `make infra-contract-test-fast` and `make quality-hooks-fast`

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_init_repo_env -v`
- Contract checks:
  - `pytest -q tests/infra/test_optional_module_required_env_contract.py`
  - `make infra-contract-test-fast`
  - `make quality-hooks-fast`
  - `make infra-validate`
- Integration checks:
  - `pytest -q tests/infra/test_optional_modules.py -k "test_postgres_module_flow or test_workflows_module_flow"`
- E2E checks:
  - not required (fixture + contract-test scope)

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
- Notes: no `apps/**` or app lane contract behavior changed.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - SDD artifact updates only; no user-facing docs behavior changes.
- Consumer docs updates:
  - none.
- Mermaid diagrams updated:
  - ADR decision and timeline diagrams for Issue #130 scope.
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
  - no new runtime metrics; contract parity diagnostics provided by deterministic test failure output.
- Alerts/ownership:
  - CI fast-lane failures on parity drift owned by blueprint maintainers.
- Runbook updates:
  - no operator runbook changes required.

## Risks and Mitigations
- Risk 1: new optional module added without helper signature alignment.
  - Mitigation: parity test asserts module-to-helper-flag mapping presence.
- Risk 2: required env defaults become empty in canonical resolver map.
  - Mitigation: parity test asserts non-empty values for every required env variable.
