# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-004, SDD-C-005 | n/a | ADR § Decision (implementer + reviewer roster); architecture.md Context A | `.agents/personas/po-analyst.md`, `.agents/personas/architect.md`, `.agents/personas/tech-lead.md`, `.agents/personas/implementer.md`, `.agents/personas/devsecops-qa.md`, `.agents/personas/doc-keeper.md`, `.agents/personas/security-reviewer.md`, `.agents/personas/architecture-reviewer.md`, `.agents/personas/contract-reviewer.md`, `.agents/personas/test-coverage-reviewer.md` | T-101 | ADR-issue-360-factory-personas-skills-roster.md; design-contracts.md § Contract C8 § Category (c) | n/a |
| FR-002 | SDD-C-004, SDD-C-005 | n/a | ADR § Decision (skill table); architecture.md Context B | `.agents/skills/blueprint-ticket-triage-size/SKILL.md`, `.agents/skills/blueprint-ticket-decompose-light/SKILL.md`, `.agents/skills/blueprint-agent-secret-scan/SKILL.md`, `.agents/skills/blueprint-agent-handoff/SKILL.md`, `.agents/skills/blueprint-spec-revision-handoff/SKILL.md`, `.agents/skills/blueprint-spec-review-prep/SKILL.md`, `.agents/skills/blueprint-human-review-prep/SKILL.md`, `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md`, `.agents/skills/blueprint-pr-review-respond/SKILL.md`, `.agents/skills/blueprint-agent-stop-cleanup/SKILL.md` | T-101 | design-contracts.md § Contract C8 § Category (c) | n/a |
| FR-003 | SDD-C-004 | n/a | architecture.md Context B; references C7 emission mechanism rule | each new `.agents/skills/*/SKILL.md` | T-102 | ADR-issue-337-c7-emission-mechanism.md | n/a |
| FR-004 | SDD-C-005, SDD-C-011 | n/a | architecture.md Context C | `docs/blueprint/autonomous-factory/design-contracts.md` | T-102 | design-contracts.md § C8 § Category (c) | n/a |
| FR-005 | SDD-C-005 | n/a | ADR § Consequences | each new persona `.md` + each new `SKILL.md` (front-matter) | T-102 | design-contracts.md § Extensibility tier dimension | n/a |
| FR-006 | SDD-C-005 | n/a | architecture.md Integration edges (epic #342 dependency) | each new persona `.md` + each new `SKILL.md` (front-matter `blueprint-version`) | T-102 | design-contracts.md § Upstream-candidate front-matter convention | n/a |
| FR-007 | SDD-C-005 | n/a | architecture.md Integration edges | persona template documentation + new-skill template documentation | T-102 | design-contracts.md § Upstream-candidate front-matter convention | n/a |
| FR-008 | SDD-C-004, SDD-C-019 | n/a | plan.md Slice 1+2 | each of the 20 new files | T-103 | n/a | n/a |
| FR-009 | SDD-C-004, SDD-C-009 | n/a | ADR § Decision (implementer half row 5) | `.agents/personas/devsecops-qa.md` § Definition of Done (DoD) | T-104 | n/a | hardening_review.md (T-205 evidence) |
| FR-010 | SDD-C-004 | n/a | ADR § Decision (implementer half row 3); references Phase 0 light-decomposition ADR | `.agents/personas/tech-lead.md` § Definition of Done (DoD) | T-104 | ADR-issue-337-light-decomposition-policy.md | n/a |
| FR-011 | SDD-C-007 | n/a | architecture.md Context A; ADR § Decision | each persona file's `## Skills Invoked` block | T-105 | n/a | n/a |
| FR-012 | SDD-C-004, SDD-C-009 | n/a | parent ADR clause 4; FR-012 | each persona file | T-105 | ADR-issue-337-persona-skill-contract.md (clause 4) | n/a |
| FR-013 | SDD-C-004 | n/a | ADR § Decision (reviewer table); architecture.md Context A | the 4 reviewer persona files | T-106 | n/a | n/a |
| FR-014 | SDD-C-004 | n/a | ADR § Decision (reviewer half — architecture-reviewer note) | `.agents/personas/architecture-reviewer.md` § Cross-Context Impact Reporting | T-106 | n/a | n/a |
| FR-015 | SDD-C-004 | n/a | architecture.md Integration edges (#338 dependency) | `.agents/skills/blueprint-ticket-triage-size/SKILL.md` | T-102 | ADR-issue-337-triage-size-threshold.md | n/a |
| FR-016 | SDD-C-007 | n/a | parent ADR clause 3 | each new `SKILL.md` | T-107 | ADR-issue-337-persona-skill-contract.md (clause 3) | n/a |
| FR-017 | SDD-C-004 | n/a | architecture.md Context A; persona template contract from #360 issue body | each of the 10 persona files | T-108 | ADR-issue-360-factory-personas-skills-roster.md | n/a |
| FR-018 | SDD-C-004 | n/a | reviewer-half table in ADR § Decision | the 4 reviewer persona files | T-106 (extended) | ADR-issue-337-reviewer-model-heterogeneity.md | n/a |
| NFR-SEC-001 | SDD-C-009 | n/a | architecture.md NFA Security | the 20 new files | T-103 | n/a | `blueprint-agent-secret-scan` SKILL.md (runtime layer for future executions) |
| NFR-OBS-001 | SDD-C-010 | n/a | architecture.md NFA Observability | each persona file (SDD Cycle Stakes); each new SKILL.md (## Required Output Schema or adjacent section) | T-101 (presence) | n/a | C7 phase enum (sealed under the design-contracts sealed list) |
| NFR-REL-001 | SDD-C-007 | n/a | architecture.md NFA Reliability | each persona file (`## Skills Invoked` ordering) | T-105 | n/a | rollback = git revert |
| NFR-OPS-001 | SDD-C-010 | n/a | architecture.md NFA Reliability | each persona file (`## Activation Triggers`, handoff reference to `blueprint-agent-stop-cleanup`) | T-101 (presence) | n/a | `blueprint-agent-stop-cleanup` SKILL.md |
| NFR-A11Y-001 | n/a | n/a | n/a — no UI | n/a | T-A01 (declared N/A) | n/a | n/a |
| AC-001 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_roster_exists.py | tests/blueprint/personas_skills/test_roster_exists.py | T-101 | n/a | n/a |
| AC-002 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_roster_exists.py | tests/blueprint/personas_skills/test_roster_exists.py | T-101 | n/a | n/a |
| AC-003 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py | tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py | T-102 | n/a | n/a |
| AC-004 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py | tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py | T-102 | design-contracts.md § C8 § Category (c) | n/a |
| AC-005 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py | tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py | T-102 | n/a | n/a |
| AC-006 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_no_placeholders_no_secrets.py | tests/blueprint/personas_skills/test_no_placeholders_no_secrets.py | T-103 | n/a | n/a |
| AC-007 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_dod_phrases.py | tests/blueprint/personas_skills/test_dod_phrases.py | T-104 | n/a | n/a |
| AC-008 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_dod_phrases.py | tests/blueprint/personas_skills/test_dod_phrases.py | T-104 | n/a | n/a |
| AC-009 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_persona_invocation_safety.py | tests/blueprint/personas_skills/test_persona_invocation_safety.py | T-105 | n/a | n/a |
| AC-010 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_persona_invocation_safety.py | tests/blueprint/personas_skills/test_persona_invocation_safety.py | T-105 | n/a | n/a |
| AC-011 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_reviewer_personas.py | tests/blueprint/personas_skills/test_reviewer_personas.py | T-106 | n/a | n/a |
| AC-012 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_reviewer_personas.py | tests/blueprint/personas_skills/test_reviewer_personas.py | T-106 | n/a | n/a |
| AC-013 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_no_skill_invokes_skill.py | tests/blueprint/personas_skills/test_no_skill_invokes_skill.py | T-107 | n/a | n/a |
| AC-014 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_persona_template_structure.py | tests/blueprint/personas_skills/test_persona_template_structure.py | T-108 | ADR-issue-360-factory-personas-skills-roster.md | n/a |
| AC-015 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_reviewer_personas.py (extended) | tests/blueprint/personas_skills/test_reviewer_personas.py (extended) | T-106 (extended) | ADR-issue-337-reviewer-model-heterogeneity.md | n/a |
| FR-019 | SDD-C-004 | n/a | architecture.md Integration edges (CLAUDE.md edit) | `CLAUDE.md` (Skills table row addition) | T-109 | spec.md § Make/CLI contract; spec.md § Open Questions OQ-1 resolution | n/a |
| FR-020 | SDD-C-004, SDD-C-005 | n/a | architecture.md Context B (extended to existing 8 skill files) | the 8 existing skill `SKILL.md` files listed in FR-020 | T-110 | spec.md § Docs contract; spec.md § Open Questions OQ-2 resolution | n/a |
| AC-016 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_claude_md_slash_command_row.py | tests/blueprint/personas_skills/test_claude_md_slash_command_row.py | T-109 | n/a | n/a |
| AC-017 | SDD-C-012 | n/a | tests/blueprint/personas_skills/test_existing_skills_output_schema_backfill.py | tests/blueprint/personas_skills/test_existing_skills_output_schema_backfill.py | T-110 | n/a | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017

## Validation Summary
- Required bundles executed (2026-06-02):
  - `make quality-sdd-check` — PASS (`[quality-sdd-check] validated SDD assets, readiness gates, and language policy`)
  - `make quality-hardening-review` — PASS (`status=success`)
  - `uv run python3 -m pytest tests/blueprint/personas_skills/` — 589 passed (0.36s)
  - `uv run python3 -m pytest tests/blueprint/` — 1769 passed in 141.90s (template-mirror drift fixed in commit e85db47d via `scripts/lib/docs/sync_blueprint_template_docs.py`)
- Result summary: all gates green; no outstanding failures
- Documentation validation:
  - `make docs-build` — PASS (`docs build complete`)
  - `make docs-smoke` — PASS (`status=success`)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None. OQ-1 (CLAUDE.md step08 slash-command row) resolved by T-006/T-109 in this PR. OQ-2 (retroactive Required Output Schema backfill) resolved by T-007/T-110 in this PR.
