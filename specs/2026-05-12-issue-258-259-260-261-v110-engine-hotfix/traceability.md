# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | N/A | Context A — Contract coverage audit | `blueprint/contract.yaml` (`init_managed`, `conditional_scaffold` entries) | `tests/infra/test_upgrade_contract_coverage.py::*issue_258*` | No doc update required | `make infra-validate` PASS |
| FR-002 | SDD-C-005, SDD-C-024 | N/A | Context B — Validate target filtering | `scripts/lib/blueprint/upgrade_consumer_validate.py` (`VALIDATION_TARGETS` filter by `repo_mode`) | `tests/infra/test_upgrade_consumer_validate.py::*issue_260*` | No doc update required | `make quality-hooks-fast` PASS |
| FR-003 | SDD-C-005, SDD-C-024 | N/A | Context C — Volatile artifact names | `scripts/lib/blueprint/upgrade_fresh_env_gate.py` (`_VOLATILE_ARTIFACT_NAMES` addition) | `tests/infra/test_upgrade_fresh_env_gate.py::*issue_261*` | No doc update required | `make quality-hooks-fast` PASS |
| FR-004 | SDD-C-005, SDD-C-024 | N/A | Context D — Transitive behavioral check | `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` (`_collect_defined_functions_transitive`, bare-command suppression) | `tests/infra/test_upgrade_shell_behavioral_check.py::*issue_259*` | No doc update required | `make quality-hooks-fast` PASS |
| NFR-SEC-001 | SDD-C-009 | N/A | N/A — no security surface | N/A | N/A | N/A | N/A |
| NFR-OBS-001 | SDD-C-010 | N/A | All four fixed modules | Existing WARNING/ERROR log lines preserved; JSON schemas unchanged | Verified by full pytest suite (no schema-breaking assertions fail) | N/A | N/A |
| NFR-REL-001 | SDD-C-008 | N/A | All four fixed modules | Backward-compatible changes only; no existing passing check made failing | Full `tests/infra/` pytest suite PASS | N/A | N/A |
| NFR-OPS-001 | SDD-C-010 | N/A | All regression tests | All tests use pytest fixtures; no network or cluster access | `uv run python3 -m pytest tests/infra/` with no external dependencies | N/A | N/A |
| AC-001 | SDD-C-012 | N/A | Context A | `blueprint/contract.yaml` + `audit_source_tree_coverage` | `tests/infra/test_upgrade_contract_coverage.py::*issue_258*` PASS | N/A | `audit_source_tree_coverage` returns `uncovered_source_files_count=0` |
| AC-002 | SDD-C-012 | N/A | Context B | `upgrade_consumer_validate.py` filter | `tests/infra/test_upgrade_consumer_validate.py::*issue_260*` PASS | N/A | `VALIDATION_TARGETS` excludes `blueprint-template-smoke` for `generated-consumer` mode |
| AC-003 | SDD-C-012 | N/A | Context C | `upgrade_fresh_env_gate.py` volatile set | `tests/infra/test_upgrade_fresh_env_gate.py::*issue_261*` PASS | N/A | `compute_artifact_checksum_divergences` returns `[]` for path-only diff |
| AC-004 | SDD-C-012 | N/A | Context D | `upgrade_shell_behavioral_check.py` transitive resolver | `tests/infra/test_upgrade_shell_behavioral_check.py::*issue_259*` PASS (3 fixtures) | N/A | `behavioral_check_failures_total=0` for blueprint-managed scripts |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004

## Validation Summary
- Required bundles executed: (to be filled during Verify phase)
- Result summary: (to be filled during Verify phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consumers currently relying on the workarounds in their `blueprint/contract.yaml` (`extra_excluded_tokens`, local patches) MUST remove them after adopting the fixed blueprint version. No automated migration is provided — the workaround removal is documented in the consumer upgrade runbook.
