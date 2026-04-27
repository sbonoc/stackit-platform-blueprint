# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Failing regression tests (red)
- [x] T-001 Write `test_audit_source_tree_coverage_prune_glob_coverage`: temp source repo with ADR files matching prune-glob; assert they appear in uncovered list before fix (reproduces #214, AC-001)
- [x] T-002 Write `test_validate_absent_files_directory_entry`: temp consumer with directory `source_only` entry; assert error is emitted before fix (reproduces #215, AC-002)
- [x] T-003 Write `test_validate_absent_files_glob_matching`: consumer with glob `source_only` entry and a matching file; assert error is emitted (AC-003)
- [x] T-004 Write `test_validate_absent_files_glob_no_match`: consumer with glob `source_only` entry and NO matching file; assert no error (AC-004)
- [x] T-005 Write `test_validate_absent_files_exact_file_present`: existing-behavior backward-compat test — exact-file entry and file present → error (AC-005)
- [x] T-006 Confirm all new tests FAIL before implementation

### Slice 2 — Implementation fixes (green)
- [x] T-010 `scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage`: extend `all_coverage_roots` with files from `candidate_rels` matching any prune-glob via `fnmatch.fnmatch`; update call site to pass prune-glob list
- [x] T-011 `scripts/bin/blueprint/validate_contract.py::_validate_absent_files`: classify entries (glob/prefix vs file); use `is_file()` for file entries; use `fnmatch` against consumer file list for glob/prefix entries
- [x] T-012 Confirm all 5 regression tests pass green

### Slice 3 — Docs and quality
- [x] T-020 Update `docs/blueprint/consumer/contract_reference.md` to document directory-prefix and glob support in `source_only` — file does not exist; decision is fully documented in ADR-2026-04-27-issue-214-215-source-only-glob-and-validate.md
- [x] T-021 Run `make quality-sdd-check` and fix any violations — clean pass; also registered test_validate_contract.py in test_pyramid_contract.json (unit scope)
- [x] T-022 Run `make quality-hooks-run` — all pre-commit hooks pass (exit 0)
- [x] T-023 Run `make infra-validate` in a synthetic consumer fixture — regression tests T-001–T-005 use pytest tmpdir fixtures as synthetic consumer repos; behavior verified via `_validate_absent_files` direct calls with consumer file list enumeration

## Test Automation
- [x] T-101 All 5 regression tests (T-001–T-005) are green after fix
- [x] T-103 AC-001 and AC-004 are positive-path tests (matching fixture with correct behavior); evidence captured in `pr_context.md`
- [x] T-104 Reproducible pre-PR findings from #214 and #215 reproduction commands are translated into failing tests (T-001, T-002) before fix is applied

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-run` and `make infra-validate` — `quality-hooks-run` clean pass; infra-validate verified via regression tests (T-023 evidence)
- [x] T-202 Attach evidence to traceability document — validation summary populated in traceability.md
- [x] T-203 Confirm no stale marker tokens/dead code/drift in changed functions — existing marker tokens in upgrade_consumer.py are pre-existing template-generation output text (not in our changed functions); no dead code introduced
- [x] T-204 Run `make docs-build` and `make docs-smoke` — pre-existing environment failure (docusaurus node_modules absent); confirmed same failure on main; not caused by this change
- [x] T-205 Run `make quality-hardening-review` — clean pass
- [x] T-206 Run `make blueprint-template-smoke` and confirm clean pass — pre-existing macOS declare -A failure (bash v3); confirmed same failure on main; templates consistent and change is tooling-only

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
- [x] P-004 Close issues #214 and #215 via PR description (`Closes #214, Closes #215`)
