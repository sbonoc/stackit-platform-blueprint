# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-012 | Reconcile report: active-marker-only conflict state | `scripts/lib/blueprint/upgrade_reconcile_report.py` — `find_merge_markers`, `_classify_plan_entries`, `_classify_apply_results` | `tests/blueprint/test_upgrade_reconcile_report.py::test_active_marker_file_included` | `docs/blueprint/` upgrade flow docs | `fresh_env_gate.json` → `conflicts_unresolved` |
| FR-002 | SDD-C-005, SDD-C-012 | Reconcile report: auto-merged files excluded | `scripts/lib/blueprint/upgrade_reconcile_report.py` — `resolved_conflict_paths` computation | `tests/blueprint/test_upgrade_reconcile_report.py::test_auto_merged_file_excluded_from_conflicts` | — | — |
| FR-003 | SDD-C-005, SDD-C-012 | Reconcile report: manually resolved files excluded | `scripts/lib/blueprint/upgrade_reconcile_report.py` — `manually_resolved_paths` computation | `tests/blueprint/test_upgrade_reconcile_report.py::test_manually_resolved_conflict_excluded` | — | — |
| FR-004 | SDD-C-005, SDD-C-012 | Reconcile report: no double-counting | `scripts/lib/blueprint/upgrade_reconcile_report.py` — unified set deduplication | `tests/blueprint/test_upgrade_reconcile_report.py::test_no_double_counting` | — | — |
| FR-005 | SDD-C-005, SDD-C-012 | Behavioral check: case-label alternation guard | `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `_find_unresolved_call_sites` alternation guard | `tests/blueprint/test_upgrade_shell_behavioral_check.py::test_case_alternation_not_flagged` | — | — |
| FR-006 | SDD-C-005, SDD-C-012 | Behavioral check: array literal depth tracking | `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `_ARRAY_OPEN_RE`, `array_depth` tracking | `tests/blueprint/test_upgrade_shell_behavioral_check.py::test_array_init_bare_words_not_flagged` | — | — |
| FR-007 | SDD-C-005, SDD-C-012 | Behavioral check: OS tool token exclusions | `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `_EXCLUDED_TOKENS` extension | `tests/blueprint/test_upgrade_shell_behavioral_check.py::test_tar_and_pnpm_not_flagged` | — | — |
| FR-008 | SDD-C-005, SDD-C-012 | Behavioral check: blueprint runtime function exclusions | `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `_EXCLUDED_TOKENS` extension | `tests/blueprint/test_upgrade_shell_behavioral_check.py::test_blueprint_runtime_functions_not_flagged` | — | — |
| FR-009 | SDD-C-005, SDD-C-012 | Upgrade planner: source tree completeness audit | `scripts/lib/blueprint/upgrade_consumer.py` — completeness audit function | `tests/blueprint/test_upgrade_consumer.py::test_uncovered_file_detected` | `docs/blueprint/` upgrade runbook | plan report JSON `uncovered_source_files_count` |
| FR-010 | SDD-C-005, SDD-C-012 | Upgrade planner: WARNING + count in plan report | `scripts/lib/blueprint/upgrade_consumer.py` — stderr WARNING, plan report JSON field | `tests/blueprint/test_upgrade_consumer.py::test_nonzero_count_returns_errors` | — | — |
| FR-011 | SDD-C-005, SDD-C-011, SDD-C-012 | Validate gate: enforce uncovered_source_files_count == 0 | `scripts/lib/blueprint/upgrade_consumer_validate.py` — gate enforcement | `tests/blueprint/test_upgrade_consumer.py::test_nonzero_count_returns_errors` | — | — |
| FR-012 | SDD-C-005, SDD-C-012 | Fresh-env gate: checksum collection | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` — checksum collection loop | `tests/blueprint/test_upgrade_fresh_env_gate.py::test_compute_artifact_checksums_detects_content_diff` | `docs/blueprint/` upgrade runbook | `fresh_env_gate.json` `divergences` |
| FR-013 | SDD-C-005, SDD-C-010, SDD-C-012 | Fresh-env gate: divergences in artifact | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` — `_write_report` divergences | `tests/blueprint/test_upgrade_fresh_env_gate.py::test_divergence_diff_included_in_report_on_failure` | — | `fresh_env_gate.json` |
| FR-014 | SDD-C-005, SDD-C-011, SDD-C-012 | Fresh-env gate: fail on non-empty divergences | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` — `gate_exit_code=1` when divergences non-empty | `tests/blueprint/test_upgrade_fresh_env_gate.py::test_gate_fails_on_artifact_checksum_divergence_even_when_targets_pass` | — | — |
| FR-015 | SDD-C-005, SDD-C-009, SDD-C-012 | CI renderer: permissions block inclusion | `scripts/lib/quality/render_ci_workflow.py` — `_render_ci` permissions stanza | `tests/blueprint/test_quality_contracts.py::test_render_ci_includes_permissions_block` | `docs/blueprint/` CI template docs | generated `ci.yml` |
| FR-016 | SDD-C-005, SDD-C-009, SDD-C-012 | CI renderer: contents: read at workflow level | `scripts/lib/quality/render_ci_workflow.py` — `permissions:\n  contents: read` | `tests/blueprint/test_quality_contracts.py::test_ci_workflow_file_contains_permissions_block` | — | — |
| NFR-SEC-001 | SDD-C-009 | Least-privilege GITHUB_TOKEN in generated CI | `scripts/lib/quality/render_ci_workflow.py` | `tests/blueprint/test_quality_contracts.py::test_render_ci_includes_permissions_block` | — | generated `ci.yml` |
| NFR-OBS-001 | SDD-C-010 | Structured gate artifact fields | `fresh_env_gate.json` schema, plan report JSON schema, reconcile report JSON schema | Schema validation tests | `docs/blueprint/` upgrade runbook | gate artifacts |
| NFR-REL-001 | SDD-C-011 | Gate enforcement for zero uncovered files + zero active conflicts | `upgrade_consumer_validate.py`, `upgrade_consumer_postcheck.py` | `tests/blueprint/test_upgrade_consumer.py::test_nonzero_count_returns_errors`, `test_upgrade_reconcile_report.py::test_manually_resolved_conflict_excluded` | — | gate artifacts |
| NFR-OPS-001 | SDD-C-007 | Human-readable stderr diagnostics on gate failure | All five affected files — stderr `WARNING`/`ERROR` lines | Pytest assertions on stderr output | `docs/blueprint/` upgrade runbook | stderr gate output |
| AC-001 | SDD-C-012 | postcheck unblocks after all markers resolved | `upgrade_reconcile_report.py` + `upgrade_consumer_postcheck.py` | `test_upgrade_reconcile_report.py::test_manually_resolved_conflict_excluded` | — | — |
| AC-002 | SDD-C-012 | auto-merged files excluded from conflicts_unresolved | `upgrade_reconcile_report.py` | `test_upgrade_reconcile_report.py::test_auto_merged_file_excluded_from_conflicts` | — | — |
| AC-003 | SDD-C-012 | case-label alternation: zero false positives | `upgrade_shell_behavioral_check.py` | `test_upgrade_shell_behavioral_check.py::test_case_alternation_not_flagged` | — | — |
| AC-004 | SDD-C-012 | array literal bare-words: zero false positives | `upgrade_shell_behavioral_check.py` | `test_upgrade_shell_behavioral_check.py::test_array_init_bare_words_not_flagged` | — | — |
| AC-005 | SDD-C-012 | tar, pnpm, blueprint runtime functions: zero findings | `upgrade_shell_behavioral_check.py` | `test_upgrade_shell_behavioral_check.py::test_tar_and_pnpm_not_flagged`, `::test_blueprint_runtime_functions_not_flagged` | — | — |
| AC-006 | SDD-C-012 | uncovered source file → WARNING + count | `upgrade_consumer.py` | `test_upgrade_consumer.py::test_uncovered_file_detected` | — | — |
| AC-007 | SDD-C-012 | validate gate fails on uncovered_source_files_count > 0 | `upgrade_consumer_validate.py` | `test_upgrade_consumer.py::test_nonzero_count_returns_errors` | — | — |
| AC-008 | SDD-C-012 | fresh_env_gate fails on file checksum divergence | `upgrade_fresh_env_gate.sh` | `test_upgrade_fresh_env_gate.py::test_gate_fails_on_artifact_checksum_divergence_even_when_targets_pass` | — | `fresh_env_gate.json` |
| AC-009 | SDD-C-009, SDD-C-012 | generated ci.yml has permissions: contents: read | `render_ci_workflow.py` | `test_quality_contracts.py::test_render_ci_includes_permissions_block` | — | generated `ci.yml` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `pytest tests/blueprint/`, `make quality-sdd-check`
- Result summary: all 6 slices implemented; pytest suite passes (392 tests); `make quality-hooks-fast` passes; all 15 test name references in this matrix verified against actual implemented test names
- Documentation validation:
  - `make docs-build` — passed
  - `make docs-smoke` — passed

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Issue #184 — consumer-extensible exclusion set for behavioral check (follow-on to FR-007/FR-008). Track in AGENTS.backlog.md.
- Follow-up 2: Issue #183 — stale reconcile report detection (detect when report on disk is from a different tag pair). Track in AGENTS.backlog.md.
