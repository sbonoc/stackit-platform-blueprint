# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Documentation-only scope — one README, one bootstrap template mirror. No script, contract, or Helm changes.
- Anti-abstraction gate: No new abstractions. Changes are additive prose and a table in two Markdown files.
- Integration-first testing gate: N/A — no new code paths. Validation is `make quality-hooks-fast` (docs lint, bootstrap drift check) and `make quality-docs-check-changed`.
- Positive-path filter/transform test gate: N/A — no filter or transform logic.
- Finding-to-test translation gate: N/A — no reproducible pre-PR smoke findings in this scope.

## Delivery Slices

1. **Slice 1 — Live README hardening**: Add Environment Variables table, Make Targets table, Provisioning Lifecycle section, Security section, and Teardown section to `docs/platform/modules/identity-aware-proxy/README.md`.
2. **Slice 2 — Bootstrap template mirror**: Mirror all additions from Slice 1 to `scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md`.

## Change Strategy
- Migration/rollout sequence: Slice 1 first, Slice 2 immediately after. Both committed together in one PR.
- Backward compatibility policy: Fully additive — no existing prose removed, no contracts changed.
- Rollback plan: Revert the PR. No runtime side effects.

## Validation Strategy (Shift-Left)
- Unit checks: n/a
- Contract checks: `make quality-docs-check-changed` — detects bootstrap template drift vs. live README.
- Integration checks: `make quality-hooks-fast` — runs docs lint (markdown target validation), shellcheck, SDD gate, bootstrap template drift check.
- E2E checks: n/a

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
- Notes: Documentation-only PR. No make target changes.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/identity-aware-proxy/README.md` — add five missing sections.
- Consumer docs updates: `scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md` — mirror all additions.
- Mermaid diagrams updated: architecture.md sequence diagram (spec-only; not added to README).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route or filter changes.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: No changes. All existing lifecycle scripts already emit metric telemetry.
- Alerts/ownership: No changes.
- Runbook updates: README IS the runbook for this module; additions constitute the runbook update.

## Risks and Mitigations
- Risk 1: Bootstrap template drift after future README edits → mitigated by the `quality-docs-check-changed` pre-push hook which rejects divergence automatically.
