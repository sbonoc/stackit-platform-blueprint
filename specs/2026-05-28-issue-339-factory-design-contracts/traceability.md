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
| FR-013 | SDD-C-004, SDD-C-013, SDD-C-014 | N/A | architecture.md § Bounded Contexts — Context D | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | reviewer checklist (four named surface categories) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| FR-014 | SDD-C-004, SDD-C-009 | N/A | architecture.md § Integration and Dependency Edges | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (LiteLLM external configuration shape) | reviewer checklist (ESO key reference, model allowlist) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| FR-015 | SDD-C-004, SDD-C-017 | N/A | architecture.md § Bounded Contexts — Context D | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (stability tiers) | reviewer checklist (every surface item tier-tagged) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| FR-016 | SDD-C-005, SDD-C-019 | N/A | spec.md § Explicit Exclusions (item 5) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 / C6 / C7 (### Consumer overlay subsections) | reviewer checklist (zero concrete consumer values) | docs/blueprint/autonomous-factory/design-contracts.md | none |
| FR-017 | SDD-C-004, SDD-C-017 | N/A | architecture.md § Bounded Contexts — Context D; § Risks and Tradeoffs — Risk 4 | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (extensibility tier dimension + sealed list) | reviewer checklist (default tier = extensible; sealed list matches FR-017(b) exactly) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| FR-018 | SDD-C-004 | N/A | architecture.md § Bounded Contexts — Context D | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (consumer-extension discovery convention) | reviewer checklist (namespaced subdirs + sealed-shadow rejection rule) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| FR-019 | SDD-C-004, SDD-C-017 | N/A | architecture.md § Non-Functional Architecture Notes — Compatibility posture | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (semver posture) | reviewer checklist (semver posture documented; per-item version range) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| FR-020 | SDD-C-004 | N/A | architecture.md § Bounded Contexts — Context D | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (upstream-candidate front-matter) | reviewer checklist (front-matter convention documented; no obligation language) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| NFR-SEC-001 | SDD-C-009 | N/A | architecture.md § Non-Functional Architecture Notes — Security | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 | reviewer checklist (exact-string equality, not regex) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 | none |
| NFR-OBS-001 | SDD-C-010 | N/A | architecture.md § Non-Functional Architecture Notes — Observability | docs/blueprint/autonomous-factory/design-contracts.md § Contract C7 | reviewer checklist (named schema with types + nullability) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C7 | none |
| NFR-REL-001 | SDD-C-016 | N/A | architecture.md § Risks and Tradeoffs — Risk 2 | docs/blueprint/autonomous-factory/design-contracts.md (Referenced by: lines per section) | reviewer checklist on downstream PRs | docs/blueprint/autonomous-factory/design-contracts.md | none |
| NFR-OPS-001 | SDD-C-011, SDD-C-012 | N/A | plan.md § Validation Strategy — Documentation checks | docs/blueprint/autonomous-factory/design-contracts.md and docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | make docs-build, make docs-smoke | both new files appear in built docs nav | none |
| NFR-OPS-002 | SDD-C-013, SDD-C-014 | N/A | architecture.md § Non-Functional Architecture Notes — STACKIT-managed and local-first preconditions for C8 surface | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 (preconditions of inclusion) | reviewer checklist (managed-first + local-first preconditions on every module wrapper) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | none |
| AC-001 | SDD-C-012, SDD-C-019 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md | reviewer checklist + make quality-sdd-check | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-002 | SDD-C-012 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md (Referenced by: lines) | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-003 | SDD-C-020 | N/A | spec.md § Acceptance Criteria | PR comment thread | PR comment thread | spec.md § Spec Readiness Gate | none |
| AC-004 | SDD-C-019 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md (### Open Decisions) | reviewer checklist | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-005 | SDD-C-003 | N/A | spec.md § Acceptance Criteria | docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | reviewer checklist | docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md | none |
| AC-006 | SDD-C-001, SDD-C-005 | N/A | spec.md § Acceptance Criteria | specs/2026-05-28-issue-339-factory-design-contracts/ | make quality-sdd-check | none | none |
| AC-007 | SDD-C-011 | N/A | spec.md § Acceptance Criteria | docs/blueprint/ | make docs-build, make docs-smoke | docs/blueprint/ | none |
| AC-008 | SDD-C-004, SDD-C-019 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md § Contract C5 / C6 / C7 (three required subsections) | reviewer checklist (subsection presence + schema-only consumer overlay) | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-009 | SDD-C-004, SDD-C-017 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | reviewer checklist (four categories + LiteLLM external + tier tags) | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-010 | SDD-C-004 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | reviewer checklist (every item carries extensibility tier; sealed list matches FR-017(b); default = extensible) | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-011 | SDD-C-004 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | reviewer checklist (discovery convention documented + 3 worked examples) | docs/blueprint/autonomous-factory/design-contracts.md | none |
| AC-012 | SDD-C-004, SDD-C-017 | N/A | spec.md § Acceptance Criteria | docs/blueprint/autonomous-factory/design-contracts.md § Contract C8 | reviewer checklist (semver posture + upstream-candidate convention documented; Referenced by: line cites #342) | docs/blueprint/autonomous-factory/design-contracts.md | none |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-OPS-002
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012

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
- Follow-up 1: Q-1 RESOLVED — Option A: `stackit-factory-bot` (PR #340 comment 2026-05-28). Carry-forward: reserve+verify the GitHub account during #334 Secrets Manager provisioning; update Contract C5 `### Blueprint instance` (under `### Open Decisions`) in the #334 PR. Does not affect consumer overlay schema.
- Follow-up 2: Q-2 RESOLVED — Option A: four flat sign-off team slugs `@sbonoc/factory-{product,architecture,security,operations}` + separate per-bounded-context teams (PR #340 comment 2026-05-28). Carry-forward: concrete team provisioning and the full bounded-context enumeration in #337; update Contract C6 `### Blueprint instance` (under `### Open Decisions`) in the #337 PR. Does not affect consumer overlay schema.
- Follow-up 3: Q-3 RESOLVED — Option A: STACKIT-managed Grafana via the existing observability module (PR #340 comment 2026-05-28). Carry-forward: concrete dashboard URLs and instrumentation wiring in #337; update Contract C7 `### Blueprint instance` (under `### Open Decisions`) in the #337 PR. Does not affect consumer overlay schema.
- Follow-up 4: Q-4 RESOLVED — Option A: LiteLLM access at `spec.factory_contract.litellm` under a new top-level `spec.factory_contract:` block in `blueprint/contract.yaml` (PR #340 comment 2026-05-28). Authored in T-001 Slice 1 (deliverable). Sealed under this work item.
- Follow-up 5: Q-5 RESOLVED — Phase 1 factory upgrade-process ticket filed as #342. Substituted into Contract C8 `Referenced by:` lines for FR-019 and FR-020. Spec open-clarification count decremented (5→4→0). Sealed under this work item; downstream work is owned by #342 itself.
