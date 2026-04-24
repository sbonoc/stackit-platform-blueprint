# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation (Slice order: 1 → 2 → 3)

### Slice 1 — Failing tests (red; implement BEFORE the fix)
- [x] T-001 Add `test_gate_passes_when_artifacts_present_and_seeded` to `tests/blueprint/test_upgrade_fresh_env_gate.py` — confirmed FAIL red before fix, PASS green after.
- [x] T-002 Add `test_gate_skips_seeding_when_artifacts_absent` to `tests/blueprint/test_upgrade_fresh_env_gate.py` — confirms no-op path does not error.

### Slice 2 — Fix (green)
- [x] T-003 Add artifact-seeding block to `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` immediately after `worktree_created=true`, before the "Run targets inside the clean worktree" block. Run full test suite and confirm all tests PASS.

### Slice 3 — Docs
- [x] T-004 Update `docs/blueprint/architecture/execution_model.md` to document the artifact-seeding step in the fresh-env gate section.

## Validation and Release Readiness
- [x] T-201 Run `python3 -m pytest tests/blueprint/test_upgrade_fresh_env_gate.py -v` — 18/18 passed.
- [x] T-202 Run `python3 -m pytest tests/blueprint/ -v` — full blueprint suite, no regressions.
- [x] T-203 Run `make quality-hooks-fast` — passes.
- [x] T-204 Run `make quality-docs-check-changed` — passes after bootstrap template sync.
- [x] T-205 Validation evidence recorded in `pr_context.md` and `hardening_review.md`.
- [x] T-206 Run `make quality-hardening-review` — passes.

## Publish
- [x] P-001 Update `hardening_review.md` with findings and proposals-only section.
- [x] P-002 Update `pr_context.md` with REQ/AC coverage, key reviewer files, test evidence, and rollback notes.
- [x] P-003 Ensure PR description references `pr_context.md` and issue #182.

## App Onboarding Minimum Targets (Normative)
- App onboarding impact: no-impact — tooling-only change; no app onboarding surface modified.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — not applicable (no-impact)
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — not applicable (no-impact)
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — not applicable (no-impact)
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — not applicable (no-impact)
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — not applicable (no-impact)
