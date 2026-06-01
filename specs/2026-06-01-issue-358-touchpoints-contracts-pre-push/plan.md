# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Change is a single YAML stanza addition to one template file plus one pytest unit test. No abstractions introduced.
- Anti-abstraction gate:
  - Direct YAML edit; no wrapper or helper introduced. Hook fields are spelled out explicitly per FR-001.
- Integration-first testing gate:
  - Unit test (T-101, T-102) asserts the hook fields in the static YAML template — deterministic and environment-independent.
  - Drift gate (T-103) uses `make quality-validate-bootstrap-template-drift` to verify no blueprint-managed file diverges.
- Positive-path filter/transform test gate:
  - N/A — no filter or payload-transform logic.
- Finding-to-test translation gate:
  - If `make quality-validate-bootstrap-template-drift` fails after the template edit, the root cause MUST become a failing test before the fix lands.

## Delivery Slices

1. Slice 1 — Red: Write `tests/blueprint/test_touchpoints_contracts_hook.py` asserting:
   - The hook `touchpoints-test-contracts-pre-push` is present in the parsed YAML of `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`.
   - The hook has `entry: make touchpoints-test-contracts`, `language: system`, `pass_filenames: false`, `always_run: false`, `stages: [pre-push]`, and `files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$`.
   - The hook is NOT in any `stages: [commit]` hook list (AC-002).
   - This test MUST fail before the template is modified.

2. Slice 2 — Green: Add the `touchpoints-test-contracts-pre-push` hook stanza to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` immediately after the existing `quality-consumer-pre-push` hook. Run `uv run python3 -m pytest tests/blueprint/test_touchpoints_contracts_hook.py` — all assertions MUST pass.

3. Slice 3 — Verify: Run `make quality-validate-bootstrap-template-drift` to confirm no drift between the modified template and any blueprint-managed derived file. Run `make quality-sdd-check` to confirm all SDD gates pass. Capture exit codes in traceability evidence.

4. Slice 4 — Document: Add a backport note entry to the blueprint upgrade documentation (`docs/blueprint/consumer/upgrade_summary.md` or equivalent) describing the new hook, its `files` trigger pattern, and the action required for consumers with Pact contract tests on earlier template versions.

## Change Strategy
- Migration/rollout sequence: single template file edit; consumers pick it up on their next `make blueprint-upgrade` or manual `.pre-commit-config.yaml` sync from the updated template.
- Backward compatibility policy: `always_run: false` guarantees no behavioural impact on consumers without matching files or without a `tests/contracts/` directory.
- Rollback plan: revert the hook stanza from the template and cut a patch blueprint release; consumers re-sync their `.pre-commit-config.yaml` from the reverted template.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_touchpoints_contracts_hook.py` — asserts hook presence and all field values in the static YAML template.
- Contract checks: N/A — this change defines a contract test hook, not contract tests themselves.
- Integration checks: `make quality-validate-bootstrap-template-drift` — validates no drift between the modified template and blueprint-managed derived files.
- E2E checks: N/A — no user-facing flow.

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
- Notes: `touchpoints-test-contracts` is already in the minimum targets list; this work item adds a pre-push hook that invokes it but introduces no new make target.

## Documentation Plan (Document Phase)
- Blueprint docs updates: upgrade release notes / `docs/blueprint/consumer/upgrade_summary.md` — backport note for the new hook.
- Consumer docs updates: none beyond the upgrade note; the hook is self-describing via its `name:` field.
- Mermaid diagrams updated: architecture.md flowchart (already authored in this intake).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - N/A — no HTTP routes or API endpoints.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: N/A — hook output is terminal-only.
- Alerts/ownership: N/A.
- Runbook updates: N/A — no new operational runbook required; the hook is documented in the upgrade notes.

## Risks and Mitigations
- Risk 1 — `make touchpoints-test-contracts` does not exit 0 cleanly when contracts directory absent -> mitigation: verify this during Slice 3; if the target does not handle the absent-directory case, a `[ -d tests/contracts ] || exit 0` guard MUST be added to the make target before the hook is merged. This finding MUST be translated into a failing test per SDD-C-024.
