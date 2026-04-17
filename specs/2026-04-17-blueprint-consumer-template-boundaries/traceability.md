# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-021 | Contract-level source-artifact prune declaration | `blueprint/contract.yaml`; `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`; `scripts/lib/blueprint/contract_schema.py` | `tests/blueprint/contract_refactor_governance_structure_cases.py`; `tests/blueprint/contract_refactor_governance_init_cases.py` | `docs/blueprint/governance/ownership_matrix.md` | `make infra-validate` |
| FR-002 | SDD-C-005, SDD-C-021 | Initial-mode-only prune helper wired into consumer seed flow with path-safety guards | `scripts/lib/blueprint/init_repo_contract.py`; `scripts/lib/blueprint/init_repo_io.py` | `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode`; `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks` | `AGENTS.decisions.md` | `make quality-hooks-run`; `make infra-validate` |
| FR-003 | SDD-C-005, SDD-C-017 | Explicit allowlist blueprint docs sync for bootstrap template | `scripts/lib/docs/sync_blueprint_template_docs.py`; `scripts/templates/blueprint/bootstrap/docs/blueprint/governance/ownership_matrix.md` | `tests/blueprint/test_quality_contracts.py::test_blueprint_docs_template_sync_prunes_source_only_docs`; `tests/blueprint/contract_refactor_docs_cases.py` | `docs/blueprint/governance/ownership_matrix.md`; `AGENTS.md` | `make quality-docs-check-blueprint-template-sync` |
| NFR-SEC-001 | SDD-C-009 | Contract-bounded prune scope with unsafe-pattern and out-of-root safeguards | `scripts/lib/blueprint/contract_schema.py`; `scripts/lib/blueprint/init_repo_contract.py`; `scripts/lib/blueprint/init_repo_io.py` | `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode`; `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks` | `AGENTS.decisions.md` | `make infra-validate` |
| NFR-OBS-001 | SDD-C-010 | Deterministic diagnostics from summary/check gates | `scripts/lib/docs/sync_blueprint_template_docs.py`; `scripts/lib/blueprint/init_repo_contract.py` | `tests/blueprint/test_quality_contracts.py`; `tests/blueprint/contract_refactor_docs_cases.py` | `specs/2026-04-17-blueprint-consumer-template-boundaries/hardening_review.md` | `make quality-hooks-run`; `make quality-hardening-review` |
| NFR-REL-001 | SDD-C-011 | Idempotent safety on generated-consumer re-runs | `scripts/lib/blueprint/init_repo_contract.py` | `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode` | `AGENTS.decisions.md` | `make infra-validate` |
| NFR-OPS-001 | SDD-C-012, SDD-C-018 | Governance and ownership boundary documentation + checks | `AGENTS.md`; `AGENTS.decisions.md`; `docs/blueprint/governance/ownership_matrix.md` | `scripts/bin/quality/check_sdd_assets.py`; `tests/blueprint/contract_refactor_docs_cases.py` | `specs/2026-04-17-blueprint-consumer-template-boundaries/pr_context.md` | `make quality-sdd-check`; `make quality-hardening-review` |
| AC-001 | SDD-C-012 | Initial-mode prune outcome | `scripts/lib/blueprint/init_repo_contract.py` | `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode` | `spec.md` acceptance criteria section | `make infra-validate` |
| AC-002 | SDD-C-012 | Generated-consumer mode preserves matched paths and blocks unsafe/out-of-root prune candidates | `scripts/lib/blueprint/init_repo_contract.py`; `scripts/lib/blueprint/init_repo_io.py` | `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode`; `tests/blueprint/test_quality_contracts.py::test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks` | `spec.md` acceptance criteria section | `make infra-validate` |
| AC-003 | SDD-C-012 | Template mirror keeps allowlisted parity and prunes source-only docs | `scripts/lib/docs/sync_blueprint_template_docs.py` | `tests/blueprint/test_quality_contracts.py::test_blueprint_docs_template_sync_prunes_source_only_docs`; `tests/blueprint/contract_refactor_docs_cases.py` | `docs/blueprint/governance/ownership_matrix.md` | `make quality-docs-check-blueprint-template-sync` |

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
  - `make quality-hooks-run`
  - `make infra-validate`
  - `make quality-hardening-review`
  - `make quality-docs-sync-all`
  - `make quality-docs-check-changed`
  - `make docs-build`
  - `make docs-smoke`
- Result summary: targeted tests, docs gates, SDD gates, and `infra-validate` passed. `quality-hooks-run` passed once and later failed in strict lane due external registry lookup reporting missing `quay.io/oauth2-proxy/oauth2-proxy:v7.15.0` after prior successful resolution.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: add a dedicated checker that verifies every docs allowlist path in contract is present in the template sync parity test matrix.
