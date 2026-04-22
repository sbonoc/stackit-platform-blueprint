# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Postgres module contract key correction | `blueprint/modules/postgres/module.contract.yaml` | AC-001 | ADR | none |
| FR-002 | SDD-C-005 | Stale module target detection in upgrade consumer | `scripts/lib/blueprint/upgrade_consumer.py:_collect_stale_module_target_actions` | AC-003, AC-005 | ADR | none |
| FR-003 | SDD-C-005 | Detection scoped to existing reference paths | `scripts/lib/blueprint/upgrade_consumer.py` | AC-005 | ADR | none |
| FR-004 | SDD-C-005 | Mode guard: skip in template-source mode | `scripts/lib/blueprint/upgrade_consumer.py` | AC-004, AC-005 | ADR | none |
| NFR-SEC-001 | SDD-C-009 | In-process Python file reads only | `scripts/lib/blueprint/upgrade_consumer.py` | AC-005 | none | none |
| NFR-OBS-001 | SDD-C-010 | File path and target name in RequiredManualAction reason | `scripts/lib/blueprint/upgrade_consumer.py` | AC-003 | none | none |
| NFR-REL-001 | SDD-C-011 | Read errors collected, not raised | `scripts/lib/blueprint/upgrade_consumer.py` | AC-004 | none | none |
| NFR-OPS-001 | SDD-C-014 | No operator action needed for key rename | `blueprint/modules/postgres/module.contract.yaml` | AC-001 | none | none |
| AC-001 | SDD-C-012 | postgres module contract outputs field | `blueprint/modules/postgres/module.contract.yaml` | test_tooling_contracts.py | ADR | none |
| AC-002 | SDD-C-012 | ESO key-contract parity test | `tests/infra/test_tooling_contracts.py` or `tests/blueprint/` | AC-002 test | ADR | none |
| AC-003 | SDD-C-012 | Stale reference detection positive path | `tests/blueprint/test_upgrade_consumer.py` | unit test | none | none |
| AC-004 | SDD-C-012 | No false positives in template-source or all-present | `tests/blueprint/test_upgrade_consumer.py` | unit test | none | none |
| AC-005 | SDD-C-012 | Unit test for AC-003 and AC-004 | `tests/blueprint/test_upgrade_consumer.py` | unit test | none | none |

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
- Required bundles executed:
- Result summary:
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- none
