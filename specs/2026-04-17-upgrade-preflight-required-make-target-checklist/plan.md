# Implementation Plan

## Implementation Start Gate
- Implementation is allowed with `SPEC_READY=true` and required sign-offs approved in `spec.md`.
- Missing-input blocker token is not active for this work item.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep changes scoped to preflight/manual-action diagnostics, tests, and consumer-facing upgrade docs.
  - Reuse existing contract metadata and follow-up command surfaces.
- Anti-abstraction gate:
  - Extend existing planner functions instead of introducing a new diagnostics subsystem.
  - Preserve existing `RequiredManualAction` payload shape.
- Integration-first testing gate:
  - Add failing regression for missing contract-required consumer target without invoker reference, then implement fix.
- Positive-path filter/transform test gate:
  - Not applicable for this work item; no route/filter payload logic changes.
- Finding-to-test translation gate:
  - Reproducible finding (`missing target undetected in preflight`) is translated to a failing unit test first and turned green with implementation.

## Delivery Slices
1. Slice 1: finalize Discover/Architecture/Specify artifacts with approved ADR linkage.
2. Slice 2: add failing regression test for contract-required missing consumer-owned Make target detection gap.
3. Slice 3: implement planner logic for fallback contract dependency context and deterministic location guidance.
4. Slice 4: update consumer upgrade docs, execute validation, and finalize publish artifacts.

## Change Strategy
- Migration/rollout sequence:
  - add regression test (red).
  - implement planner fix (green).
  - update docs to explain checklist guarantees.
  - run validation bundles and package publish artifacts.
- Backward compatibility policy:
  - no contract schema changes; existing required-manual-action consumers remain compatible.
- Rollback plan:
  - revert planner/test/docs changes and rerun targeted validation.

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer`
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight`
- Contract checks:
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`
- Integration checks:
  - `make quality-hooks-fast`
- E2E checks:
  - not applicable for this planner/docs scope.

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
- Notes: this work item touches upgrade planning diagnostics and docs only.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - none.
- Consumer docs updates:
  - `docs/platform/consumer/quickstart.md`
  - `docs/platform/consumer/troubleshooting.md`
- Mermaid diagrams updated:
  - not required.
- Docs validation commands:
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - not applicable; no HTTP route/filter/new endpoint changes.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces:
  - no runtime telemetry changes; deterministic required-manual-action diagnostics are enhanced.
- Alerts/ownership:
  - upgrade operators own manual-action resolution before validate/apply.
- Runbook updates:
  - consumer quickstart/troubleshooting clarify missing-target checklist behavior.

## Risks and Mitigations
- Risk 1: higher manual-action volume on legacy consumer repos can overwhelm operators.
- Mitigation 1: include exact target names, expected location guidance, and canonical follow-up command.

## Rollback Notes
- Revert this work-item diff and rerun:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer`
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight`
  - `make quality-hooks-fast`
