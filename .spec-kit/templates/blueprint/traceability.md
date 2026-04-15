# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 |  |  |  |  |  |
| FR-002 | SDD-C-005 |  |  |  |  |  |
| NFR-SEC-001 | SDD-C-009 |  |  |  |  |  |
| NFR-OBS-001 | SDD-C-010 |  |  |  |  |  |
| AC-001 | SDD-C-012 |  |  |  |  |  |
| AC-002 | SDD-C-012 |  |  |  |  |  |

## Graph Linkage
- Graph file: `graph.yaml`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.yaml`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - NFR-SEC-001
  - NFR-OBS-001
  - AC-001
  - AC-002

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
- Follow-up 1:
