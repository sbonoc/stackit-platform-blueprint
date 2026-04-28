# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Add `scripts/lib/shell/keep_going.sh` with `keep_going_active`, `keep_going_init`, `run_check`, `keep_going_finalize` and EXIT-trap cleanup composition
- [ ] T-002 Modify `scripts/bin/quality/hooks_fast.sh` to parse `--keep-going`, source the helper, run pre-commit fail-fast first, dispatch downstream checks via `run_check` when keep-going is active, and update `--help`
- [ ] T-003 Modify `scripts/bin/quality/hooks_strict.sh` to parse `--keep-going`, source the helper, dispatch every check via `run_check` when keep-going is active, and update `--help`
- [ ] T-004 Modify `scripts/bin/quality/hooks_run.sh` to parse `--keep-going`, propagate to both child invocations, gate the strict-phase invocation on the fast-phase pre-commit-passed signal, and update `--help`
- [ ] T-005 Update `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` doc-comments for `quality-hooks-fast`, `quality-hooks-strict`, `quality-hooks-run` to mention `QUALITY_HOOKS_KEEP_GOING`; re-render `make/blueprint.generated.mk`
- [ ] T-006 Add the operations doc entry under `docs/blueprint/operations/` documenting `--keep-going`, `QUALITY_HOOKS_KEEP_GOING`, `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES`, the failure-cascade caveat, and the recommended agent inner-loop usage
- [ ] T-007 Move ADR `Status: proposed → approved` once Architecture sign-off is recorded

## Test Automation
- [ ] T-101 Add `tests/blueprint/test_quality_hooks_keep_going.py` (or `.bats` per Q-2) covering helper contract: env-var detection, per-check pass/fail/duration recording, summary block format, exit code aggregation, tail-length env-var override, EXIT-trap cleanup
- [ ] T-102 Add `tests/blueprint/test_quality_hooks_fast_keep_going.py` (or `.bats` per Q-2) covering: AC-001 (default fail-fast), AC-002 (`--keep-going` flag aggregation), AC-003 (env-var trigger), AC-004 (pre-commit fail-fast invariant), AC-006 (`--help` mentions keep-going)
- [ ] T-103 Add `tests/blueprint/test_quality_hooks_strict_keep_going.py` (or `.bats` per Q-2) covering: keep-going aggregation across strict-phase checks, default fail-fast preservation, `--help` mentions keep-going
- [ ] T-104 Add `tests/blueprint/test_quality_hooks_run_keep_going.py` (or `.bats` per Q-2) covering: AC-005 (cross-phase invocation order), env-var propagation through composite, combined exit code aggregation, `--help` mentions keep-going
- [ ] T-105 Add a contract test that asserts default invocation (no flag, env var unset) produces byte-equivalent behavior on a fixture with two known-broken independent checks (only the first failure observed; no summary marker emitted)

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast`, `make quality-hooks-fast QUALITY_HOOKS_KEEP_GOING=true`, `make quality-hooks-run`, `make quality-hooks-run QUALITY_HOOKS_KEEP_GOING=true` locally; record pass/fail in `traceability.md`
- [ ] T-202 Attach evidence (test output, summary block sample) to `traceability.md`
- [ ] T-203 Confirm no stale TODOs / dead code / drift; confirm default code path remains a verbatim `run_cmd` invocation per file
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
