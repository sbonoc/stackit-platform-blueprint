# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-012 | required-field check for `context_pack.md` | `scripts/bin/quality/check_sdd_assets.py` | guard test | — | `make quality-hardening-review` |
| FR-002 | SDD-C-005, SDD-C-012 | required-field check for `architecture.md` | `scripts/bin/quality/check_sdd_assets.py` | guard test | — | `make quality-hardening-review` |
| FR-003 | SDD-C-005 | required fields declared in `blueprint/contract.yaml` | `blueprint/contract.yaml` | guard test reads from contract | — | — |
| NFR-OPS-001 | SDD-C-012 | violation message includes path and field name | `scripts/bin/quality/check_sdd_assets.py` | guard failure message | — | `make quality-hardening-review` |
| NFR-REL-001 | SDD-C-012 | "none" and other non-blank values are accepted | `scripts/bin/quality/check_sdd_assets.py` | guard passes on populated docs | — | — |
| AC-001 | SDD-C-012 | quality-hardening-review fails on empty context_pack.md field | test | guard test | — | `make quality-hardening-review` |
| AC-002 | SDD-C-012 | quality-hardening-review fails on empty architecture.md field | test | guard test | — | `make quality-hardening-review` |
| AC-003 | SDD-C-012 | quality-hardening-review passes when all required fields populated | test | guard test | — | `make quality-hardening-review` |
| AC-004 | SDD-C-012 | violation message includes path and field name | `scripts/bin/quality/check_sdd_assets.py` | guard failure message | — | `make quality-hardening-review` |
| AC-005 | SDD-C-012 | infra-contract-test-fast remains green | test suite | 94 passed | — | `make infra-contract-test-fast` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003
  - NFR-OPS-001, NFR-REL-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed: pending
- Result summary: pending
- Documentation validation:
  - `make quality-hooks-fast`
  - `make quality-hardening-review`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- none
