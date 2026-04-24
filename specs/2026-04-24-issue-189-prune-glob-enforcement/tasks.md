# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation (Slice order: 1 → 2 → 3 → 4)

### Slice 1 — Failing tests (red; implement BEFORE the fix)
- [ ] T-001 Add unit test `test_prune_glob_scan_returns_violations_when_file_matches` to `tests/blueprint/test_upgrade_consumer_validate.py` — asserts that a file matching a prune glob appears in `violations` and `violation_count > 0` (REQ-010, positive-path assertion). Confirm FAIL red before Slice 2.
- [ ] T-002 Add unit test `test_prune_glob_scan_returns_empty_when_no_match` — asserts `violations = []` and `violation_count = 0` when no files match (REQ-011). Confirm FAIL red before Slice 2.
- [ ] T-003 Add unit test `test_prune_glob_scan_skipped_when_not_generated_consumer` — asserts `prune_glob_check.status = "skipped"` when `repo_mode = "template-source"` (REQ-012). Confirm FAIL red before Slice 2.
- [ ] T-004 Add integration test: validate exits non-zero and `upgrade_validate.json` includes `prune_glob_check.violations` when a file matching a prune glob is present (REQ-013). Confirm FAIL red before Slice 2.
- [ ] T-005 Add integration test: postcheck exits non-zero and `upgrade_postcheck.json` includes `prune-glob-violations` in `blocked_reasons` when validate report contains violations (REQ-014). Confirm FAIL red before Slice 2.

### Slice 2 — Implementation (green)
- [ ] T-006 Implement `_scan_prune_glob_violations(repo_root, contract)` in `scripts/lib/blueprint/upgrade_consumer_validate.py` — uses `pathlib.Path.rglob()` for each pattern in `source_artifact_prune_globs_on_init`; filters symlinks resolving outside `repo_root`; returns sorted list of repo-relative POSIX paths (REQ-001, NFR-SEC-001).
- [ ] T-007 Call `_scan_prune_glob_violations()` in the validate main flow; append `prune_glob_check` section (`status`, `globs_checked`, `violations`, `violation_count`, `remediation_hint`) to `upgrade_validate.json`; set `summary.status = "failure"` when `violation_count > 0` (REQ-002, REQ-003, NFR-OPS-001).
- [ ] T-008 Add stderr emission loop: one line per violation in the format `prune-glob violation: <path> (matches: <glob>)` when violations are found (REQ-004, NFR-OBS-001).
- [ ] T-009 Handle skip cases: set `prune_glob_check.status = "skipped"` when `repo_mode != "generated-consumer"` (REQ-005) or when contract cannot be loaded (REQ-006).
- [ ] T-010 Add `prune_glob_violations` section (`violation_count`, `violations`) and `prune-glob-violations` to `blocked_reasons` in `scripts/lib/blueprint/upgrade_consumer_postcheck.py` when `prune_glob_check.violation_count > 0` (REQ-007, REQ-008).
- [ ] T-011 Run full test suite; confirm all tests PASS including T-001 through T-005.

### Slice 3 — Skill runbook
- [ ] T-012 Add required check step to `.agents/skills/blueprint-consumer-upgrade/SKILL.md` after the manual merge resolution step, naming both canonical glob patterns `specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*` and `docs/blueprint/architecture/decisions/ADR-*.md` by value (REQ-009, AC-005).

### Slice 4 — Docs
- [ ] T-013 Update `docs/blueprint/architecture/execution_model.md` to document the prune glob check in the validate phase description.
- [ ] T-014 Run `python3 scripts/lib/docs/sync_blueprint_template_docs.py` to sync bootstrap template docs. Run `make quality-docs-check-changed`.

## Validation and Release Readiness
- [ ] T-201 Run `python3 -m pytest tests/blueprint/test_upgrade_consumer_validate.py -v -k prune_glob` — unit tests pass (REQ-010, REQ-011, REQ-012).
- [ ] T-202 Run `python3 -m pytest tests/blueprint/ -v` — full blueprint suite, no regressions (REQ-013, REQ-014).
- [ ] T-203 Run `make quality-hooks-fast` — passes.
- [ ] T-204 Run `make quality-docs-check-changed` — passes.
- [ ] T-205 Record test evidence in `pr_context.md` and `hardening_review.md`.
- [ ] T-206 Run `make quality-hardening-review` — passes.

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section.
- [ ] P-002 Update `pr_context.md` with REQ-001 through REQ-014, NFR, and AC-001 through AC-005 coverage, key reviewer files, test evidence, and rollback notes.
- [ ] P-003 Ensure PR description references `pr_context.md` and issue #189.

## App Onboarding Minimum Targets (Normative)
- App onboarding impact: no-impact — tooling-only Python module change; no app onboarding surface modified.
- [ ] A-001 `apps-bootstrap` and `apps-smoke` — not applicable (no-impact)
- [ ] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — not applicable (no-impact)
- [ ] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — not applicable (no-impact)
- [ ] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — not applicable (no-impact)
- [ ] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — not applicable (no-impact)
