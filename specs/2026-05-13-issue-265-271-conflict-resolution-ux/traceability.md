# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-023 | N/A | architecture.md § Engine context | `upgrade_consumer.py: _write_upgrade_triage()` | `test_conflict_triage_issue_265.py: test_triage_json_schema_valid` | `architecture.md` flowchart | `upgrade_triage.json` artifact |
| FR-002 | SDD-C-005, SDD-C-019 | N/A | architecture.md § Schema layer | `upgrade_consumer.py: _write_upgrade_triage()` + `upgrade_triage.schema.json` | `test_conflict_triage_issue_265.py: test_triage_json_schema_valid` | `upgrade_triage.schema.json` | — |
| FR-003 | SDD-C-004, SDD-C-023 | N/A | spec.md § Option Decision | `upgrade_consumer.py: _recommended_action()` | `test_conflict_triage_issue_265.py: test_recommended_action_*` | `architecture.md` | — |
| FR-004 | SDD-C-004 | N/A | architecture.md § Risk 2 | `upgrade_consumer.py: _write_upgrade_triage()` exclusion guard | `test_conflict_triage_issue_265.py: test_triage_excludes_contract_yaml` | `spec.md` § Explicit Exclusions | — |
| FR-005 | SDD-C-004 | N/A | spec.md § NFR-SEC-001 | `upgrade_consumer.py: _write_upgrade_triage()` | `test_conflict_triage_issue_265.py: test_triage_entries_contain_no_file_contents` | `spec.md` § NFR-SEC-001 | — |
| FR-006 | SDD-C-005 | N/A | architecture.md § Make layer | `blueprint.generated.mk: blueprint-upgrade-consumer-resolve` | `test_conflict_resolve_issue_265.py` | `blueprint-consumer-upgrade/SKILL.md` | — |
| FR-007 | SDD-C-023 | N/A | architecture.md § Resolve context | `upgrade_consumer_resolve.py` apply loop | `test_conflict_resolve_issue_265.py: test_take_source_rows_applied_to_working_tree` | `upgrade_consumer_resolve.py` | `upgrade_resolve.json` artifact |
| FR-008 | SDD-C-005 | N/A | architecture.md § High-Level Component Design | `upgrade_consumer_resolve.py` residual table print | `test_conflict_resolve_issue_265.py: test_residual_table_sorted_and_truncated_above_20` | `upgrade_consumer_pipeline.sh` usage | — |
| FR-009 | SDD-C-004 | N/A | spec.md § AC-009 | `upgrade_consumer_resolve.py` sort + slice with footer | `test_conflict_resolve_issue_265.py: test_residual_table_sorted_and_truncated_above_20` | — | — |
| FR-010 | SDD-C-004 | N/A | spec.md § FR-010 | `upgrade_consumer_resolve.py` `--interactive` branch | `test_conflict_resolve_issue_265.py: test_accept_source_all_applies_human_required_rows` (batch-mode proxy; full interactive requires stdin mock) | `blueprint-consumer-upgrade/SKILL.md` | — |
| FR-011 | SDD-C-004 | N/A | spec.md § FR-011 | `upgrade_consumer_resolve.py` `--accept-source`, `--accept-target` | `test_conflict_resolve_issue_265.py: test_accept_source_all_applies_human_required_rows` | — | — |
| FR-012 | SDD-C-004 | N/A | spec.md § FR-012 | `upgrade_consumer_resolve.py` `--dry-run` no-op path | `test_conflict_resolve_issue_265.py: test_dry_run_makes_no_file_changes` | — | — |
| NFR-IDM-001 | SDD-C-023 | N/A | plan.md § Change Strategy | `upgrade_consumer_resolve.py` idempotency guard | `test_conflict_resolve_issue_265.py: test_resolve_is_idempotent` | — | — |
| NFR-SCH-001 | SDD-C-019 | N/A | architecture.md § Schema layer | `upgrade_triage.schema.json` + resolve-script startup validation | `test_conflict_triage_issue_265.py: test_triage_json_schema_valid` | `upgrade_triage.schema.json` | — |
| NFR-SEC-001 | SDD-C-007 | N/A | architecture.md § Security | `upgrade_consumer.py: _write_upgrade_triage()` diff-summaries-only | `test_conflict_triage_issue_265.py: test_triage_entries_contain_no_file_contents` | `spec.md` § NFR-SEC-001 | — |
| NFR-REL-001 | SDD-C-023 | N/A | plan.md § Risks | `upgrade_consumer_resolve.py` startup triage validation | `test_conflict_resolve_issue_265.py: test_resolve_exits_nonzero_if_triage_missing` | — | — |
| NFR-OBS-001 | SDD-C-011 | N/A | plan.md § Operational Readiness | `upgrade_consumer_resolve.py` `print(f"upgrade-resolve: ...")` | `test_conflict_resolve_issue_265.py: test_resolve_prints_action_per_row` | — | `upgrade_resolve.json` |
| NFR-A11Y-001 | — | N/A | spec.md | N/A — CLI tool, no UI surface | N/A | spec.md § NFR-A11Y-001 | — |
| NFR-OPS-001 | — | N/A | spec.md | N/A — offline tooling | N/A | spec.md § NFR-OPS-001 | — |
| AC-001 | SDD-C-023 | N/A | FR-001 | `upgrade_consumer.py: _write_upgrade_triage()` | `test_conflict_triage_issue_265.py: test_triage_json_schema_valid` | — | — |
| AC-002 | SDD-C-023 | N/A | FR-003 | `_recommended_action()` | `test_conflict_triage_issue_265.py: test_recommended_action_blueprint_managed_root_is_take_source` | — | — |
| AC-003 | SDD-C-023 | N/A | FR-003 | `_recommended_action()` | `test_conflict_triage_issue_265.py: test_recommended_action_blueprint_managed_catch_all_is_human_required` | — | — |
| AC-004 | SDD-C-023 | N/A | FR-004 | `_write_upgrade_triage()` exclusion guard | `test_conflict_triage_issue_265.py: test_triage_excludes_contract_yaml` | — | — |
| AC-005 | SDD-C-023 | N/A | FR-005, NFR-SEC-001 | `_write_upgrade_triage()` | `test_conflict_triage_issue_265.py: test_triage_entries_contain_no_file_contents` | — | — |
| AC-006 | SDD-C-023 | N/A | FR-007 | `upgrade_consumer_resolve.py` apply loop | `test_conflict_resolve_issue_265.py: test_take_source_rows_applied_to_working_tree` | — | — |
| AC-007 | SDD-C-023 | N/A | FR-007 | `upgrade_consumer_resolve.py` apply loop | `test_conflict_resolve_issue_265.py: test_human_required_rows_not_touched` | — | — |
| AC-008 | SDD-C-023 | N/A | FR-007 | `upgrade_consumer_resolve.py` | `test_conflict_resolve_issue_265.py: test_upgrade_resolve_json_written` | — | `upgrade_resolve.json` |
| AC-009 | SDD-C-023 | N/A | FR-008, FR-009 | `upgrade_consumer_resolve.py` | `test_conflict_resolve_issue_265.py: test_residual_table_sorted_and_truncated_above_20` | — | — |
| AC-010 | SDD-C-023 | N/A | FR-010 | `upgrade_consumer_resolve.py` `--interactive` | `test_conflict_resolve_issue_265.py` interactive path | `blueprint-consumer-upgrade/SKILL.md` | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, NFR-IDM-001, NFR-SCH-001, NFR-SEC-001, NFR-REL-001, NFR-OBS-001, NFR-A11Y-001, NFR-OPS-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010

## Validation Summary
- Required bundles executed: pending (post-implementation)
- Result summary: pending
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Issue #270 (explicit consumer test ownership markers) — when shipped, `_recommended_action()` mapping table gains a `consumer-test` class reducing catch-all false positives. No action required in this work item; Option A is correct and conservative.
