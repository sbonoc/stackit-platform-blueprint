# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Change is a single conditional branch added at the top of `parse_literal_pairs()`. No new abstractions.
- Anti-abstraction gate:
  - No wrapper layer introduced. The bash `while IFS= read -r pair` idiom replaces the array-based split directly.
- Integration-first testing gate:
  - Test for the comma-in-value scenario (AC-001) written first as a failing test, then fixed (SDD-C-024).
- Positive-path filter/transform test gate:
  - `parse_literal_pairs` is a filter/transform: at least one test MUST assert a matching input returns a correctly parsed output record with the full value preserved (SDD-C-023).
- Finding-to-test translation gate:
  - Issue #234 is a reproducible failure. The test for `NUXT_OIDC_TOKEN_KEY=data:;base64,...` MUST be written as a failing test before the fix is applied (SDD-C-024).

## Delivery Slices

### Slice 1 — Failing regression test + parse fix (red→green)
1. Add failing test in `tests/infra/test_runtime_credentials_eso.py` that passes `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` as a newline-separated string containing a comma-in-value (data URI). Confirm it fails against the current `parse_literal_pairs()`.
2. Update `parse_literal_pairs()` in `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh`:
   - Add delimiter-detection branch: if no `\n` in input, convert commas to newlines (legacy path); else use input as-is (newline path).
   - Replace `IFS=',' read -r -a raw_pairs <<<"$literals_csv"` + for-loop with `while IFS= read -r pair; done <<< "$literals"`.
   - Confirm failing test now passes. Confirm existing comma-separated tests still pass.
3. Update `record_reconcile_issue` error message to reference both formats.

### Slice 2 — Documentation update
1. Update `docs/platform/consumer/runtime_credentials_eso.md`:
   - Mark newline-separated as recommended format; mark comma-separated as legacy (values without commas only).
   - Update usage example to newline-separated form with `$'...'` quoting.
2. Update bootstrap template copy: `scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md` — same changes.
3. Run `make docs-build && make docs-smoke`.

## Change Strategy
- Migration/rollout sequence: parser fix ships in one commit; docs update ships in the same PR. No consumer migration required — legacy format remains valid.
- Backward compatibility policy: comma-separated format is preserved for inputs with no newlines. Consumers using newline-separated format (the workaround) require no changes.
- Rollback plan: revert `parse_literal_pairs()` to comma-only split; any consumer using the workaround would need to revert their serializer as well.

## Validation Strategy (Shift-Left)
- Unit checks: shell-level `parse_literal_pairs()` behavior via Python subprocess tests in `tests/infra/test_runtime_credentials_eso.py`.
- Contract checks: dry-run reconcile with newline-separated literal containing comma-in-value; verify rendered secret YAML contains the full value base64-encoded.
- Integration checks: existing dry-run reconcile test suite in `tests/infra/test_runtime_credentials_eso.py`.
- E2E checks: not required for this change; no infrastructure topology changes.

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
- Notes: `parse_literal_pairs()` is called only during auth reconciliation; app onboarding Make targets are unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none (this is platform track, not blueprint track).
- Consumer docs updates: `docs/platform/consumer/runtime_credentials_eso.md` + bootstrap template copy.
- Mermaid diagrams updated: none (architecture.md diagram is work-item-scoped, not a published doc diagram).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP endpoints touched.
- Publish checklist:
  - include FR-001…FR-004 and AC-001…AC-003 coverage in `pr_context.md`
  - include key reviewer files: `reconcile_eso_runtime_secrets.sh`, `test_runtime_credentials_eso.py`, updated doc files
  - include test evidence (pass/fail summary)
  - include rollback note

## Operational Readiness
- Logging/metrics/traces: `record_reconcile_issue` call preserved; error message updated. Existing `reconcile_issue_total` metric emitted on parse failure remains.
- Alerts/ownership: no new alerts required.
- Runbook updates: `docs/platform/consumer/runtime_credentials_eso.md` and `troubleshooting.md` format examples updated.

## Risks and Mitigations
- Risk 1: Consumer scripts may rely on the exact reconcile-issue message string for parsing → mitigation: check if any scripts grep for this string before changing it; update if found.
