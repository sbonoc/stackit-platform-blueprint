# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Remove 4 paths from `required_files` | `blueprint/contract.yaml` | `test_seed_manifest_paths_not_in_required_files` | spec.md FR-001 | upgrade plan shows source-only/skip for 4 paths |
| FR-002 | SDD-C-005 | Add 4 paths to `source_only_paths` | `blueprint/contract.yaml` | `test_seed_manifest_paths_in_source_only_paths` | spec.md FR-002 | upgrade plan shows source-only ownership |
| FR-003 | SDD-C-005 | Remove 4 paths from `required_paths_when_enabled` | `blueprint/contract.yaml` | `test_app_runtime_required_paths_no_hardcoded_manifest_names` | spec.md FR-003 | n/a |
| FR-004 | SDD-C-005 | Contract content change propagated via upgrade sync | `blueprint/contract.yaml` | upgrade planner test AC-004/AC-005 | ADR | n/a |
| NFR-SEC-001 | SDD-C-009 | Config-only change; no I/O or credential handling | n/a | no new security surface | n/a | n/a |
| NFR-OBS-001 | SDD-C-010 | source-only classification appears in plan output | upgrade planner classification | upgrade plan output | n/a | plan JSON |
| NFR-REL-001 | SDD-C-011 | source-only classification preserves existing files unchanged | upgrade_consumer.py source_only logic | AC-005 test | n/a | n/a |
| NFR-OPS-001 | SDD-C-010 | audit_source_tree_coverage passes with source_only | upgrade_consumer.py | T-105 | n/a | template-source CI |
| AC-001 | SDD-C-012 | 4 paths in source_only, NOT in required_files | `blueprint/contract.yaml` | `test_seed_manifest_paths_not_in_required_files` + `test_seed_manifest_paths_in_source_only_paths` | n/a | n/a |
| AC-002 | SDD-C-012 | 4 paths NOT in required_paths_when_enabled | `blueprint/contract.yaml` | `test_app_runtime_required_paths_no_hardcoded_manifest_names` | n/a | n/a |
| AC-003 | SDD-C-012 | audit_source_tree_coverage passes | upgrade_consumer.py | T-105 | n/a | template-source CI |
| AC-004 | SDD-C-012 | consumer-renamed manifests → no create/delete in plan | upgrade planner | upgrade planner test | n/a | upgrade plan |
| AC-005 | SDD-C-012 | original seed names → source-only/skip in plan | upgrade planner | upgrade planner test | n/a | upgrade plan |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005

## Validation Summary
- Required bundles executed: deferred to implementation work item
- Result summary: deferred to implementation work item
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Option B — `consumer_workload_manifest_paths` schema field for explicit preflight validation of consumer-named manifests. Tracked in backlog as enhancement after this spec ships.
- Follow-up 2: Verify that removing the 4 paths from `app_runtime_gitops_contract.required_paths_when_enabled` does not break `init_repo_contract.py` init-time scaffolding for fresh `blueprint-init-repo` runs (bootstrap.sh's `ensure_infra_template_file` mechanism is separate and unaffected — verify with a fresh init test).
