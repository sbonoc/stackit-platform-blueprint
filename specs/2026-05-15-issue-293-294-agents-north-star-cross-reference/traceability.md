# Traceability

## Work Item
- Slug: 2026-05-15-issue-293-294-agents-north-star-cross-reference
- Closes: #293, #294

## Requirement → Design → Implementation → Test → Docs → Ops

| Requirement | Design reference | Implementation path | Test | Docs | Ops evidence |
|---|---|---|---|---|---|
| FR-001 (Pointers section in AGENTS.md.tmpl) | architecture.md § Template governance context; ADR § Layer 1 | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `TestTemplateSectionPresence::test_pointers_section_present`, `test_pointers_table_has_placeholder_row`, `test_anti_duplication_statement_present`, `test_add_to_north_star_instruction_present` | `docs/blueprint/governance/quality_hooks.md` § AGENTS.md ↔ north_star.md Checks; self-documenting template | N/A — no runtime |
| FR-002 (Mandatory Workflow rule in AGENTS.md.tmpl) | architecture.md § Template governance context; ADR § Layer 1 | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `TestTemplateMandatoryWorkflowRule::test_mandatory_workflow_rule_present`, `test_must_not_duplicate_language_present` | `docs/blueprint/governance/quality_hooks.md` § AGENTS.md ↔ north_star.md Checks | N/A — no runtime |
| FR-003 (check_docs_cross_reference.py heading detection) | architecture.md § Quality enforcement context; ADR § Layer 2 | `scripts/bin/quality/check_docs_cross_reference.py` | `TestHeadingDetection::test_heading_match_without_allowlist_exits_one`, `test_heading_in_pointers_table_exits_zero`, `test_case_insensitive_normalization` | `docs/blueprint/governance/quality_hooks.md` § quality-docs-cross-reference-check | exit code 0/1; stderr violation messages |
| FR-004 (allowlist support) | architecture.md § Domain layer (_load_allowlist) | `scripts/bin/quality/check_docs_cross_reference.py` | `TestHeadingDetection::test_heading_in_allowlist_exits_zero` | `docs/blueprint/governance/quality_hooks.md` § Allowlist format | exit 0 with valid allowlist entry |
| FR-005 (make target + hooks wiring) | architecture.md § Integration and Dependency Edges | `make/blueprint.generated.mk`, `scripts/bin/quality/hooks_fast.sh` | `make infra-contract-test-fast` (target presence); `make quality-hooks-fast` (integration) | `docs/reference/generated/core_targets.generated.md` (auto-regenerated) | hooks_fast.sh run log |
| FR-006 (exit code semantics + output format) | architecture.md § Presentation/API/workflow boundaries | `scripts/bin/quality/check_docs_cross_reference.py` | `TestHeadingDetection::test_clean_files_exit_zero`, `test_heading_match_without_allowlist_exits_one` | N/A | exit code surfaced in hooks_fast.sh output |
| NFR-PERF-001 (under 2 seconds, stdlib only) | architecture.md § Domain layer (stdlib only) | `scripts/bin/quality/check_docs_cross_reference.py` (no subprocess, no network) | Implicit: 25 tests complete in 0.04s; `make quality-hooks-fast` timing | N/A | hooks_fast.sh runtime |
| NFR-MAINT-001 (Pointers table ≥1 placeholder row) | architecture.md § Template governance context | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `TestTemplateSectionPresence::test_pointers_table_has_placeholder_row` | N/A | N/A |
| NFR-COMPAT-001 (graceful no-op when files absent) | architecture.md § Application layer (main() path) | `scripts/bin/quality/check_docs_cross_reference.py` | `TestHeadingDetection::test_absent_agents_md_exits_zero`, `test_absent_north_star_exits_zero`, `test_missing_allowlist_exits_zero` | N/A | exit 0 in consumer repos without these files |
| FR-007 (north_star.md MUST-read rule in blueprint AGENTS.md) | architecture.md § Blueprint governance context; ADR § Layer 1 | `AGENTS.md` (blueprint root) | `TestBlueprintAgentsMd::test_blueprint_agents_md_north_star_rule_present`, `test_blueprint_agents_md_must_not_duplicate` | `docs/blueprint/governance/quality_hooks.md` § AGENTS.md ↔ north_star.md Checks | N/A — text instruction, no runtime |
| FR-010 (check_agents_md_structure.py structure detection) | architecture.md § Structure enforcement context; ADR § Layer 3 | `scripts/bin/quality/check_agents_md_structure.py` | `TestStructureCheckUnit` (4 tests), `TestStructureCheckMain` (5 tests) | `docs/blueprint/governance/quality_hooks.md` § quality-docs-agents-md-structure-check; `docs/platform/consumer/troubleshooting.md` § AGENTS.md structure check fails after blueprint upgrade | exit code 0/1; stderr violation messages |
| FR-011 (make target + hooks wiring for structure check, consumer-only gate) | architecture.md § Integration and Dependency Edges | `make/blueprint.generated.mk`, `scripts/bin/quality/hooks_fast.sh` (blueprint_repo_is_generated_consumer gate) | `make infra-contract-test-fast` (target presence); `make quality-hooks-fast` (integration) | `docs/reference/generated/core_targets.generated.md` (auto-regenerated) | hooks_fast.sh run log; skip metric in blueprint repo |

