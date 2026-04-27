# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008, SDD-C-023, SDD-C-024 | Extend `all_coverage_roots` with prune-glob matches | `scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage` | `test_audit_source_tree_coverage_prune_glob_coverage` | `docs/blueprint/consumer/contract_reference.md` | stderr WARNING preserved for genuinely uncovered files |
| FR-002 | SDD-C-005, SDD-C-008 | Change `exists()` to `is_file()` in `_validate_absent_files` | `scripts/bin/blueprint/validate_contract.py::_validate_absent_files` | `test_validate_absent_files_directory_entry`, `test_validate_absent_files_exact_file_present` | `docs/blueprint/consumer/contract_reference.md` | `make infra-validate` output change |
| FR-003 | SDD-C-005, SDD-C-008, SDD-C-023 | Glob-pattern entry support in `_validate_absent_files` | `scripts/bin/blueprint/validate_contract.py::_validate_absent_files` | `test_validate_absent_files_glob_matching`, `test_validate_absent_files_glob_no_match` | `docs/blueprint/consumer/contract_reference.md` | `make infra-validate` output change |
| FR-004 | SDD-C-005, SDD-C-008, SDD-C-024 | Regression fixture covering directory, glob, and prune-glob cases | `tests/` (new test functions) | All 5 regression tests pass green | ADR | pytest run evidence in pr_context.md |
| NFR-SEC-001 | SDD-C-009 | Glob expansion bounded to repo root via `fnmatch` on pre-enumerated file list | `scripts/bin/blueprint/validate_contract.py`, `scripts/lib/blueprint/upgrade_consumer.py` | `test_validate_absent_files_glob_no_match` (no external calls) | Architecture section | none |
| NFR-OBS-001 | SDD-C-010 | stderr WARNING preserved for uncovered files | `scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage` | Existing audit tests | none | stderr output |
| NFR-REL-001 | SDD-C-008 | Backward compat — exact-file entries unchanged | `scripts/bin/blueprint/validate_contract.py::_validate_absent_files` | `test_validate_absent_files_exact_file_present` | none | existing consumer infra-validate unaffected |
| NFR-OPS-001 | SDD-C-010 | Tests runnable via pytest without k8s | All test files | All regression tests | none | `make quality-contract-test-fast` |
| AC-001 | SDD-C-012 | prune-glob files not in uncovered list | `audit_source_tree_coverage` | `test_audit_source_tree_coverage_prune_glob_coverage` | | |
| AC-002 | SDD-C-012 | directory entry no longer triggers absent error | `_validate_absent_files` | `test_validate_absent_files_directory_entry` | | |
| AC-003 | SDD-C-012 | glob entry matches file → error emitted | `_validate_absent_files` | `test_validate_absent_files_glob_matching` | | |
| AC-004 | SDD-C-012 | glob entry with no matching file → no error | `_validate_absent_files` | `test_validate_absent_files_glob_no_match` | | |
| AC-005 | SDD-C-012 | exact-file entry with file present → error (backward compat) | `_validate_absent_files` | `test_validate_absent_files_exact_file_present` | | |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed: (to be populated at Verify phase)
- Result summary: (to be populated at Verify phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: Glob support for `source_only` in other validation contexts (e.g. template coverage checks) is deferred; this fix targets only `_validate_absent_files` and `audit_source_tree_coverage`.
