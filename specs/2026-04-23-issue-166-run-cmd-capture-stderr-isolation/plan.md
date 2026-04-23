# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: single-line removal of `2>&1` in `run_cmd_capture`; one doc comment added; one structural test. No new files beyond the ADR.
- Anti-abstraction gate: no new helper variants introduced; the fix corrects the existing primitive directly.
- Integration-first testing gate: structural test in `contract_refactor_scripts_cases.py` added before any further integration work.
- Positive-path filter/transform test gate: no filter or payload-transform logic; gate not applicable to this shell utility fix.
- Finding-to-test translation gate: pre-PR finding (stderr merged into stdout in `run_cmd_capture`) translated to `test_run_cmd_capture_does_not_merge_stderr_into_stdout`, which asserts the `2>&1` pattern is absent from the function body.

## Delivery Slices
1. Slice 1 — Shell fix + doc comment + structural test: remove `2>&1` from `run_cmd_capture` in `scripts/lib/shell/exec.sh`; add inline doc comment above the function definition; add structural assertion in `tests/blueprint/contract_refactor_scripts_cases.py`.

## Change Strategy
- Migration/rollout sequence: additive to existing behavior — callers are unchanged; the fix is inherited automatically.
- Backward compatibility policy: fully backward-compatible; all existing call sites redirect to files or `/dev/null` and do not rely on stderr being merged.
- Rollback plan: revert the commit; no persistent state introduced.

## Validation Strategy (Shift-Left)
- Unit checks: `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k run_cmd_capture -v`
- Contract checks: `shellcheck --severity=error scripts/lib/shell/exec.sh`
- Integration checks: `make quality-hooks-fast` exercises the full fast-lane gate including shellcheck on all `scripts/lib/**/*.sh`.
- E2E checks: not applicable (no cluster state changed).

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
- App onboarding impact: no-impact — blueprint shell utility only; no app lane behavior changes.
- Notes: `run_cmd_capture` is used only in blueprint-internal scripts; no app onboarding paths are affected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — the doc comment in the function is the authoritative documentation for this primitive.
- Consumer docs updates: none.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP route/filter changes).
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no new metrics; stderr from subprocesses becomes directly visible on success and failure, improving diagnosability without code changes.
- Alerts/ownership: none required.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1 (a caller depends on stderr being merged into stdout) → mitigation: all 12 call sites investigated; none rely on stderr being merged. The risk is negligible.
