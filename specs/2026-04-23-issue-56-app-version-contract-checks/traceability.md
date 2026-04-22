# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | `check_versions_lock` | `scripts/lib/platform/apps/version_contract_checker.py` | `CheckVersionsLockTests` | spec.md FR-001 | per-check stdout report |
| FR-002 | SDD-C-005 | `check_manifest_yaml` | `scripts/lib/platform/apps/version_contract_checker.py` | `CheckManifestYamlTests` | spec.md FR-002 | per-check stdout report |
| FR-003 | SDD-C-006 | catalog-check invocation + `apps_version_contract_check_total` | `scripts/bin/platform/apps/audit_versions.sh` | `MainTests::test_catalog_check_mode_exits_nonzero_when_lock_stale` | spec.md FR-003 | `apps_version_contract_check_total` metric |
| FR-004 | SDD-C-006 | conditional fingerprint expansion | `scripts/bin/platform/apps/audit_versions_cached.sh` | `test_catalog_check_mode_exits_zero_when_all_pass` (indirect) | spec.md FR-004 | cache file fingerprint |
| FR-005 | SDD-C-005 | consistency-check invocation in smoke | `scripts/bin/platform/apps/smoke.sh` | `CheckCatalogConsistencyTests`, `MainTests::test_consistency_mode_exits_nonzero_when_stale_lock` | spec.md FR-005 | smoke stdout report |
| FR-006 | SDD-C-009 | `re.search` text-match; no PyYAML | `scripts/lib/platform/apps/version_contract_checker.py` | all `CheckManifestYamlTests` | spec.md FR-006 | N/A |
| FR-007 | SDD-C-010 | `ContractCheckResult.detail` + `_print_report` | `scripts/lib/platform/apps/version_contract_checker.py` | `test_single_var_mismatch_returns_failed_result` (both lock and manifest) | spec.md FR-007 | stdout output |
| NFR-SEC-001 | SDD-C-009 | `pathlib.Path.read_text`; no subprocess | `scripts/lib/platform/apps/version_contract_checker.py` | `ParseLockFileTests` | architecture.md NFR Notes | N/A |
| NFR-OBS-001 | SDD-C-010 | `apps_version_contract_check_total` metric; extended summary metric | `scripts/bin/platform/apps/audit_versions.sh` | manual: `make apps-audit-versions` | spec.md NFR-OBS-001 | log output |
| NFR-REL-001 | SDD-C-011 | missing-file skip logic | `scripts/lib/platform/apps/version_contract_checker.py` | `test_missing_lock_file_returns_skipped_passed`, `test_missing_manifest_file_returns_skipped_passed`, `test_catalog_check_mode_skips_when_catalog_files_absent` | spec.md NFR-REL-001 | N/A |
| NFR-OPS-001 | SDD-C-010 | `_print_report` human-readable output | `scripts/lib/platform/apps/version_contract_checker.py` | `MainTests` | spec.md NFR-OPS-001 | stdout |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make infra-validate`, `python3 -m pytest tests/infra/test_version_contract_checker.py -v`
- Result summary: 22/22 tests pass; quality-hooks-fast green
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: optional PyYAML-based manifest validation for improved robustness — deferred to a future work item.
- Follow-up 2: source file contract checks (`pyproject.toml`, `package.json`) — deferred; consumer-owned.