## Acceptance Criteria → Test Mapping

| AC | Test name | Test file | Status |
|---|---|---|---|
| AC-001 | `TestTemplateSectionPresence::test_pointers_section_present`, `test_pointers_table_has_placeholder_row`, `test_anti_duplication_statement_present`, `test_add_to_north_star_instruction_present` | `tests/blueprint/test_docs_cross_reference.py` | PASS (25 tests, 0.04s) |
| AC-002 | `TestTemplateMandatoryWorkflowRule::test_mandatory_workflow_rule_present`, `test_must_not_duplicate_language_present` | `tests/blueprint/test_docs_cross_reference.py` | PASS |
| AC-003 | `TestHeadingDetection::test_heading_match_without_allowlist_exits_one` | `tests/blueprint/test_docs_cross_reference.py` | PASS |
| AC-004 | `TestHeadingDetection::test_heading_in_pointers_table_exits_zero` | `tests/blueprint/test_docs_cross_reference.py` | PASS |
| AC-005 | `TestHeadingDetection::test_heading_in_allowlist_exits_zero` | `tests/blueprint/test_docs_cross_reference.py` | PASS |
| AC-006 | `make quality-docs-cross-reference-check` target presence | `make infra-contract-test-fast` | PASS |
| AC-007 | `TestHeadingDetection::test_absent_agents_md_exits_zero`, `test_absent_north_star_exits_zero`, `test_clean_files_exit_zero`, `test_missing_allowlist_exits_zero` | `tests/blueprint/test_docs_cross_reference.py` | PASS |
| AC-008 | `TestBlueprintAgentsMd::test_blueprint_agents_md_north_star_rule_present` | `tests/blueprint/test_docs_cross_reference.py` | PASS |
| AC-011 | `TestStructureCheckMain::test_missing_pointers_section_exits_one`, `test_missing_north_star_rule_exits_one`, `test_both_missing_exits_one_with_two_violations`; `TestStructureCheckUnit::test_missing_pointers_section_returns_one_violation`, `test_missing_north_star_rule_returns_one_violation`, `test_both_missing_returns_two_violations` | `tests/blueprint/test_agents_md_structure.py` | PASS |
| AC-012 | `TestStructureCheckMain::test_all_present_exits_zero`, `test_absent_agents_md_exits_zero`; `TestStructureCheckUnit::test_compliant_content_returns_no_violations` | `tests/blueprint/test_agents_md_structure.py` | PASS |

## Validation Summary
- Total unit tests delivered: 25 (16 cross-reference + 9 structure check)
- All 25 tests green: `uv run python3 -m pytest tests/blueprint/test_docs_cross_reference.py tests/blueprint/test_agents_md_structure.py -v` (0.04s)
- Contract gate: `make infra-contract-test-fast` — PASS (target list contract satisfied)
- Integration gate: `make quality-hooks-fast` — PASS (both new checks wired and passing)
- Docs gate: `make docs-build` — PASS; `make docs-smoke` — PASS
- Docs sync: `quality_hooks.md` and `troubleshooting.md` synced to bootstrap template mirrors
