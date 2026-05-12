# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Each fix is a targeted single-line or single-block edit to `scripts/lib/docs/site.sh`. No new abstractions, no new files, no new Make targets.
- Anti-abstraction gate: `--ignore-workspace` is a flag on existing pnpm calls; no wrapper function needed. Error message is inline text in `log_fatal`; no helper or template introduced.
- Integration-first testing gate: Each slice writes a failing pytest content-level regression test before the fix, then turns it green (red→green TDD order per slice).
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic introduced.
- Finding-to-test translation gate: Both defects were reproduced in the dhe-marketplace consumer upgrade (PR sbonoc/dhe-marketplace#62); each became a failing automated test before the fix was applied.

## Delivery Slices

### Slice 1 — Restore --ignore-workspace (#272, FR-001, AC-001)

**Objective:** Restore `--ignore-workspace` to `docs_pnpm_install`, `docs_pnpm_build`, and `docs_pnpm_start` in `scripts/lib/docs/site.sh`. Restore the explanatory comment alongside `docs_pnpm_install`.

**Red:** Write a pytest regression fixture that reads `scripts/lib/docs/site.sh` and asserts all three pnpm invocations contain `--ignore-workspace`. Confirm RED (currently absent from all three).

**Green:** Restore `--ignore-workspace` to the three functions and the explanatory comment.

**Slice gate:** `uv run python3 -m pytest tests/infra/ -k "issue_272" -v` → PASS.

### Slice 2 — Improve pnpm version assertion error message (#273, FR-002, AC-002)

**Objective:** Rewrite the `log_fatal` message in `_docs_assert_pnpm_version` to enumerate all three sources of pnpm version truth: docs `package.json` `packageManager` (canonical), root `package.json` `packageManager` (corepack auto-activation), CI corepack prepare pin.

**Red:** Write a pytest regression fixture that reads `scripts/lib/docs/site.sh` and asserts the `log_fatal` message mentions "root package.json" and "corepack prepare". Confirm RED.

**Green:** Replace the single-line error message in `_docs_assert_pnpm_version` with a multi-part message that names all three sources.

**Slice gate:** `uv run python3 -m pytest tests/infra/ -k "issue_273" -v` → PASS.

## Change Strategy
- Migration/rollout sequence: Slices 1 and 2 are independent single-file edits to `scripts/lib/docs/site.sh`; deliver in order 1→2 to maintain green tests at each boundary.
- Backward compatibility policy: Both changes are additive (Slice 1 restores a previously-present flag; Slice 2 expands error message text). No consumer that currently succeeds is broken.
- Rollback plan: Revert `scripts/lib/docs/site.sh` to the prior commit. Single-file revert with no side effects.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/ -k "issue_272 or issue_273" -v` after each slice.
- Contract checks: `make docs-build && make docs-smoke` after Slice 1 to verify the pnpm invocations still function correctly.
- Integration checks: none required — content-level regression tests cover the critical properties.
- E2E checks: covered by the existing `blueprint-upgrade-consumer` CI e2e job on reference consumer.

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
- Notes: No app delivery workflow, Make-target contract, or port-forward wrappers affected. All targets listed for gate compliance; none are modified by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — `scripts/lib/docs/site.sh` is a script, not a docs surface. `docs/blueprint/architecture/execution_model.md` does not cover pnpm invocation details.
- Consumer docs updates: `docs/platform/consumer/troubleshooting.md` MUST add a v1.10.0 docs build section covering the --ignore-workspace regression (#272) and the pnpm version mismatch migration steps (#273). Mirror to bootstrap template.
- Mermaid diagrams updated: none in docs — ADR diagrams are in the spec artifacts only.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP routes touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no new observability signals; `log_fatal` output preserved with expanded message text for #273.
- Alerts/ownership: none — docs build failures surface in CI; no alert configuration needed.
- Runbook updates: `docs/platform/consumer/troubleshooting.md` updated with v1.10.0 docs build section.

## Risks and Mitigations
- Risk 1 (consumer pnpm workspace includes docs/) → mitigation: `--ignore-workspace` is safe for both consumers that include and exclude `docs/`; it simply forces standalone resolution regardless, which is the correct behavior for an intentionally self-contained Docusaurus workspace.
- Risk 2 (improved error message verbosity) → mitigation: `log_fatal` already exits with non-zero; expanded text does not change exit behavior or artifact schemas.
