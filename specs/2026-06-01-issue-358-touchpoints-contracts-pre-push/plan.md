# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Change is three YAML stanza additions to one template file plus one pytest unit test file. No abstractions introduced.
- Anti-abstraction gate:
  - Direct YAML edits; no wrapper or helper introduced. Hook fields are spelled out explicitly per FR-001 through FR-003.
- Integration-first testing gate:
  - Unit tests (T-101 through T-104) assert all hook fields in the static YAML template — deterministic and environment-independent.
  - Drift gate (T-105) uses `make quality-validate-bootstrap-template-drift` to verify no blueprint-managed file diverges.
- Positive-path filter/transform test gate:
  - N/A — no filter or payload-transform logic.
- Finding-to-test translation gate:
  - If `make quality-validate-bootstrap-template-drift` fails after the template edit, the root cause MUST become a failing test before the fix lands.

## Delivery Slices

1. Slice 1 — Red: Write `tests/blueprint/test_pre_push_hooks.py` asserting all three hooks are absent from the parsed YAML of `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`. This test MUST fail (hooks do not yet exist). Assert for each hook: correct `id`, `entry`, `language`, `pass_filenames`, `always_run`, `stages`, and `files` fields.

2. Slice 2 — Green (touchpoints-unit): Add `touchpoints-test-unit-pre-push` hook stanza to the template. Run the test file — T-101 assertion MUST pass; T-102 and T-103 still fail.

3. Slice 3 — Green (touchpoints-contracts): Add `touchpoints-test-contracts-pre-push` hook stanza to the template immediately after the unit hook. Run test file — T-101 and T-102 MUST pass; T-103 still fails.

4. Slice 4 — Green (backend-unit): Add `backend-test-unit-pre-push` hook stanza. Run test file — T-101, T-102, T-103 MUST all pass. Run T-104 (no-commit-stage assertion) and T-105 (drift check) — both MUST pass.

5. Slice 5 — Verify: Run `make quality-validate-bootstrap-template-drift` (exit 0). Run `make quality-sdd-check` (exit 0). Capture exit codes as T-105 evidence in traceability.

6. Slice 6 — Document: Add a backport note to the blueprint upgrade documentation describing all three new hooks with their `files` trigger patterns and the make targets they invoke.

## Change Strategy
- Migration/rollout sequence: three hook stanzas added to the template in a single commit; consumers pick them up on their next blueprint upgrade or manual template sync.
- Backward compatibility policy: `always_run: false` on every hook guarantees no behavioural impact on consumers without matching files or without the relevant test directories.
- Rollback plan: revert the three hook stanzas from the template and cut a patch blueprint release; consumers re-sync from the reverted template.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_pre_push_hooks.py` — asserts all three hook IDs present with correct field values in the static YAML template.
- Contract checks: N/A — this change defines pre-push hooks, not contract tests themselves.
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
- Risk 1 — any of the three make targets does not exit 0 cleanly when the relevant test directory is absent -> mitigation: verify each target during Slice 5; if a target does not handle the absent-directory case, a guard MUST be added before the hook is merged, and the finding MUST be translated into a failing test per SDD-C-024.
- Risk 2 — `backend-test-unit-pre-push` has a broader Python file scope (`apps/backend/|tests/backend/`) and runs pytest; on slow machines or large test suites this adds more push latency than the Vitest hooks -> mitigation: file-scoped trigger limits invocations to backend source changes; acceptable tradeoff given the postmortem evidence (PR #78).
