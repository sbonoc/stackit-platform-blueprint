# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Single-file assertion addition in `template_smoke_assertions.py`; no new abstractions, no helper modules.
- Anti-abstraction gate:
  - Assertion logic is inline in `main()` after the existing kustomization resource check; no wrapper layer.
- Integration-first testing gate:
  - Unit test asserts template file consistency (kustomization template filenames match descriptor template filenames) before implementation of the assertion itself.
- Positive-path filter/transform test gate:
  - The assertion uses filename extraction (Path(...).name and convention-default derivation); one positive-path unit test MUST verify a fully consistent descriptor+kustomization pair returns no assertion error.
- Finding-to-test translation gate:
  - The pre-patch failure (4 kustomization membership errors in infra-validate) is translated to a failing unit test against the template files; the assertion implementation turns it green.

## Delivery Slices
1. Slice 1 — assertion implementation: extend `template_smoke_assertions.py:main()` with the descriptor-kustomization cross-check block when `APP_RUNTIME_GITOPS_ENABLED=true`; handle convention-default manifest paths using the same defaulting logic as `_resolve_manifest_path`.
2. Slice 2 — test coverage: add unit tests in `tests/blueprint/` covering (a) consistent templates pass, (b) missing filename raises AssertionError with named message, (c) template file content agreement (FR-002/AC-003).

## Change Strategy
- Migration/rollout sequence: single commit on branch, no staged rollout; change is additive (assertion added, no behavior removed).
- Backward compatibility policy: fully backward compatible — existing template smoke passes if templates are consistent; new assertion only adds earlier-stage failure for drift that already causes infra-validate to fail.
- Rollback plan: revert the `template_smoke_assertions.py` assertion block; infra-validate continues to catch membership errors in consumer repos.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_template_smoke_assertions.py` (new file) — consistent-pair pass, missing-filename fail with message, convention-default path handling.
- Contract checks: `make quality-sdd-check` (SDD asset compliance); `make quality-hooks-fast`.
- Integration checks: `make blueprint-template-smoke` against the current consistent templates exits 0.
- E2E checks: `make quality-ci-generated-consumer-smoke` (runs the full template smoke in CI mode).

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
- App onboarding impact: no-impact
- Notes: change is limited to blueprint tooling (template smoke assertion); no consumer app targets, ports, or scaffolding are affected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none required — the fix is a tooling-only change; no new consumer-facing contract is introduced.
- Consumer docs updates: none required.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable — this change does not touch HTTP route handlers, query/filter logic, or API endpoints.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no new logs/metrics; AssertionError message in CI stdout is the only new observable output.
- Alerts/ownership: blueprint maintainer owns the template smoke CI lane.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1 — convention-default path handling: if the descriptor uses a component with no explicit `manifests:` block, the assertion must derive the convention-default filename rather than extracting from None. Mitigation: copy the defaulting expression `{component_id}-{kind}.yaml` from `_resolve_manifest_path` into the assertion extraction logic.
