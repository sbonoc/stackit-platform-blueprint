# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated
- [ ] G-006 Confirm [NEEDS CLARIFICATION] Q-1 (FR-011 gate severity: hard-fail vs warn-and-continue) is resolved before implementing Slice 4

## Implementation — Slice 1: #180 behavioral_check false positives

- [ ] T-001 Add failing test: case-label `|` alternation produces zero unresolved_symbols (`tests/blueprint/test_upgrade_shell_behavioral_check.py`)
- [ ] T-002 Add failing test: multi-line array initializer bare-words produce zero unresolved_symbols (`tests/blueprint/test_upgrade_shell_behavioral_check.py`)
- [ ] T-003 Extend `_find_unresolved_call_sites` in `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` to skip case-label alternation tokens
- [ ] T-004 Add `_ARRAY_OPEN_RE` and `array_depth` tracking to skip array literal bare-words

## Implementation — Slice 2: #181 _EXCLUDED_TOKENS

- [ ] T-005 Add failing tests: `tar`, `pnpm`, and each of the 13 blueprint runtime functions produce zero unresolved_symbols (`tests/blueprint/test_upgrade_shell_behavioral_check.py`)
- [ ] T-006 Extend `_EXCLUDED_TOKENS` in `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` with all 15 new tokens

## Implementation — Slice 3: #179 reconcile_report conflict state

- [ ] T-007 Create `tests/blueprint/test_upgrade_reconcile_report.py` with failing tests for: auto-merged exclusion, manually-resolved exclusion, no double-counting, active-markers included
- [ ] T-008 Implement `find_merge_markers(repo_root)` in `scripts/lib/blueprint/upgrade_reconcile_report.py`
- [ ] T-009 Compute `resolved_conflict_paths` and filter `conflicts_unresolved` to active-marker-only paths
- [ ] T-010 Eliminate double-counting of same path from plan-entry and apply-result paths

## Implementation — Slice 4: #185 upgrade planner completeness audit

- [ ] T-011 Add failing test: uncovered source file triggers WARNING and sets `uncovered_source_files_count > 0` (`tests/blueprint/test_upgrade_consumer.py`)
- [ ] T-012 Add failing test: validate gate fails when `uncovered_source_files_count > 0` (`tests/blueprint/test_upgrade_consumer.py`)
- [ ] T-013 Implement source tree completeness audit in `scripts/lib/blueprint/upgrade_consumer.py` (collect all blueprint source files, compute uncovered set, emit WARNING per uncovered file, record count in plan report JSON)
- [ ] T-014 Implement validate gate enforcement of `uncovered_source_files_count == 0` in upgrade validate logic
- [ ] T-015 Run audit against current blueprint source tree; add newly discovered uncovered files to `required_files` or `source_only` in `blueprint/contract.yaml`

## Implementation — Slice 5: #186 fresh_env_gate divergence detection

- [ ] T-016 Add failing test: gate fails when clean-worktree output file checksums differ from working-tree (both exit 0) (`tests/blueprint/test_upgrade_fresh_env_gate.py`)
- [ ] T-017 Add failing test: gate passes when output files match
- [ ] T-018 Add test: `fresh_env_gate.json` divergences array contains path + checksum entries on mismatch
- [ ] T-019 Implement checksum collection for `artifacts/blueprint/` in clean worktree and working tree in `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`
- [ ] T-020 Update `_write_report` call to include divergences list
- [ ] T-021 Set `gate_exit_code=1` when divergences are non-empty

## Implementation — Slice 6: #187 render_ci_workflow permissions

- [ ] T-022 Add failing test: `_render_ci` output contains `permissions:\n  contents: read` before `jobs:` (`tests/blueprint/test_quality_contracts.py` or new `test_render_ci_workflow.py`)
- [ ] T-023 Add `"permissions:\n  contents: read\n\n"` to `_render_ci` in `scripts/lib/quality/render_ci_workflow.py` after the `on:` block
- [ ] T-024 Audit generated job steps for any scope requiring explicit per-job grants; add if needed

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast` — passes
- [ ] T-202 Run `python3 -m pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` — all tests pass
- [ ] T-203 Run `python3 -m pytest tests/blueprint/test_upgrade_reconcile_report.py` — all tests pass
- [ ] T-204 Run `python3 -m pytest tests/blueprint/test_upgrade_consumer.py` — all tests pass
- [ ] T-205 Run `python3 -m pytest tests/blueprint/test_upgrade_fresh_env_gate.py` — all tests pass
- [ ] T-206 Run `make infra-contract-test-fast` — passes
- [ ] T-207 Attach evidence to traceability document
- [ ] T-208 Confirm no stale TODOs/dead code/drift
- [ ] T-209 Run `make docs-build` and `make docs-smoke` — passes
- [ ] T-210 Run `make quality-hardening-review` — passes

## Publish
- [ ] P-001 Update `hardening_review.md` with findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
- [ ] P-004 Update `AGENTS.backlog.md` — mark items for #179, #180+#181 as done; add #185, #186, #187 entries and mark done

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact: pre-existing targets unaffected)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact: pre-existing targets unaffected)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact: pre-existing targets unaffected)
