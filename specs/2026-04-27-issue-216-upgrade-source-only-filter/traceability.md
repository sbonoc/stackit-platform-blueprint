# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008, SDD-C-023, SDD-C-024 | `_filter_source_only` Phase 1 + Phase 2 wired into `resolve_contract_conflict` | `scripts/lib/blueprint/resolve_contract_upgrade.py::_filter_source_only`, `resolve_contract_conflict` | `test_resolve_contract_conflict_source_only_phase1_drop`, `test_resolve_contract_conflict_source_only_claude_md_drop`, `test_resolve_contract_conflict_source_only_phase2_carry_forward` | ADR | Stage 3 stdout log |
| FR-002 | SDD-C-005, SDD-C-008 | `_filter_source_only` function signature and return type | `scripts/lib/blueprint/resolve_contract_upgrade.py::_filter_source_only` | All regression tests | ADR | none |
| FR-003 | SDD-C-005, SDD-C-008 | `ContractResolveResult` extended with `dropped_source_only`, `kept_consumer_source_only` | `scripts/lib/blueprint/resolve_contract_upgrade.py::ContractResolveResult` | All regression tests | none | decisions JSON |
| FR-004 | SDD-C-005 | Decision JSON extended with drop/keep arrays | `scripts/lib/blueprint/resolve_contract_upgrade.py::resolve_contract_conflict` decisions dict | inspection of `artifacts/blueprint/contract_resolve_decisions.json` | none | decisions JSON artifact |
| FR-005 | SDD-C-005, SDD-C-008, SDD-C-024 | Regression test fixture covering Phase 1, Phase 2, backward-compat | `tests/` (new test functions) | All regression tests pass green | ADR | pytest output in pr_context.md |
| NFR-SEC-001 | SDD-C-009 | `Path.exists()` bounded to repo_root; no subprocess | `scripts/lib/blueprint/resolve_contract_upgrade.py::_filter_source_only` | Tests run without external network calls | none | none |
| NFR-OBS-001 | SDD-C-010 | Pipeline stdout logs drop/keep counts | `scripts/lib/blueprint/resolve_contract_upgrade.py::main` | Captured in pr_context.md | none | Stage 3 stdout |
| NFR-REL-001 | SDD-C-008 | Backward compat — no-conflict consumer unchanged | `_filter_source_only` | `test_resolve_contract_conflict_source_only_no_conflict` | none | existing consumers unaffected |
| NFR-OPS-001 | SDD-C-010 | Tests runnable via pytest without k8s | All test files | All regression tests | none | `pytest` run |
| AC-001 | SDD-C-012 | Phase 1 drops `specs` from source_only | `_filter_source_only` Phase 1 | `test_resolve_contract_conflict_source_only_phase1_drop` | | |
| AC-002 | SDD-C-012 | Phase 1 drops `CLAUDE.md` from source_only | `_filter_source_only` Phase 1 | `test_resolve_contract_conflict_source_only_claude_md_drop` | | |
| AC-003 | SDD-C-012 | Phase 2 carries forward consumer-added entry | `_filter_source_only` Phase 2 | `test_resolve_contract_conflict_source_only_phase2_carry_forward` | | |
| AC-004 | SDD-C-012 | infra-validate passes after Phase 1 | fixture-level validate | regression test + smoke | | |
| AC-005 | SDD-C-012 | No-conflict consumer unchanged | `_filter_source_only` | `test_resolve_contract_conflict_source_only_no_conflict` | | |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, AC-001, AC-002, AC-003, AC-004, AC-005

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
- Follow-up: Phase 1 silently drops intentional on-disk `source_only` entries — documented in decisions JSON; matches v1.7.0 semantics.
