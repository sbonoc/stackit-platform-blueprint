# Traceability

## Work Item
- Slug: 2026-05-15-issue-293-294-agents-north-star-cross-reference
- Closes: #293, #294

## Requirement → Design → Implementation → Test → Docs → Ops

| Requirement | Design reference | Implementation path | Test | Docs | Ops evidence |
|---|---|---|---|---|---|
| FR-001 (Pointers section in AGENTS.md.tmpl) | architecture.md § Template governance context; ADR § Layer 1 | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `tests/blueprint/test_docs_cross_reference.py::TemplateSectionTests::test_pointers_section_present` | ADR; self-documenting template | N/A — no runtime |
| FR-002 (Mandatory Workflow rule in AGENTS.md.tmpl) | architecture.md § Template governance context; ADR § Layer 1 | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `tests/blueprint/test_docs_cross_reference.py::TemplateSectionTests::test_mandatory_workflow_rule_present` | ADR | N/A — no runtime |
| FR-003 (check_docs_cross_reference.py heading detection) | architecture.md § Quality enforcement context; ADR § Layer 2; Flowchart diagram | `scripts/bin/quality/check_docs_cross_reference.py` | `tests/blueprint/test_docs_cross_reference.py::HeadingDetectionTests` (AC-003, AC-004) | ADR | exit code 0/1; stdout violation messages |
| FR-004 (allowlist support) | architecture.md § Domain layer (_load_allowlist) | `scripts/bin/quality/check_docs_cross_reference.py` | `tests/blueprint/test_docs_cross_reference.py::AllowlistTests` (AC-005) | ADR | exit 0 with valid allowlist entry |
| FR-005 (make target + hooks wiring) | architecture.md § Integration and Dependency Edges | `make/blueprint.generated.mk`, `scripts/bin/quality/hooks_fast.sh` | `make infra-contract-test-fast` (AC-006); `make quality-hooks-fast` (AC-006) | `docs/blueprint/core_targets.md` auto-updated via `make quality-docs-sync-core-targets` | hooks_fast.sh run log |
| FR-006 (exit code semantics + output format) | architecture.md § Presentation/API/workflow boundaries | `scripts/bin/quality/check_docs_cross_reference.py` | `tests/blueprint/test_docs_cross_reference.py::ExitCodeTests` | N/A | exit code in hooks_fast.sh output |
| NFR-PERF-001 (under 2 seconds, stdlib only) | architecture.md § Domain layer (stdlib only) | `scripts/bin/quality/check_docs_cross_reference.py` (no subprocess, no network) | Implicit: `make quality-hooks-fast` timing | N/A | hooks_fast.sh runtime |
| NFR-MAINT-001 (Pointers table ≥1 placeholder row) | architecture.md § Template governance context | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `tests/blueprint/test_docs_cross_reference.py::TemplateSectionTests::test_pointers_table_has_placeholder_row` | N/A | N/A |
| NFR-COMPAT-001 (graceful no-op when files absent) | architecture.md § Application layer (main() path) | `scripts/bin/quality/check_docs_cross_reference.py` | `tests/blueprint/test_docs_cross_reference.py::GracefulSkipTests` (AC-007) | N/A | exit 0 in consumer repos without these files |
| FR-007 (north_star.md MUST-read rule in blueprint AGENTS.md) | architecture.md § Blueprint governance context; ADR § Layer 1 | `AGENTS.md` (blueprint root) | `tests/blueprint/test_docs_cross_reference.py::BlueprintAgentsMdTests::test_blueprint_agents_md_north_star_rule_present` | ADR | N/A — text instruction, no runtime |
| FR-008 (AGENTS.decisions.md scan rule in AGENTS.md.tmpl) | architecture.md § Template governance context; ADR § Layer 1 | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `tests/blueprint/test_docs_cross_reference.py::TemplateSectionTests::test_decisions_scan_rule_present` | ADR; self-documenting template | N/A — no runtime |
| FR-009 (AGENTS.decisions.md scan rule in blueprint AGENTS.md) | architecture.md § Blueprint governance context; ADR § Layer 1 | `AGENTS.md` (blueprint root) | `tests/blueprint/test_docs_cross_reference.py::BlueprintAgentsMdTests::test_blueprint_agents_md_decisions_scan_rule_present` | ADR | N/A — text instruction, no runtime |

## Acceptance Criteria → Test Mapping

| AC | Test name | Test file | Status |
|---|---|---|---|
| AC-001 | `test_pointers_section_present`, `test_pointers_table_has_placeholder_row` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-002 | `test_mandatory_workflow_rule_present` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-003 | `test_heading_match_without_allowlist_exits_one` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-004 | `test_heading_in_pointers_table_exits_zero` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-005 | `test_heading_in_allowlist_exits_zero` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-006 | `make quality-docs-cross-reference-check` target presence | `make infra-contract-test-fast` | pending |
| AC-007 | `test_absent_agents_md_exits_zero`, `test_absent_north_star_exits_zero`, `test_clean_files_exit_zero`, `test_missing_allowlist_exits_zero` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-008 | `test_blueprint_agents_md_north_star_rule_present` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-009 | `test_decisions_scan_rule_present` | `tests/blueprint/test_docs_cross_reference.py` | pending |
| AC-010 | `test_blueprint_agents_md_decisions_scan_rule_present` | `tests/blueprint/test_docs_cross_reference.py` | pending |

## Validation Summary
- Total unit tests planned: 13 (6 template/blueprint content assertions, 7 detection/edge-case)
- Contract gate: `make infra-contract-test-fast`
- Integration gate: `make quality-hooks-fast`
- Docs gate: `make docs-build` + `make docs-smoke`
- Test result: pending (pre-implementation)
