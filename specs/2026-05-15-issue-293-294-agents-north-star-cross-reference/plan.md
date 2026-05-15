# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two focused deliverables — a template text change and a single-file Python script. No shared abstractions, no new frameworks.
- Anti-abstraction gate: Use `pathlib`, `re`, and `sys` directly in the script. PyYAML for allowlist parsing (already a declared dependency). No wrapper classes around file I/O.
- Integration-first testing gate: Not applicable — no service boundary interactions. Unit tests drive detection logic (red → green TDD per slice).
- Positive-path filter/transform test gate: Not applicable — no filter/payload-transform logic in the script. The detection logic is heading-set intersection, not record filtering.
- Finding-to-test translation gate: The dhe-marketplace duplication pattern is the triggering finding. AC-003 translates it into a failing test (AGENTS.md heading matches north_star.md heading → violation). The fix turns it green.

## Delivery Slices

1. Slice 1 — AGENTS.md template + blueprint AGENTS.md update (closes #293): Add "Architecture Invariants — Pointers" section and north_star.md MUST-read Mandatory Workflow rule (FR-002) to `scripts/templates/consumer/init/AGENTS.md.tmpl`. Add the same north_star.md MUST-read rule (FR-007) to blueprint's own `AGENTS.md`. Write failing unit tests for AC-001, AC-002, AC-008 (template/blueprint content assertions); turn green with the text updates. Run `make quality-hooks-fast`.

2. Slice 2 — Cross-reference quality hook (closes #294): Write failing unit tests for AC-003 through AC-007 (heading detection, Pointers-table exemption, allowlist, graceful skip). Implement `scripts/bin/quality/check_docs_cross_reference.py`. Add `quality-docs-cross-reference-check` make target to `make/blueprint.generated.mk`. Wire into `scripts/bin/quality/hooks_fast.sh`. Turn tests green. Run `make quality-hooks-fast`.

## Change Strategy
- Migration/rollout sequence: Additive only. Slice 1 is a template text change; existing consumers are unaffected until they re-run init or explicitly pull the updated template. Slice 2 adds a new make target and hook invocation — existing consumers see the hook on blueprint upgrade; clean consumers pass immediately.
- Backward compatibility policy: No existing behavior is removed or modified. The new hook is an additive check. Consumers with pre-existing AGENTS.md ↔ north_star.md heading overlap will see violations on upgrade; the allowlist mechanism provides a structured escape hatch.
- Rollback plan: Revert `AGENTS.md.tmpl` text change (Slice 1). Remove `check_docs_cross_reference.py`, the make target from `make/blueprint.generated.mk`, and the `hooks_fast.sh` invocation (Slice 2). No consumer data affected.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_docs_cross_reference.py` — covers AC-003 through AC-007. Template assertions for AC-001 + AC-002 via content checks on the updated `AGENTS.md.tmpl`.
- Contract checks: `make infra-contract-test-fast` — validates make target list and hook wiring.
- Integration checks: `make quality-hooks-fast` — full fast hook suite including the new check against the blueprint repo itself.
- E2E checks: N/A — local tooling only; no runtime or service boundary involved.

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
- Notes: tooling-only change; no app delivery workflow targets are added or modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/decisions/ADR-issue-293-294-agents-north-star-cross-reference.md` — advance status from proposed to approved. `docs/blueprint/core_targets.md` will auto-update via `make quality-docs-sync-core-targets` once the new make target is added.
- Consumer docs updates: none required — the template update is self-documenting (the new section includes the instruction inline).
- Mermaid diagrams updated: architecture.md flowchart documents the detection flow; no consumer-facing diagram changes.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP routes touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: Violations printed to stdout with `[quality-docs-cross-reference-check]` prefix; exit code is the signal. No new metrics or traces owned by this tooling.
- Alerts/ownership: Blueprint maintainer owns the script. No alerting changes.
- Runbook updates: None required.

## Risks and Mitigations
- Risk 1: Consumers with existing AGENTS.md ↔ north_star.md heading overlap will see hook failures on blueprint upgrade -> mitigation: `.quality-docs-cross-reference-allowlist.yml` with required `justification` field provides a structured escape hatch; upgrade notes should flag the new hook.
- Risk 2: Pointers-table exemption requires exact heading text match -> mitigation: template instructions and ADR explicitly state that the Pointers-table domain name MUST match the north_star.md heading text exactly; mismatch means the author must either fix the row or add an allowlist entry.
