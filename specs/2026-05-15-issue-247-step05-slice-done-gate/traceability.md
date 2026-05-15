# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-011 | — | Guardrail #13 — API response field coverage | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` § Guardrails | AC-001 confirmed by human review of SKILL.md content | SKILL.md is self-documenting governance | n/a |
| FR-002 | SDD-C-005, SDD-C-011 | — | Guardrail #14 — Vue component branch enumeration | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` § Guardrails | AC-002 confirmed by human review of SKILL.md content | SKILL.md is self-documenting governance | n/a |
| FR-003 | SDD-C-005, SDD-C-011 | — | Guardrail #15 — Pact consumer + provider | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` § Guardrails | AC-003 confirmed by human review of SKILL.md content | SKILL.md is self-documenting governance | n/a |
| FR-004 | SDD-C-005, SDD-C-011 | — | Minimum validation bundle table update | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` § After All Slices Complete | AC-004 confirmed by human review of SKILL.md table | SKILL.md is self-documenting governance | n/a |
| FR-005 | SDD-C-005, SDD-C-011 | — | Numbered workflow step "3. Local smoke gate" | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` § Workflow | AC-005 confirmed by human review of SKILL.md workflow | SKILL.md is self-documenting governance | n/a |
| FR-006 | SDD-C-005, SDD-C-011 | — | Checklist file (derived artifact — contract compliance gap) | `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` | AC-006 confirmed by file existence + consistency with SKILL.md | checklist is summary of SKILL.md; SKILL.md is normative | n/a |
| FR-007 | SDD-C-005, SDD-C-011 | — | AGENTS.md § Cross-Cutting Guardrails — field-coverage gate addition | `AGENTS.md` § Cross-Cutting Guardrails | AC-008 confirmed by human review of AGENTS.md section | AGENTS.md is self-documenting governance | n/a |
| FR-008 | SDD-C-005, SDD-C-011 | — | AGENTS.md § Testing and Quality Ratios — per-SFC branch coverage rule | `AGENTS.md` § Testing and Quality Ratios | AC-009 confirmed by human review of AGENTS.md section | AGENTS.md is self-documenting governance | n/a |
| FR-009 | SDD-C-005, SDD-C-011 | — | AGENTS.md § Contract Testing Standards — same-repo provider timing | `AGENTS.md` § Contract Testing Standards | AC-010 confirmed by human review of AGENTS.md section | AGENTS.md is self-documenting governance | n/a |
| FR-010 | SDD-C-005, SDD-C-011 | — | AGENTS.md § Minimum Validation Bundles — HTTP-scope entries | `AGENTS.md` § Minimum Validation Bundles | AC-011 confirmed by human review of AGENTS.md section | AGENTS.md is self-documenting governance | n/a |
| NFR-MAINT-001 | SDD-C-004 | — | Guardrails additive-only constraint | SKILL.md guardrail section (no removal of #1–#12) | PR diff review confirms no deletions in guardrail list | n/a | n/a |
| NFR-COMPAT-001 | SDD-C-004 | — | Additive-only change policy | SKILL.md diff — additions only | PR diff review confirms additive-only | n/a | n/a |
| NFR-A11Y-001 | — | — | N/A — no UI changes | — | — | — | — |
| AC-001 | SDD-C-012 | — | Guardrail #13 text | SKILL.md § Guardrails #13 | Human review confirms exact text matches spec | — | n/a |
| AC-002 | SDD-C-012 | — | Guardrail #14 text | SKILL.md § Guardrails #14 | Human review confirms exact text matches spec | — | n/a |
| AC-003 | SDD-C-012 | — | Guardrail #15 text | SKILL.md § Guardrails #15 | Human review confirms exact text matches spec | — | n/a |
| AC-004 | SDD-C-012 | — | Validation bundle table rows | SKILL.md § After All Slices Complete | Human review confirms two REQUIRED HTTP rows present | — | n/a |
| AC-005 | SDD-C-012 | — | Numbered smoke step | SKILL.md § Workflow step 3 | Human review confirms step 3 exists with non-optional language | — | n/a |
| AC-006 | SDD-C-012 | — | Checklist file on disk (contract compliance) | `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` | File existence confirmed; content consistency with SKILL.md confirmed by review | — | n/a |
| AC-007 | SDD-C-012 | — | Quality gate | `make quality-hooks-run` | Output: clean exit 0 | — | n/a |
| AC-008 | SDD-C-012 | — | AGENTS.md § Cross-Cutting Guardrails — field-coverage addition | `AGENTS.md` | Human review confirms text matches FR-007 | — | n/a |
| AC-009 | SDD-C-012 | — | AGENTS.md § Testing and Quality Ratios — SFC branch coverage | `AGENTS.md` | Human review confirms text matches FR-008 | — | n/a |
| AC-010 | SDD-C-012 | — | AGENTS.md § Contract Testing Standards — same-repo provider timing | `AGENTS.md` | Human review confirms text matches FR-009 | — | n/a |
| AC-011 | SDD-C-012 | — | AGENTS.md § Minimum Validation Bundles — HTTP-scope rows | `AGENTS.md` | Human review confirms two HTTP entries present | — | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010
  - NFR-MAINT-001, NFR-COMPAT-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011

## Validation Summary
- Required bundles executed: pending (governance/docs bundle — `make quality-hooks-run` · `make infra-validate`)
- Result summary: pending
- Documentation validation:
  - `make docs-build`: pending
  - `make docs-smoke`: pending

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Option B (automated SKILL.md content scanner) parked as a future proposal on-scope: skills — surfaces when next skills-scope work item is in flight.
