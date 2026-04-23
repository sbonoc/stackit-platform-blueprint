# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | `ensure_infra_template_file` consumer_seeded guard | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md FR-001 | bootstrap stdout skip log |
| FR-002 | SDD-C-005 | `ensure_infra_rendered_file` consumer_seeded guard | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md FR-002 | bootstrap stdout skip log |
| NFR-SEC-001 | SDD-C-009 | `blueprint_path_is_consumer_seeded` helper (existing) | `scripts/lib/blueprint/contract_runtime.sh` | all bootstrap tests | spec.md NFR-SEC-001 | N/A |
| NFR-OBS-001 | SDD-C-010 | `infra_consumer_seeded_skip_count` metric + `log_info` | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md NFR-OBS-001 | bootstrap stdout metric |
| NFR-REL-001 | SDD-C-012 | silent skip when file absent | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md NFR-REL-001 | N/A |
| NFR-OPS-001 | SDD-C-010 | `log_info "skipping consumer-seeded file (consumer-owned): $relative_path"` | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md NFR-OPS-001 | bootstrap stdout |
| AC-001 | SDD-C-012 | consumer_seeded guard returns 0 without calling `ensure_file_from_template` | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md AC-001 | N/A |
| AC-002 | SDD-C-010 | `log_metric "infra_consumer_seeded_skip_count"` | `scripts/bin/infra/bootstrap.sh` | `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos` | spec.md AC-002 | bootstrap stdout |
| AC-003 | SDD-C-012 | guard conditioned on `blueprint_path_is_consumer_seeded`; non-seeded paths fall through | `scripts/bin/infra/bootstrap.sh` | existing `test_infra_bootstrap_does_not_recreate_init_managed_files_in_generated_repos` | spec.md AC-003 | N/A |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k infra_bootstrap -v`
- Result summary: 2/2 targeted tests pass; quality-hooks-fast green
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None. The fix is additive and uses the existing `consumer_seeded` contract infrastructure.
