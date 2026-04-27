# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Failing regression tests (red)
- [x] T-001 Write `test_resolve_contract_conflict_source_only_phase1_drop`: fixture consumer with `specs/` populated and source contract with `specs` in `source_only`; assert resolved `source_only` still contains `specs` before fix (reproduces #216, AC-001)
- [x] T-002 Write `test_resolve_contract_conflict_source_only_claude_md_drop`: fixture with `CLAUDE.md` present and source contract with `CLAUDE.md` in `source_only`; assert same failure (AC-002)
- [x] T-003 Write `test_resolve_contract_conflict_source_only_phase2_carry_forward`: consumer with consumer-added `source_only` entry; assert it is dropped before fix (AC-003)
- [x] T-004 Write `test_resolve_contract_conflict_source_only_no_conflict`: consumer with no consumer-added entries and no on-disk conflicts; assert resolved equals source (AC-005)
- [x] T-005 Confirm all new tests FAIL before implementation

### Slice 2 — Implementation (green)
- [x] T-010 Add `_filter_source_only(source_list, consumer_list, repo_root)` to `resolve_contract_upgrade.py` — Phase 1: drop source entries existing on disk; Phase 2: carry forward consumer additions existing on disk
- [x] T-011 Extend `ContractResolveResult` with `dropped_source_only: list[str]` and `kept_consumer_source_only: list[str]` fields
- [x] T-012 Wire `_filter_source_only` into `resolve_contract_conflict` after FR-007 prune-globs step; update `resolved["spec"]["repository"]["ownership_path_classes"]["source_only"]`
- [x] T-013 Extend `decisions` dict and pipeline stdout logging with `dropped_source_only` and `kept_consumer_source_only`
- [x] T-014 Confirm all regression tests pass green

### Slice 3 — Quality
- [x] T-020 Run `make quality-sdd-check` and fix violations
- [x] T-021 Run `make quality-hooks-run`
- [x] T-022 Run `make infra-validate`

## Test Automation
- [x] T-101 All 4 regression tests (T-001–T-004) are green after fix
- [x] T-103 AC-003 and AC-005 are positive-path tests; evidence captured in `pr_context.md`
- [x] T-104 Reproducible finding from #216 reproduction command translated into failing tests (T-001, T-002) before fix is applied

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-run` and `make infra-validate` — capture results
- [x] T-202 Attach evidence to traceability document
- [x] T-203 Confirm no stale TODOs/dead code/drift in changed function
- [x] T-204 Run `make docs-build` and `make docs-smoke` — pre-existing environment failure (docusaurus node_modules absent); not caused by this change (confirmed same failure on main)
- [x] T-205 Run `make quality-hardening-review`
- [x] T-206 Run `make blueprint-template-smoke` — pre-existing environment failure (bash 3 declare -A); confirmed same failure on main branch

## App Onboarding Minimum Targets
- [x] A-001 `apps-bootstrap` — no-impact (Python script tooling fix only)
- [x] A-002 `apps-smoke` — no-impact
- [x] A-003 `backend-test-unit` — no-impact
- [x] A-004 `backend-test-integration` — no-impact
- [x] A-005 `backend-test-contracts` — no-impact
- [x] A-006 `backend-test-e2e` — no-impact
- [x] A-007 `touchpoints-test-unit` — no-impact
- [x] A-008 `touchpoints-test-integration` — no-impact
- [x] A-009 `touchpoints-test-contracts` — no-impact
- [x] A-010 `touchpoints-test-e2e` — no-impact
- [x] A-011 `test-unit-all` — no-impact
- [x] A-012 `test-integration-all` — no-impact
- [x] A-013 `test-contracts-all` — no-impact
- [x] A-014 `test-e2e-all-local` — no-impact
- [x] A-015 `infra-port-forward-start` — no-impact
- [x] A-016 `infra-port-forward-stop` — no-impact
- [x] A-017 `infra-port-forward-cleanup` — no-impact

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (pytest output), and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
- [x] P-004 Close issue #216 via PR description (`Closes #216`)
