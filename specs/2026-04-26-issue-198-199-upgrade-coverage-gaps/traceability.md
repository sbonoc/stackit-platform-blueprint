# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-004, SDD-C-005 | `VALIDATION_TARGETS` tuple | `scripts/lib/blueprint/upgrade_consumer_validate.py:28-35` | `test_blueprint_template_smoke_in_validation_targets` [planned] | — | `make quality-hooks-fast` |
| FR-005 | SDD-C-004, SDD-C-005 | `VALIDATION_TARGETS` tuple | `scripts/lib/blueprint/upgrade_consumer_validate.py:28-35` | `test_infra_argocd_topology_validate_in_validation_targets` [planned] | — | `make quality-hooks-fast` |
| FR-002 | SDD-C-004, SDD-C-005, SDD-C-007 | `RepositoryOwnershipPathClasses.feature_gated` | `scripts/lib/blueprint/contract_schema.py:44-48` | `test_feature_gated_paths_covered` [planned] | — | `make infra-validate` |
| FR-003 | SDD-C-004, SDD-C-008 | `audit_source_tree_coverage(feature_gated=...)` | `scripts/lib/blueprint/upgrade_consumer.py:336-386` | `test_feature_gated_paths_covered` [planned] | — | `make infra-validate` |
| FR-004 | SDD-C-004, SDD-C-005 | `ownership_path_classes.feature_gated` YAML | `blueprint/contract.yaml:597-638` (ownership block, insertion after line 638), bootstrap template mirror | `make infra-validate` + schema loader test [planned] | — | `make infra-validate` |
| NFR-SEC-001 | SDD-C-009 | No secret/authn changes | — | — | — | No runtime surface changed |
| NFR-OBS-001 | SDD-C-010 | Error message in `validate_plan_uncovered_source_files` | `scripts/lib/blueprint/upgrade_consumer.py:399` | AC-007 (code inspection) [planned] | — | — |
| NFR-REL-001 | SDD-C-012 | Rollback = `git revert`; default-empty param | Backward-compat default in `audit_source_tree_coverage` | All pre-existing `TestAuditSourceTreeCoverage` tests remain green (AC-005) | — | — |
| NFR-OPS-001 | SDD-C-010 | `blueprint-template-smoke` and `infra-argocd-topology-validate` are read-only, no side effects | `scripts/bin/blueprint/template_smoke.sh`; `scripts/bin/infra/argocd_topology_validate.sh` | `tests/blueprint/contract_refactor_governance_init_cases.py:45,52` (blueprint-template-smoke); `tests/infra/test_tooling_contracts.py:test_argocd_topology_validate_uses_explicit_load_restrictor_none`; `tests/e2e/test_vertical_slice.py:173` (infra-argocd-topology-validate) | — | — |
| FR-006 | SDD-C-004, SDD-C-005 | `_IndentedDumper` in `resolve_contract_upgrade.py` | `scripts/lib/blueprint/resolve_contract_upgrade.py:208-214` | `test_resolve_contract_yaml_dump_uses_indented_style` [planned] | — | — |
| AC-001 | SDD-C-012 | `VALIDATION_TARGETS` membership | `upgrade_consumer_validate.py` | `test_blueprint_template_smoke_in_validation_targets` [planned] | — | — |
| AC-006 | SDD-C-012 | `VALIDATION_TARGETS` membership | `upgrade_consumer_validate.py` | `test_infra_argocd_topology_validate_in_validation_targets` [planned] | — | — |
| AC-002 | SDD-C-012 | `audit_source_tree_coverage` + `feature_gated` | `upgrade_consumer.py` | `test_feature_gated_paths_covered` [planned] | — | — |
| AC-003 | SDD-C-012 | `validate_contract.py` accepts `feature_gated` | `validate_contract.py` | `test_feature_gated_no_validation_errors` [planned] | — | — |
| AC-004 | SDD-C-012 | `make infra-validate` pass | `blueprint/contract.yaml` + bootstrap template | `make infra-validate` output | — | — |
| AC-005 | SDD-C-008, SDD-C-012 | Backward-compat default | `upgrade_consumer.py` | All pre-existing `TestAuditSourceTreeCoverage` tests green | — | — |
| AC-007 | SDD-C-010, SDD-C-012 | `validate_plan_uncovered_source_files` error string | `scripts/lib/blueprint/upgrade_consumer.py:399` | Code inspection: string must include `feature_gated` [planned] | — | — |
| AC-008 | SDD-C-008, SDD-C-012 | yaml.dump output format in `resolve_contract_upgrade.py` | `scripts/lib/blueprint/resolve_contract_upgrade.py:208-214` | `test_resolve_contract_yaml_dump_uses_indented_style` [planned] | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007
  - FR-006
  - AC-008

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
- Follow-up 1: If additional feature-flag-gated paths are added to `app_catalog_scaffold_contract` in the future, they must also be added to `feature_gated` in `contract.yaml` — consider adding a validator that cross-checks the two lists.
- Follow-up 2: All test names marked `[planned]` must be confirmed as implemented and green before the Publish gate is opened (SPEC_READY is already true; planned tests must be green before closing the PR).
