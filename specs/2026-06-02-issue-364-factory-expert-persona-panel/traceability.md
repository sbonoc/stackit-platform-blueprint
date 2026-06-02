# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | N/A | ADR §3 (persona file shape) | `.agents/personas/<slug>/PERSONA.md` (8 files) | `pr_context.md` AC-001 grep block | ADR-issue-364 §3 | N/A |
| FR-002 | SDD-C-005, SDD-C-007 | N/A | ADR §4 (matrix anchor) | `docs/blueprint/autonomous-factory/design-contracts.md` § C3 | `pr_context.md` AC-003 grep block | design-contracts § C3 + ADR-issue-364 §4 | N/A |
| FR-003 | SDD-C-005 | N/A | ADR §5 (convergence) | ADR-issue-364 §5 | `pr_context.md` AC-002 substring block | ADR-issue-364 §5 | N/A |
| FR-004 | SDD-C-005, SDD-C-010 | N/A | ADR §6 (verdict schema) | ADR-issue-364 §6 (embedded JSON Schema) | `pr_context.md` AC-002 + schema-validity script | ADR-issue-364 §6 | C7 `outcome.details.expert_verdicts[]` post-merge |
| FR-005 | SDD-C-007 | N/A | ADR §7 (supersession + amendments) | ADR-issue-360 (Status flip); ADR-issue-337-persona-skill-contract (Amended-by); ADR-issue-337-c7-emission-mechanism (Amended-by); ADR-issue-337-reviewer-model-heterogeneity (Amended-by) | `pr_context.md` AC-002 substring block | ADR file diffs in this PR | N/A |
| FR-006 | SDD-C-005 | N/A | ADR §8 (skill panel-input shape) | `.agents/skills/blueprint-*/SKILL.md` (10 files) | `pr_context.md` AC-004 grep block | ADR-issue-364 §8 + skill diffs in this PR | N/A |
| FR-007 | SDD-C-010, SDD-C-007 | N/A | ADR §9 (C7 additive field) | ADR-issue-337-c7-emission-mechanism amendment | `pr_context.md` AC-002 substring block | ADR amendment diff | C7 events post-merge carry optional field |
| FR-008 | SDD-C-007, SDD-C-018 | N/A | Plan slice 6 (fan-out checklist) | GH comments on #333, #361, #335, #336, #342, #343, #332; close-with-reference #360 + PR #362 | `pr_context.md` AC-005 URL list + `gh api` HTTP-200 each | `pr_context.md` Cross-Ticket Amendments section | N/A |
| FR-009 | SDD-C-005, SDD-C-007 | N/A | spec §FR-009 (C8 (c) persona-list rows) | `docs/blueprint/autonomous-factory/design-contracts.md` § C8 (c) | `pr_context.md` AC-008 grep block | design-contracts § C8 (c) diff | N/A |
| FR-010 | SDD-C-005, SDD-C-007, SDD-C-010 | N/A | spec §FR-010 (C7 persona-field semantics) | `docs/blueprint/autonomous-factory/design-contracts.md` § C7 | `pr_context.md` AC-009 grep block | design-contracts § C7 diff + ADR-issue-337-c7-emission-mechanism amendment | C7 events post-merge carry skill-basename `persona` field |
| NFR-SEC-001 | SDD-C-009, SDD-C-014 | N/A | ADR §10 (SoD posture) | ADR-issue-364 §10 (bot-authored verdicts; two-gate invariant) | `pr_context.md` AC-002 substring block | ADR-issue-364 §10 + AGENTS.md sign-off policy unchanged | Sign-off log post-merge |
| NFR-OBS-001 | SDD-C-010 | N/A | ADR §9 (C7 invariants preserved) | ADR-issue-337-c7-emission-mechanism amendment (additive only) | `pr_context.md` AC-002 substring block | ADR amendment diff | C7 event log post-merge |
| NFR-REL-001 | SDD-C-008, SDD-C-018 | N/A | Plan §Rollback | Single PR atomic merge | `pr_context.md` Rollback section | plan.md Change Strategy | Revert verified by re-run of quality bundle on revert commit (if invoked) |
| NFR-OPS-001 | SDD-C-006, SDD-C-008 | N/A | Plan §Operational Readiness | Bootstrap template mirror resync script | `pr_context.md` AC-006 quality-gate output | plan.md Validation Strategy | Quality-hooks logs |
| NFR-A11Y-001 | SDD-C-019 | N/A — no UI | spec.md NFR-A11Y-001 declares N/A | N/A | N/A | spec.md inline | N/A |
| AC-001 | SDD-C-012 | N/A | spec.md AC-001 | shell + grep | `pr_context.md` AC-001 block | `pr_context.md` | N/A |
| AC-002 | SDD-C-012 | N/A | spec.md AC-002 | shell + grep | `pr_context.md` AC-002 block | `pr_context.md` | N/A |
| AC-003 | SDD-C-012 | N/A | spec.md AC-003 | shell + grep | `pr_context.md` AC-003 block | `pr_context.md` | N/A |
| AC-004 | SDD-C-012 | N/A | spec.md AC-004 | shell + grep | `pr_context.md` AC-004 block | `pr_context.md` | N/A |
| AC-005 | SDD-C-012, SDD-C-018 | N/A | spec.md AC-005 | `gh api` HTTP-200 per URL | `pr_context.md` AC-005 block | `pr_context.md` Cross-Ticket Amendments | GH issue/PR comment URLs |
| AC-006 | SDD-C-012, SDD-C-006 | N/A | spec.md AC-006 | make quality-* | `pr_context.md` AC-006 block + CI logs | `pr_context.md` | Quality-hooks logs |
| AC-007 | SDD-C-012 | N/A | spec.md AC-007 | shell + grep + skip-if-absent | `pr_context.md` AC-007 block | `pr_context.md` | MEMORY.md updated in user memory store |
| AC-008 | SDD-C-012, SDD-C-005 | N/A | spec.md AC-008 | shell + grep | `pr_context.md` AC-008 block | `pr_context.md` | design-contracts § C8 (c) diff |
| AC-009 | SDD-C-012, SDD-C-005 | N/A | spec.md AC-009 | shell + grep | `pr_context.md` AC-009 block | `pr_context.md` | design-contracts § C7 diff |
| AC-010 | SDD-C-012, SDD-C-006 | N/A | spec.md AC-010 | `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py --check` or `diff -u` | `pr_context.md` AC-010 block | `pr_context.md` | mirror sync verified at PR-ready |
| AC-011 | SDD-C-012, SDD-C-005 | N/A | spec.md AC-011 | shell + grep | `pr_context.md` AC-011 block | `pr_context.md` | step08 SKILL.md `## Required Output Schema` diff |

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
  - FR-008
  - FR-009
  - FR-010
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - NFR-A11Y-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007
  - AC-008
  - AC-009
  - AC-010
  - AC-011

## Validation Summary
- Required bundles executed: `make quality-sdd-check`, `make quality-hooks-fast`, `make quality-hooks-slow`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review` (planned for step07; not yet executed at intake).
- Result summary: pending — populated at step07.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Convergence finding-text dedup quality — owned by #361 orchestrator implementation; if naive string-equality dedup proves insufficient, escalate to embedding-based dedup.
- Follow-up 2: Per-expert prompt-cache discipline — flagged in ADR §11 (Future Work); surfaces during #361 implementation if cache contamination shows up in observability.
- Follow-up 3: Expert-verdict-to-skill-output feedback loop — held until parallel-then-merge proves insufficient in practice; #361 follow-up.
- Follow-up 4: Optional `make expert-review` for solo-operator local SDD sessions — held until user demand emerges; separate ticket if pursued.
