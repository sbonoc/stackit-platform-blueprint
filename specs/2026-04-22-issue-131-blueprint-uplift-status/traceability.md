# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | `_parse_backlog` + `_UNCHECKED_LINE` + `_backlog_pattern` | `scripts/lib/blueprint/uplift_status.py` | `BacklogParsingTests` in `test_uplift_status.py` | spec.md FR-001 | N/A |
| FR-002 | SDD-C-005 | `_query_issue_state` | `scripts/lib/blueprint/uplift_status.py` | `QueryIssueStateTests` in `test_uplift_status.py` | spec.md FR-002 | log_metric query_failures |
| FR-003 | SDD-C-005 | `_build_report` classification logic | `scripts/lib/blueprint/uplift_status.py` | `BuildReportTests` in `test_uplift_status.py` | spec.md FR-003 | JSON artifact `classification` field |
| FR-004 | SDD-C-006 | `_write_json` | `scripts/lib/blueprint/uplift_status.py` | `MainIntegrationTests` in `test_uplift_status.py` | spec.md FR-004 | `artifacts/blueprint/uplift_status.json` |
| FR-005 | SDD-C-006 | `_print_table` / `_emit_metrics` | `scripts/lib/blueprint/uplift_status.py` | `MainIntegrationTests` in `test_uplift_status.py` | spec.md FR-005 | N/A |
| FR-006 | SDD-C-005 | strict mode exit logic in `main()` | `scripts/lib/blueprint/uplift_status.py` | `BuildReportTests`, `MainIntegrationTests` | spec.md FR-006 | exit code |
| FR-007 | SDD-C-006 | `set_default_env BLUEPRINT_UPLIFT_REPO` | `scripts/bin/blueprint/uplift_status.sh` | `MainIntegrationTests::test_missing_uplift_repo_exits_nonzero` | spec.md FR-007 | shell wrapper usage |
| FR-008 | SDD-C-007 | make target definition | `make/blueprint.generated.mk`, `blueprint.generated.mk.tmpl` | `make blueprint-uplift-status --dry-run` | `core_targets.generated.md` | N/A |
| NFR-SEC-001 | SDD-C-009 | `pathlib` reads; `gh --repo` flag | `scripts/lib/blueprint/uplift_status.py` | `BacklogParsingTests` | architecture.md NFR Notes | N/A |
| NFR-OBS-001 | SDD-C-010 | `_build_report` fields; `_write_json` | `scripts/lib/blueprint/uplift_status.py` | `BuildReportTests::test_report_contains_required_fields` | spec.md NFR-OBS-001 | `artifacts/blueprint/uplift_status.json` |
| NFR-REL-001 | SDD-C-011 | missing file guard in `_parse_backlog`; exception catch in `_query_issue_state` | `scripts/lib/blueprint/uplift_status.py` | `BacklogParsingTests::test_missing_backlog_file_returns_empty`, `QueryIssueStateTests::test_exception_returns_unknown` | spec.md NFR-REL-001 | N/A |
| NFR-OPS-001 | SDD-C-010 | `emit_uplift_metrics` in shell wrapper | `scripts/bin/blueprint/uplift_status.sh` | manual: `make blueprint-uplift-status` | architecture.md NFR Notes | log output |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: `make quality-sdd-check`, `make quality-sdd-check-all`, `make quality-hooks-fast`, `python3 -m pytest tests/blueprint/test_uplift_status.py -v`
- Result summary: all 32 tests pass; quality-hooks-fast green
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: optional integration into `blueprint-upgrade-consumer-validate` behind an env gate (non-breaking default off) — deferred to a future work item.
