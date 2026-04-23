# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | SemanticAnnotation dataclass + UpgradeEntry.semantic field |  |  |  |  |
| FR-002 | SDD-C-005 | kind closed-set enum + detection order in annotator |  |  |  |  |
| FR-003 | SDD-C-005 | upgrade_semantic_annotator.py static diff analysis |  |  |  |  |
| FR-004 | SDD-C-005 | per-entry try/except fallback in annotator |  |  |  |  |
| FR-005 | SDD-C-005 | UpgradeEntry.as_dict() + upgrade_plan.schema.json |  |  |  |  |
| FR-006 | SDD-C-005 | upgrade_summary.md renderer in upgrade_consumer.py |  |  |  |  |
| FR-007 | SDD-C-005 | ApplyResult.as_dict() + upgrade_apply.schema.json |  |  |  |  |
| NFR-SEC-001 | SDD-C-009 | static regex only; no subprocess with file content |  |  |  |  |
| NFR-OBS-001 | SDD-C-010 | plan generation log statements for annotation counts |  |  |  |  |
| NFR-REL-001 | SDD-C-011 | per-entry fallback + backward-compatible schema change |  |  |  |  |
| NFR-OPS-001 | SDD-C-013 | kind enum documented in upgrade reference docs |  |  |  |  |
| AC-001 | SDD-C-012 |  |  |  |  |  |
| AC-002 | SDD-C-012 |  |  |  |  |  |
| AC-003 | SDD-C-012 |  |  |  |  |  |
| AC-004 | SDD-C-012 |  |  |  |  |  |
| AC-005 | SDD-C-012 |  |  |  |  |  |
| AC-006 | SDD-C-012 |  |  |  |  |  |
| AC-007 | SDD-C-012 |  |  |  |  |  |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - FR-007
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
- Follow-up 1: Extend annotation detection coverage (non-shell file types, transitive source-chain analysis) if structural-change fallback rate is high in practice.
