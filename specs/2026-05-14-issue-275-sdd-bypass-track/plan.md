# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two new fields added to spec.md readiness section (`SPEC_READY_EXCEPTION`, `authorized-by`); one conditional branch added to `check_sdd_assets.py`; one metric line emitted. No new abstractions, no new files beyond the test file.
- Anti-abstraction gate: Exception logic is a direct conditional in the existing artifact-existence check loop — no new class, no wrapper, no strategy pattern.
- Integration-first testing gate: Tests use synthetic in-memory `spec.md` content and temp dirs — realistic coverage of the gate logic without a live cluster or CI runner.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in this work item.
- Finding-to-test translation gate: The motivating finding (10-stub artifact ceremony for non-feature changes) is translated into AC-001 through AC-005 regression tests that assert the bypass path is correct and the full-SDD path is not regressed.

## Delivery Slices

### Slice 1 — Failing tests (red) + checker + scaffold update (green)

Write failing regression tests for AC-001 through AC-005, then implement the checker change and scaffold update to turn them green.

**Files touched:**
- `tests/blueprint/test_sdd_bypass_track.py` (new)
- `scripts/bin/quality/check_sdd_assets.py`
- `scripts/bin/blueprint/spec_scaffold.py` (or the spec.md template it reads from)
- `scripts/lib/quality/test_pyramid_contract.json` (register new test file)

**Steps (red → green):**
1. Write `tests/blueprint/test_sdd_bypass_track.py` with AC-001 through AC-005 test cases.
2. Confirm all 5 tests fail (the bypass logic does not yet exist in `check_sdd_assets.py`).
3. Add `SPEC_READY_EXCEPTION` + `authorized-by` field parsing to `check_sdd_assets.py`.
4. Add conditional bypass branch: when exception is valid + `authorized-by` present, skip non-`{spec.md, pr_context.md}` artifact checks.
5. Add `authorized-by` required violation when exception is set but field is absent/empty/`none`.
6. Demote "implementation tasks checked while SPEC_READY not true" to warning when exception + `authorized-by` are set.
7. Emit `[METRIC] name=sdd_exception_gate_total value=1 type=<type> authorized_by=<handle>` on the bypass path.
8. Update `spec.md` scaffold template to include `SPEC_READY_EXCEPTION: none` and `authorized-by: none` in the Readiness Gate section.
9. Register `tests/blueprint/test_sdd_bypass_track.py` in `scripts/lib/quality/test_pyramid_contract.json` unit scope.
10. Confirm all 5 tests pass.
11. Run `make test-unit-all` — confirm no regressions.

### Slice 2 — AGENTS.md policy documentation

Add new subsection to `AGENTS.md` documenting the lightweight bypass track, allowed exception types, `authorized-by` requirement, and per-type minimum traceability expectations.

**Files touched:**
- `AGENTS.md`

**Steps:**
1. Add `## Lightweight SDD Bypass Track` subsection to `AGENTS.md` covering: allowed `SPEC_READY_EXCEPTION` values, `authorized-by` requirement, per-type minimum artifact set, chore-with-no-specs-dir convention (record in `AGENTS.decisions.md`), and metric emitted for audit.
2. Run `make quality-sdd-check-all` — confirm no regressions.
3. Run `make quality-hooks-fast` — confirm all gates pass.

## Change Strategy
- Migration/rollout sequence: scaffold template updated atomically with checker — no existing `spec.md` requires modification (new fields default to `none`).
- Backward compatibility policy: fully additive; existing `spec.md` files without the new fields are treated as `SPEC_READY_EXCEPTION: none` (full-SDD path). No file migration required.
- Rollback plan: remove `SPEC_READY_EXCEPTION` and `authorized-by` from a spec.md to restore full-SDD enforcement immediately. Revert `check_sdd_assets.py` to remove the bypass branch.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_sdd_bypass_track.py -v` (AC-001 through AC-005) + `make test-unit-all`
- Contract checks: `make quality-sdd-check` (self-consistency gate, AC-006)
- Integration checks: N/A — no running services touched.
- E2E checks: N/A — no live cluster required.

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
- Notes: No app onboarding make targets are modified by this work item. All targets above remain unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `AGENTS.md` — new `## Lightweight SDD Bypass Track` subsection.
- Consumer docs updates: none — consumer repos inherit AGENTS.md changes via bootstrap-template sync.
- Mermaid diagrams updated: `architecture.md` flowchart diagram; no `docs/` Mermaid pages.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP routes or API endpoints changed.
- Publish checklist:
  - Requirement coverage: FR-001–007, NFR-SEC/OBS/REL, AC-001–006
  - Key reviewer files: `scripts/bin/quality/check_sdd_assets.py`, `tests/blueprint/test_sdd_bypass_track.py`, `AGENTS.md`
  - Validation evidence: pytest output + quality-sdd-check PASS
  - Rollback notes: remove exception fields from spec.md; revert check_sdd_assets.py

## Operational Readiness
- Logging/metrics/traces: `[METRIC] name=sdd_exception_gate_total` emitted to stdout on bypass path; visible in CI job logs.
- Alerts/ownership: none — quality gate metric for audit visibility only.
- Runbook updates: none — AGENTS.md subsection is the operator-facing guide.

## Risks and Mitigations
- Risk 1: Exception mechanism could be misused to bypass full SDD on feature work. Mitigation: `SPEC_READY_EXCEPTION` is only valid when `SPEC_READY: false`; any spec with `SPEC_READY: true` + exception set is flagged as a violation. Code review provides the human gate.
- Risk 2: Scaffold template update doesn't propagate to consumer-repo spec templates immediately. Mitigation: consumer repos receive the update on next blueprint upgrade via bootstrap-template sync; the bypass track is opt-in so no consumer is affected until they explicitly set the field.
