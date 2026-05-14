# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-004 | N/A | D-1, D-2 | `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` | `test_load_manifest_returns_entries_for_target_version` | `SKILL.md` § Workaround Catalogue | `artifacts/blueprint/workarounds_applied.json` |
| FR-002 | SDD-C-004 | N/A | D-2 | `manifest.yaml` entry schema | `test_load_manifest_returns_entries_for_target_version` (entry field assertions) | ADR § Manifest Schema | — |
| FR-003 | SDD-C-004 | N/A | D-4 | `scripts/lib/blueprint/upgrade_workarounds.py` — `run_before_apply()` / `run_after_apply()` | `test_apply_phase_before_apply_filters_correctly`, `test_apply_phase_after_apply_filters_correctly` | `SKILL.md` § Pipeline Stages | pipeline log output |
| FR-004 | SDD-C-004 | N/A | D-3 | `upgrade_workarounds.py` — log format | `test_pipeline_stage_1c_log_present`, `test_pipeline_stage_2c_log_present` | — | pipeline stdout |
| FR-005 | SDD-C-004 | N/A | D-3 | `upgrade_workarounds.py` — `_write_applied_json()` | `test_run_before_apply_writes_applied_json_with_required_fields` | — | `artifacts/blueprint/workarounds_applied.json` |
| FR-006 | SDD-C-004 | N/A | D-6 | `upgrade_workarounds.py` — `should_revert()` / `revert()` | `test_contract_merge_revert_removes_yaml_entries`, `test_should_revert_true_when_landed_in_satisfied_and_previously_applied` | `SKILL.md` § Revert Lifecycle | `workarounds_applied.json` status field |
| FR-007 | SDD-C-004 | N/A | D-6 | `upgrade_workarounds.py` — revert log | `test_should_revert_true_when_landed_in_satisfied_and_previously_applied` | — | pipeline stdout |
| FR-008 | SDD-C-004 | N/A | D-1 | `.agents/skills/blueprint-consumer-upgrade/workarounds/v1.10.0/` | `test_initial_catalogue_entries_present` | ADR § Initial Catalogue | — |
| FR-009 | SDD-C-004 | N/A | D-5 | `upgrade_workarounds.py` — `is_idempotent()` | `test_idempotency_check_skips_already_applied_entry`, `test_contract_merge_apply_is_idempotent`, `test_patch_apply_is_idempotent` | — | log: "already applied" |
| NFR-SEC-001 | SDD-C-009 | N/A | D-3, D-7 | `upgrade_workarounds.py` — `_PYTHON_SCRIPT_ENV_ALLOWLIST` | `test_python_script_isolation_env_allowlist` | ADR § Security | — |
| NFR-REL-001 | SDD-C-008 | N/A | D-3, D-4 | `upgrade_consumer_pipeline.sh` — `stage1c_rc` / `stage2c_rc` exit code propagation | `test_pipeline_calls_upgrade_workarounds_before_apply`, `test_pipeline_calls_upgrade_workarounds_after_apply` | — | `$pipeline_exit` variable |
| NFR-REL-002 | SDD-C-007 | N/A | D-2 | `manifest.yaml` `schema_version: 1` | `test_load_manifest_returns_empty_for_unknown_version` (unknown version → empty, not error) | ADR § Schema Versioning | — |
| NFR-OPS-001 | SDD-C-010 | N/A | D-5, D-6 | `upgrade_workarounds.py` — `_write_applied_json()` | `test_run_before_apply_writes_applied_json_with_required_fields` | — | `workarounds_applied.json` |
| AC-001 | SDD-C-008 | N/A | D-2 | `workarounds/manifest.yaml` | `test_load_manifest_returns_entries_for_target_version` | — | — |
| AC-002 | SDD-C-008 | N/A | D-1 | `workarounds/v1.10.0/` | `test_initial_catalogue_entries_present` | — | — |
| AC-003 | SDD-C-008 | N/A | D-3, D-4 | `upgrade_consumer_pipeline.sh` Stage 1c | `test_pipeline_stage_1c_log_present` | — | — |
| AC-004 | SDD-C-008 | N/A | D-5 | `upgrade_workarounds.py` — `_write_applied_json()` | `test_run_before_apply_writes_applied_json_with_required_fields` | — | — |
| AC-005 | SDD-C-008, SDD-C-023 | N/A | D-6 | `upgrade_workarounds.py` — `contract_merge` revert | `test_contract_merge_revert_removes_yaml_entries`, `test_contract_merge_revert_is_noop_when_entries_absent` | — | — |
| AC-006 | SDD-C-008 | N/A | D-3 | `upgrade_workarounds.py` — `evaluate_applies_when()` | `test_evaluate_applies_when_repo_mode_mismatch_returns_false` | — | — |
| AC-007 | SDD-C-008, SDD-C-023 | N/A | D-3, D-5, D-6 | `upgrade_workarounds.py` — full apply+revert cycle | `test_contract_merge_apply_adds_yaml_entries` + `test_contract_merge_revert_removes_yaml_entries` (sequential coverage) | — | — |
| AC-008 | SDD-C-008 | N/A | D-3 | `upgrade_workarounds.py` — `evaluate_applies_when()` | `test_evaluate_applies_when_repo_mode_mismatch_returns_false` | — | — |
| FR-010 | SDD-C-001 | N/A | D-3 | `upgrade_workarounds.py` — per-action_kind failure dispatch in `run_before_apply()` / `run_after_apply()` | `test_contract_merge_failure_in_run_before_apply_is_fatal`, `test_patch_failure_in_run_after_apply_is_nonfatal` | ADR § Resolved Decisions (Q-2) | pipeline exit code; `workarounds_applied.json` status: failed |
| NFR-A11Y-001 | — | N/A | — | N/A — no UI components | N/A | N/A | N/A |
| AC-009 | SDD-C-008 | N/A | D-3 | `upgrade_workarounds.py` — per-action_kind failure dispatch | `test_contract_merge_failure_in_run_before_apply_is_fatal`, `test_patch_failure_in_run_after_apply_is_nonfatal` | — | — |
| FR-011 | SDD-C-004, SDD-C-009 | N/A | D-8 | `.github/ISSUE_TEMPLATE/bug_report.yml` — optional workaround section | `test_workaround_report_parser_extracts_all_fields` (uses template-section fixture) | `SKILL.md` § Workaround Report Filing | GitHub issue creation UI |
| FR-012 | SDD-C-004, SDD-C-009 | N/A | D-8, D-9 | `.github/workflows/workaround_report_scaffolder.yml`, `scripts/lib/blueprint/workaround_report_parser.py` | `test_workaround_report_parser_produces_correct_action_filename`, `test_workaround_report_parser_produces_manifest_entry_stub` | ADR § Scaffolder | GitHub Actions run log |
| FR-013 | SDD-C-004 | N/A | D-10 | `scripts/lib/blueprint/workaround_report_filer.py`, `SKILL.md` (filing step) | `test_workaround_report_filer_calls_gh_issue_create_with_correct_fields` | `SKILL.md` § Manual Workaround Filing | upgrade session log |
| FR-014 | SDD-C-004 | N/A | D-10 | `workaround_report_filer.py` — duplicate detection via `gh issue list --search` | `test_workaround_report_filer_skips_when_duplicate_exists` | — | log: "workaround-report already filed" |
| NFR-SEC-002 | SDD-C-009 | N/A | D-9 | `workaround_report_scaffolder.yml` — verbatim file write (no eval/exec); `workaround_report_parser.py` — plain string assignment only | `test_workaround_report_parser_extracts_all_fields` (action_content returned as raw string, not evaluated) | ADR § Security | GitHub Actions permissions |
| NFR-REL-003 | SDD-C-008 | N/A | D-10 | `workaround_report_filer.py` — try/except wraps all gh calls | `test_workaround_report_filer_is_nonfatal_on_gh_failure` | — | upgrade log warning |
| AC-010 | SDD-C-008 | N/A | D-8 | `.github/ISSUE_TEMPLATE/bug_report.yml` — optional workaround section | `test_workaround_report_parser_extracts_all_fields` (uses template fixture body) | — | — |
| AC-011 | SDD-C-008 | N/A | D-8, D-9 | `workaround_report_parser.py` + scaffolder workflow | `test_workaround_report_parser_produces_correct_action_filename`, `test_workaround_report_parser_produces_manifest_entry_stub` | — | — |
| AC-012 | SDD-C-008 | N/A | D-10 | `workaround_report_filer.py` | `test_workaround_report_filer_calls_gh_issue_create_with_correct_fields` | — | — |
| AC-013 | SDD-C-008 | N/A | D-10 | `workaround_report_filer.py` — `gh issue list --search` | `test_workaround_report_filer_skips_when_duplicate_exists` | — | log output |

## Validation Summary
- Test run output: `make blueprint-test-unit` — 26 tests in `test_upgrade_workarounds.py`, 8 in `test_workaround_report_parser.py`, 4 in `test_workaround_report_filer.py`, 4 in `test_upgrade_pipeline.py` (TestWorkaroundCatalogueStages) — 0 failures
- Quality gate result: `make quality-hooks-fast` — all 9 checks PASS (2026-05-14); `make quality-sdd-check` — PASS; `make quality-spec-pr-ready` — PASS
- Smoke evidence: N/A — no HTTP endpoints, no local runtime; pipeline stage integration covered by `test_upgrade_pipeline.py` assertions on script text
