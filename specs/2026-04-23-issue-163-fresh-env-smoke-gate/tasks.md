# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (sbonoc, 2026-04-23)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Python report module + test fixtures

- [x] T-101 Create `tests/blueprint/fixtures/fresh_env_gate/pass_state/` — matched file-set snapshot for positive-path divergence diff test
- [x] T-102 Create `tests/blueprint/fixtures/fresh_env_gate/fail_state/` — mismatched file-set snapshot (absent bootstrap file) for negative-path divergence diff test
- [x] T-103 Create `scripts/lib/blueprint/upgrade_fresh_env_gate.py`:
  - `FreshEnvGateResult` dataclass with fields: `status` (pass|fail|error), `worktree_path`, `targets_run`, `divergences`, `error`, `exit_code`
  - `compute_divergences(worktree_path, working_tree_path) -> list[dict]` — file-set diff
  - `write_report(result, output_path) -> None` — JSON serialization
- [x] T-104 Create `tests/blueprint/test_upgrade_fresh_env_gate.py` with all eight test cases (see Test File Plan in plan.md)
- [x] T-105 Verify `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` — all green (16 passed in 2.44s)

## Slice 2 — Shell wrapper + EXIT trap

- [x] T-201 Create `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`:
  - Read `BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH` (default: `artifacts/blueprint/fresh_env_gate.json`)
  - Require `git`, `python3`, `make` on PATH
  - `git worktree add <tmpdir> HEAD` — hard fail (status=error) if non-zero
  - `trap "git worktree remove --force <tmpdir>" EXIT` — registered immediately after creation
  - Run `make infra-validate` inside worktree (`make -C <worktree>`)
  - Run `make blueprint-upgrade-consumer-postcheck` inside worktree (`make -C <worktree>`)
  - Delegate divergence diff + JSON report write to `upgrade_fresh_env_gate.py`
  - Emit `log_metric "blueprint_upgrade_fresh_env_gate_status_total" "1" "status=<pass|fail|error>"`
  - Inline stdout progress via `log_info` / `log_error`
- [x] T-202 Verify `bash -n scripts/bin/blueprint/upgrade_fresh_env_gate.sh` — no syntax errors
- [x] T-203 Verify shell wrapper integration tests in `test_upgrade_fresh_env_gate.py` pass

## Slice 3 — Make target + contract wiring

- [x] T-301 Add `blueprint-upgrade-fresh-env-gate` target to `make/blueprint.generated.mk`
- [x] T-302 Add same target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk` (template counterpart)
- [x] T-303 Declare `blueprint-upgrade-fresh-env-gate` as a required make target in `blueprint/contract.yaml`
- [x] T-304 Update `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — add `make blueprint-upgrade-fresh-env-gate` as step 6 in the command sequence (after `make blueprint-upgrade-consumer-postcheck`)
- [x] T-305 Run `make infra-validate` — clean

## Slice 4 — Blueprint docs update

- [x] T-401 Update `docs/blueprint/` upgrade skill reference — add `blueprint-upgrade-fresh-env-gate` gate step documentation (SKILL.md + template; quickstart.md + template; troubleshooting.md + template)
- [x] T-402 Document `artifacts/blueprint/fresh_env_gate.json` schema (status, worktree_path, targets_run, divergences, error, exit_code)
- [x] T-403 Document metric `blueprint_upgrade_fresh_env_gate_status_total` and its labels
- [x] T-404 Document failure diagnostic guidance (divergences field interpretation, how to fix a bootstrap regression)
- [ ] T-405 Run `make docs-build` — confirm no errors
- [ ] T-406 Run `make docs-smoke` — confirm no errors

## Validation and Release Readiness

- [x] T-501 Run `make quality-sdd-check` — clean
- [ ] T-502 Run `make quality-hooks-run` — clean
- [x] T-503 Run `make infra-validate` — clean
- [x] T-504 Run full test suite: `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` — 16 passed in 2.44s
- [x] T-505 Attach pytest output as validation evidence in `traceability.md`
- [x] T-506 Confirm no stale TODOs or dead code in touched scope
- [x] T-507 Run `make quality-hardening-review` — clean

## Publish

- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed, observability/metric changes, and proposals-only section
- [x] P-002 Update `pr_context.md` with: FR-001–FR-006, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, AC-001–AC-005 coverage mapping; key reviewer files; pytest validation evidence; rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact: pre-existing targets unaffected)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact: pre-existing targets unaffected)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact: pre-existing targets unaffected)
