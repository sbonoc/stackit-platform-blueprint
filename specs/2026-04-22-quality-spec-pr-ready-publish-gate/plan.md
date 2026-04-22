# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: implement a single script with four focused check functions; no shared base class or plugin architecture; no config file for placeholder labels — keep them as module-level constants.
- Anti-abstraction gate: use `pathlib` and `re` directly; no custom markdown parser; line-by-line string matching is sufficient and avoids an external dependency.
- Integration-first testing gate: define test fixtures (minimal fully-filled and placeholder-only spec dirs) before implementing check logic; tests drive what the script MUST detect.
- Positive-path filter/transform test gate: positive-path tests assert that a fully-filled spec dir exits 0 and produces no violations; this is the primary regression guard.
- Finding-to-test translation gate: the triggering incident (issue-118-137 shipped with all-placeholder publish-gate files) is translated into per-file negative-path tests for each placeholder variant before the fix is implemented.

## Delivery Slices
1. Slice 1 — script + make target + makefile regeneration: create `scripts/bin/quality/check_spec_pr_ready.py`, add `quality-spec-pr-ready` to the makefile template, regenerate `make/blueprint.generated.mk`, add `tests/blueprint/test_spec_pr_ready.py`, run `make quality-hooks-fast` and `make infra-contract-test-fast` green.
2. Slice 2 — hooks integration + docs + ADR: wire `quality-spec-pr-ready` into `hooks_fast.sh` with branch-pattern guard, add ADR, run `make quality-docs-sync-all` and `make quality-hooks-fast` green end-to-end.

## Change Strategy
- Migration/rollout sequence: the make target is additive; `hooks_fast.sh` change is additive with a branch-pattern guard so existing non-SDD workflows are unaffected. No migration is required.
- Backward compatibility policy: the `quality-spec-pr-ready` target is a new addition; it does not replace or rename any existing target. `hooks_fast.sh` change is gated so it is transparent to non-SDD branch workflows.
- Rollback plan: remove the `quality-spec-pr-ready` target from both makefile files and the `hooks_fast.sh` invocation; rerun `make blueprint-render-makefile`. The script file can be left in place as it is not called except via the make target.

## Validation Strategy (Shift-Left)
- Unit checks: `tests/blueprint/test_spec_pr_ready.py` — positive-path (fully-filled spec dir exits 0), per-file negative-path (each placeholder type exits non-zero with correct message), branch-resolution, missing-spec-dir.
- Contract checks: `make infra-contract-test-fast` — includes `make quality-sdd-check` which validates makefile targets, scaffold wiring, and script presence; `make quality-docs-lint` validates no forward references in markdown.
- Integration checks: `make quality-hooks-fast` end-to-end on the SDD branch — exercises the `hooks_fast.sh` branch-pattern guard path live.
- E2E checks: none; this is local developer tooling.

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
- Notes: tooling-only change; no app runtime or API surface modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260422-quality-spec-pr-ready-publish-gate.md`; core-targets doc auto-updated by `make quality-docs-sync-core-targets`.
- Consumer docs updates: none; `quality-spec-pr-ready` is a blueprint-side tooling target not propagated to consumers.
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: violations are printed to stdout with `[quality-spec-pr-ready]` prefix; exit code is the machine-readable signal; no persistent metrics.
- Alerts/ownership: no runtime alerts; blueprint maintainer owns the script and allowlist.
- Runbook updates: none required; the script is self-documenting via its `--help` output and violation messages.

## Risks and Mitigations
- Risk 1: static placeholder label allowlist drifts from scaffold templates -> mitigation: per-label negative-path tests in `test_spec_pr_ready.py` catch drift at test time; template changes MUST update the test and the allowlist together.
- Risk 2: branch-pattern guard in `hooks_fast.sh` uses a bash regex — a typo silently skips the check on SDD branches -> mitigation: the pattern is tested manually during Verify phase; integration test covers the positive-path invocation.
