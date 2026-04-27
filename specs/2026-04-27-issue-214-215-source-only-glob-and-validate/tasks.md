# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Failing regression tests (red)
- [ ] T-001 Write `test_audit_source_tree_coverage_prune_glob_coverage`: temp source repo with ADR files matching prune-glob; assert they appear in uncovered list before fix (reproduces #214, AC-001)
- [ ] T-002 Write `test_validate_absent_files_directory_entry`: temp consumer with directory `source_only` entry; assert error is emitted before fix (reproduces #215, AC-002)
- [ ] T-003 Write `test_validate_absent_files_glob_matching`: consumer with glob `source_only` entry and a matching file; assert error is emitted (AC-003)
- [ ] T-004 Write `test_validate_absent_files_glob_no_match`: consumer with glob `source_only` entry and NO matching file; assert no error (AC-004)
- [ ] T-005 Write `test_validate_absent_files_exact_file_present`: existing-behavior backward-compat test — exact-file entry and file present → error (AC-005)
- [ ] T-006 Confirm all new tests FAIL before implementation

### Slice 2 — Implementation fixes (green)
- [ ] T-010 `scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage`: extend `all_coverage_roots` with files from `candidate_rels` matching any prune-glob via `fnmatch.fnmatch`; update call site to pass prune-glob list
- [ ] T-011 `scripts/bin/blueprint/validate_contract.py::_validate_absent_files`: classify entries (glob/prefix vs file); use `is_file()` for file entries; use `fnmatch` against consumer file list for glob/prefix entries
- [ ] T-012 Confirm all 5 regression tests pass green

### Slice 3 — Docs and quality
- [ ] T-020 Update `docs/blueprint/consumer/contract_reference.md` to document directory-prefix and glob support in `source_only`
- [ ] T-021 Run `make quality-sdd-check` and fix any violations
- [ ] T-022 Run `make quality-hooks-run`
- [ ] T-023 Run `make infra-validate` in a synthetic consumer fixture

## Test Automation
- [ ] T-101 All 5 regression tests (T-001–T-005) are green after fix
- [ ] T-103 AC-001 and AC-004 are positive-path tests (matching fixture with correct behavior); evidence captured in `pr_context.md`
- [ ] T-104 Reproducible pre-PR findings from #214 and #215 reproduction commands are translated into failing tests (T-001, T-002) before fix is applied

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-run` and `make infra-validate` — capture results
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift in changed functions
- [ ] T-204 Run `make docs-build` and `make docs-smoke`
- [ ] T-205 Run `make quality-hardening-review`
- [ ] T-206 Run `make blueprint-template-smoke` and confirm clean pass

## App Onboarding Minimum Targets
- [ ] A-001 `apps-bootstrap` — no-impact (Python script tooling fix only)
- [ ] A-002 `apps-smoke` — no-impact
- [ ] A-003 `backend-test-unit` — no-impact
- [ ] A-004 `backend-test-integration` — no-impact
- [ ] A-005 `backend-test-contracts` — no-impact
- [ ] A-006 `backend-test-e2e` — no-impact
- [ ] A-007 `touchpoints-test-unit` — no-impact
- [ ] A-008 `touchpoints-test-integration` — no-impact
- [ ] A-009 `touchpoints-test-contracts` — no-impact
- [ ] A-010 `touchpoints-test-e2e` — no-impact
- [ ] A-011 `test-unit-all` — no-impact
- [ ] A-012 `test-integration-all` — no-impact
- [ ] A-013 `test-contracts-all` — no-impact
- [ ] A-014 `test-e2e-all-local` — no-impact
- [ ] A-015 `infra-port-forward-start` — no-impact
- [ ] A-016 `infra-port-forward-stop` — no-impact
- [ ] A-017 `infra-port-forward-cleanup` — no-impact

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (pytest output), and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
- [ ] P-004 Close issues #214 and #215 via PR description (`Closes #214, Closes #215`)
