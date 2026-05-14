# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-004 | N/A | D-1, D-2 | `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` | AC-001 — schema validation test | `SKILL.md` § Workaround Catalogue | `artifacts/blueprint/workarounds_applied.json` |
| FR-002 | SDD-C-004 | N/A | D-2 | `manifest.yaml` entry schema | AC-001 — required field presence test | ADR § Manifest Schema | — |
| FR-003 | SDD-C-004 | N/A | D-4 | `scripts/lib/blueprint/upgrade_workarounds.py` — `run_before_apply()` / `run_after_apply()` | AC-003, AC-005 — Stage 1c log assertion | `SKILL.md` § Pipeline Stages | pipeline log output |
| FR-004 | SDD-C-004 | N/A | D-3 | `upgrade_workarounds.py` — log format | AC-003 — log line assertion | — | pipeline stdout |
| FR-005 | SDD-C-004 | N/A | D-3 | `upgrade_workarounds.py` — `write_applied_json()` | AC-004 — JSON schema test | — | `artifacts/blueprint/workarounds_applied.json` |
| FR-006 | SDD-C-004 | N/A | D-6 | `upgrade_workarounds.py` — `should_revert()` / `revert()` | AC-005 — contract_merge revert test | `SKILL.md` § Revert Lifecycle | `workarounds_applied.json` status field |
| FR-007 | SDD-C-004 | N/A | D-6 | `upgrade_workarounds.py` — revert log | AC-005 — log assertion | — | pipeline stdout |
| FR-008 | SDD-C-004 | N/A | D-1 | `.agents/skills/blueprint-consumer-upgrade/workarounds/v1.10.0/` | AC-002 — catalogue entry presence test | ADR § Initial Catalogue | — |
| FR-009 | SDD-C-004 | N/A | D-5 | `upgrade_workarounds.py` — `is_idempotent()` | Slice 2 idempotency tests | — | log: "already applied" |
| NFR-SEC-001 | SDD-C-009 | N/A | D-3, D-7 | `upgrade_workarounds.py` — subprocess env allowlist | Slice 4 isolation test | ADR § Security | — |
| NFR-REL-001 | SDD-C-008 | N/A | D-3, D-4 | pipeline exit code propagation | Slice 5 pipeline integration test | — | `$pipeline_exit` variable |
| NFR-REL-002 | SDD-C-007 | N/A | D-2 | `manifest.yaml` schema_version field | manifest backward-compat test | ADR § Schema Versioning | — |
| NFR-OPS-001 | SDD-C-010 | N/A | D-5, D-6 | `upgrade_workarounds.py` — `write_applied_json()` | AC-004 — JSON field test | — | `workarounds_applied.json` |
| AC-001 | SDD-C-008 | N/A | D-2 | `workarounds/manifest.yaml` | `test_load_manifest_returns_entries_for_target_version` | — | — |
| AC-002 | SDD-C-008 | N/A | D-1 | `workarounds/v1.10.0/` | `test_initial_catalogue_entries_present` | — | — |
| AC-003 | SDD-C-008 | N/A | D-3, D-4 | `upgrade_consumer_pipeline.sh` Stage 1c | `test_pipeline_stage_1c_log_applied` | — | — |
| AC-004 | SDD-C-008 | N/A | D-5 | `upgrade_workarounds.py` — `write_applied_json()` | `test_workarounds_applied_json_fields` | — | — |
| AC-005 | SDD-C-008, SDD-C-023 | N/A | D-6 | `upgrade_workarounds.py` — `contract_merge` revert | `test_contract_merge_revert_removes_yaml_entries` | — | — |
| AC-006 | SDD-C-008 | N/A | D-3 | `upgrade_workarounds.py` — `evaluate_applies_when()` | `test_evaluate_applies_when_repo_mode_mismatch_returns_false` | — | — |
| AC-007 | SDD-C-008, SDD-C-023 | N/A | D-3, D-5, D-6 | `upgrade_workarounds.py` — full apply+revert cycle | `test_contract_merge_apply_revert_cycle_synthetic_version` | — | — |
| AC-008 | SDD-C-008 | N/A | D-3 | `upgrade_workarounds.py` — `evaluate_applies_when()` | `test_evaluate_applies_when_repo_mode_mismatch_returns_false` | — | — |
| FR-010 | SDD-C-001 | N/A | D-3 | `upgrade_workarounds.py` — failure policy per action_kind (pending Q-2) | Slice 2/3 error-path tests (to be defined post Q-2) | ADR § Failure Policy | pipeline exit code |

## Validation Summary
<!-- To be completed at Publish phase (Step 7) -->
- Test run output: pending implementation
- Quality gate result: pending implementation
- Smoke evidence: pending implementation
