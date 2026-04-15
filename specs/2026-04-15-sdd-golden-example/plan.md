# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Delivery Slices
1. Slice 1:
2. Slice 2:

## Change Strategy
- Migration/rollout sequence:
- Backward compatibility policy:
- Rollback plan:

## Validation Strategy (Shift-Left)
- Unit checks:
- Contract checks:
- Integration checks:
- E2E checks:

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
- Blueprint docs updates:
- Consumer docs updates:
- Mermaid diagrams updated:
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Operational Readiness
- Logging/metrics/traces:
- Alerts/ownership:
- Runbook updates:

## Risks and Mitigations
- Risk 1 -> mitigation:
