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
1. Slice 1: add upgrade reconcile-report contract and artifact emission in upgrade plan/apply flow.
2. Slice 2: extend preflight merge-risk classification from reconcile buckets and add deterministic hint mapping.
3. Slice 3: add postcheck make target + wrapper + python gate + metrics and repo-mode-aware docs hooks.
4. Slice 4: update docs/skills/contracts/tests and validate end-to-end.

## Change Strategy
- Migration/rollout sequence:
  - implement reconcile artifact generation + schema
  - wire wrapper env/args/metrics and preflight enrichment
  - add postcheck target and deterministic report
  - update docs/skill runbooks and contract metadata surfaces
  - run targeted + contract validation bundles
- Backward compatibility policy:
  - keep existing `upgrade_plan.json`/`upgrade_apply.json` fields stable
  - add new artifact/fields as additive; no removal of current keys
- Rollback plan:
  - revert changed upgrade/preflight/postcheck scripts, make targets, and contract/docs updates
  - rerun `make infra-validate` and `make quality-hooks-fast`

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer`
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight`
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer_wrapper`
  - `python3 -m unittest tests.blueprint.test_quality_contracts`
- Contract checks:
  - `make infra-validate`
  - `make quality-hooks-fast`
- Integration checks:
  - not required (script/report scope)
- E2E checks:
  - not required (script/report scope)

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
- Notes: no `apps/**` functional scope changes; required targets remain unchanged.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - update command reference and upgrade guardrail sections (`docs/README.md` + template mirror)
  - update architecture execution model + consumer quickstart/troubleshooting upgrade flow
- Consumer docs updates:
  - update skill runbooks (source + consumer template fallback) for reconcile/postcheck usage
- Mermaid diagrams updated:
  - ADR decision diagram for preflight/reconcile/postcheck composition
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
  - emit reconcile bucket count metrics and postcheck status metrics from wrappers
- Alerts/ownership:
  - no new alert resources; CI gate outcome and report artifacts are canonical operator signals
- Runbook updates:
  - include safe-to-continue vs blocked contract in upgrade skill and troubleshooting docs

## Risks and Mitigations
- Risk 1: generated-consumer fixture regressions due stricter postcheck.
  - Mitigation: add fixture coverage for pass/fail postcheck states.
- Risk 2: docs/contract drift from new target/artifacts.
  - Mitigation: update `blueprint/contract.yaml`, template counterpart, and generated docs in same change.
