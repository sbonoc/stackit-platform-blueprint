# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-017 | Contract-backed docs allowlist source | `blueprint/contract.yaml`; `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`; `scripts/lib/blueprint/contract_schema.py`; `scripts/lib/docs/sync_blueprint_template_docs.py` | `tests/blueprint/test_quality_contracts.py::test_blueprint_docs_template_sync_prunes_source_only_docs`; `tests/blueprint/contract_refactor_governance_init_cases.py` | `docs/blueprint/governance/ownership_matrix.md`; template mirror docs | `make quality-docs-check-blueprint-template-sync` |
| FR-002 | SDD-C-005, SDD-C-012 | Prune-glob documentation checker in contract validation lane | `scripts/lib/blueprint/contract_validators/docs_sync.py`; `scripts/bin/blueprint/validate_contract.py` | `tests/blueprint/test_quality_contracts.py::test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows`; `tests/blueprint/contract_refactor_docs_cases.py` | `docs/blueprint/governance/ownership_matrix.md` | `make infra-validate` |
| FR-003 | SDD-C-017 | Bootstrap docs mirror parity from contract allowlist | `scripts/lib/docs/sync_blueprint_template_docs.py`; `scripts/templates/blueprint/bootstrap/docs/blueprint/governance/assistant_compatibility.md` | `tests/blueprint/contract_refactor_docs_cases.py`; `tests/blueprint/test_quality_contracts.py::test_blueprint_docs_template_sync_prunes_source_only_docs` | `docs/README.md`; `docs/blueprint/README.md`; `docs/blueprint/governance/spec_driven_development.md` | `make quality-docs-check-blueprint-template-sync` |
| NFR-SEC-001 | SDD-C-009 | Safe prune behavior hardening | `scripts/lib/blueprint/init_repo_contract.py`; `scripts/lib/blueprint/init_repo_io.py` | `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks` | `spec.md` normative section | `make infra-validate` |
| NFR-OBS-001 | SDD-C-010 | Explicit contract validation diagnostics | `scripts/lib/blueprint/contract_validators/docs_sync.py` | `tests/blueprint/test_quality_contracts.py::test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows` | `hardening_review.md` | `make infra-validate` |
| NFR-REL-001 | SDD-C-011 | Deterministic local validation path | `scripts/bin/blueprint/validate_contract.py` | `tests/blueprint/contract_refactor_docs_cases.py` | `plan.md` validation strategy | `make infra-validate` |
| NFR-OPS-001 | SDD-C-018 | Governance/docs/tests synchronization | `AGENTS.decisions.md`; `docs/blueprint/governance/ownership_matrix.md`; `tests/blueprint/**` | `tests/blueprint/contract_refactor_docs_cases.py`; `tests/blueprint/contract_refactor_governance_init_cases.py` | `pr_context.md` | `make quality-hardening-review` |
| AC-001 | SDD-C-012 | Missing pattern detection | `scripts/lib/blueprint/contract_validators/docs_sync.py` | `tests/blueprint/test_quality_contracts.py::test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows` | `spec.md` acceptance criteria | `make infra-validate` |
| AC-002 | SDD-C-012 | Complete pattern mapping success path | `scripts/lib/blueprint/contract_validators/docs_sync.py` | `tests/blueprint/test_quality_contracts.py::test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows` | `spec.md` acceptance criteria | `make infra-validate` |
| AC-003 | SDD-C-012 | Allowlist-driven mirror parity | `scripts/lib/docs/sync_blueprint_template_docs.py`; template docs mirror | `tests/blueprint/contract_refactor_docs_cases.py`; `tests/blueprint/test_quality_contracts.py::test_blueprint_docs_template_sync_prunes_source_only_docs` | `docs/blueprint/governance/assistant_compatibility.md` | `make quality-docs-check-blueprint-template-sync` |

## Graph Linkage
- Graph file: `graph.yaml`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file has a corresponding node in `graph.yaml`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows tests.blueprint.test_quality_contracts.QualityContractsTests.test_blueprint_docs_template_sync_prunes_source_only_docs tests.blueprint.test_quality_contracts.QualityContractsTests.test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks tests.blueprint.contract_refactor_docs_cases.DocsRefactorCases.test_bootstrap_docs_templates_are_synchronized tests.blueprint.contract_refactor_governance_init_cases.GovernanceInitRepoCases.test_blueprint_template_init_assets_exist`
  - `make quality-docs-check-blueprint-template-sync`
  - `make quality-sdd-check`
  - `make quality-hardening-review`
  - `make infra-validate`
- Result summary: all commands listed above passed on branch `codex/2026-04-17-prune-glob-ownership-check`.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: add normalization guidance for future glob-pattern formatting so ownership docs checker remains resilient to equivalent pattern variants.
