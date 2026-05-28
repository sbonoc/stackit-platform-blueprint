# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-011 | N/A | architecture.md § Bounded Contexts — Context A | docs/blueprint/autonomous-factory/design-contracts.md | make docs-build, make docs-smoke | docs/blueprint/autonomous-factory/design-contracts.md | none (documentation-only) |
| FR-002 | SDD-C-005 | N/A | architecture.md § Integration and Dependency Edges | docs/blueprint/autonomous-factory/design-contracts.md (Referenced by: lines per section) | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-003 | SDD-C-019 | N/A | spec.md § Informative Notes § Clarifications | docs/blueprint/autonomous-factory/design-contracts.md (### Open Decisions subsections) | make quality-sdd-check | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-004 | SDD-C-004 | N/A | architecture.md § High-Level Component Design | docs/blueprint/autonomous-factory/design-contracts.md § Contract C1 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-005 | SDD-C-004 | N/A | architecture.md § Integration and Dependency Edges | docs/blueprint/autonomous-factory/design-contracts.md § Contract C2 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-006 | SDD-C-004, SDD-C-006 | N/A | architecture.md § High-Level Component Design | docs/blueprint/autonomous-factory/design-contracts.md § Contract C3 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-007 | SDD-C-004 | N/A | architecture.md § Bounded Contexts — Context B | docs/blueprint/autonomous-factory/design-contracts.md § Contract C4 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-008 | SDD-C-004, SDD-C-009 | N/A | architecture.md § Non-Functional Architecture Notes — Security | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-009 | SDD-C-004 | N/A | architecture.md § Bounded Contexts — Context C | docs/blueprint/autonomous-factory/design-contracts.md § Contract C6 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-010 | SDD-C-004, SDD-C-010 | N/A | architecture.md § Non-Functional Architecture Notes — Observability | docs/blueprint/autonomous-factory/design-contracts.md § Contract C7 | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-011 | SDD-C-003 | N/A | architecture.md § High-Level Component Design | docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | make docs-build | docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | none |
| FR-012 | SDD-C-020 | N/A | spec.md § Spec Readiness Gate | PR comment thread on the Draft PR (sign-off phrases per AGENTS.md) | PR comment thread | spec.md § Spec Readiness Gate (recorded sign-offs) | none |
| NFR-SEC-001 | SDD-C-009 | N/A | architecture.md § Non-Functional Architecture Notes — Security | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 | reviewer checklist (exact-string equality, not regex) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 | none |
| NFR-OBS-001 | SDD-C-010 | N/A | architecture.md § Non-Functional Architecture Notes — Observability | docs/blueprint/autonomous-factory/design-contracts.md § Contract C7 | reviewer checklist (named schema with types + nullability) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C7 | none |
| NFR-REL-001 | SDD-C-016 | N/A | architecture.md § Risks and Tradeoffs — Risk 2 | docs/blueprint/autonomous-factory/design-contracts.md (Referenced by: lines per section) | reviewer checklist on downstream PRs | docs/blueprint/autonomous-factory/design-contracts.md | none |
| NFR-OPS-001 | SDD-C-011, SDD-C-012 | N/A | plan.md § Validation Strategy — Documentation checks | docs/blueprint/autonomous-factory/design-contracts.md and docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | make docs-build, make docs-smoke | both new files appear in built docs nav | none |
| AC-001 | SDD-C-012, SDD-C-019 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md | reviewer checklist + make quality-sdd-check | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-002 | SDD-C-012 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md (Referenced by: lines) | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-003 | SDD-C-020 | N/A | spec.md § Acceptance Criteria | PR comment thread | PR comment thread | spec.md § Spec Readiness Gate | none |
| AC-004 | SDD-C-019 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md (### Open Decisions) | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-005 | SDD-C-003 | N/A | spec.md § Acceptance Criteria | docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | reviewer checklist | docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | none |
| AC-006 | SDD-C-001, SDD-C-005 | N/A | spec.md § Acceptance Criteria | specs/2026-05-28-issue-339-factory-design-contracts/ | make quality-sdd-check | none | none |
| AC-007 | SDD-C-011 | N/A | spec.md § Acceptance Criteria | docs/blueprint/ | make docs-build, make docs-smoke | docs/blueprint/ | none |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: (to be filled after Step 7 — `make quality-sdd-check`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`)
- Result summary: (to be filled after Step 7)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: resolve Q-1 (factory bot final handle) during #334; update Contract C5 `### Open Decisions` in the same PR.
- Follow-up 2: resolve Q-2 (CODEOWNERS team slugs + bounded-context enumeration) during #337; update Contract C6 `### Open Decisions` in the same PR.
- Follow-up 3: resolve Q-3 (metrics dashboard platform) during #337; update Contract C7 `### Open Decisions` in the same PR.
