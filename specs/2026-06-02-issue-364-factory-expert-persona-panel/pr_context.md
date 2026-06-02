# PR Context

> **Note:** This file is populated incrementally across the SDD lifecycle. At
> intake (step01) only the Summary, scope, and key reviewer files are filled.
> Requirement coverage, validation evidence, and Cross-Ticket Amendments are
> completed at step06/step07.

## Summary
- Work item: 2026-06-02-issue-364-factory-expert-persona-panel
- Objective: Replace the stage-persona model (PR #362, issue #360) with a three-layer factory execution architecture — SDD step (sealed) / skill (verb) / expert persona (lens) — and ship 8 standing expert personas, a single-sourced SDD-step × expert dispatch matrix, an always-respond verdict contract, and the additive C7 `expert_verdicts[]` field.
- Scope boundaries: This PR ships specs, ADR, 8 persona files, skill runbook edits, design-contracts § C3 reshape, AGENTS.md persona section update, MEMORY.md updates, and cross-ticket GH amendments. It does NOT ship runtime orchestrator code (#361), LiteLLM routing changes (#335), webhook FR-008 implementation (#336), or upgrade-process versioning extension (#342) — those land in their respective tickets via comment amendments posted in step06.

## Requirement Coverage
- Requirement IDs covered: FR-001..FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001..AC-007 (assertion evidence populated in step07)
- Contract surfaces changed:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C3 (matrix reshape)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` (additive `expert_verdicts[]` clause)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` (Amended-by line)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` (Amended-by line)
  - `docs/blueprint/architecture/decisions/ADR-issue-360-factory-personas-skills-roster.md` (Status: superseded)
  - `AGENTS.md` § persona section (retitle + rewrite)
  - `.agents/personas/<slug>/PERSONA.md` × 8 (new files)
  - `.agents/skills/blueprint-*/SKILL.md` × 10 (re-homed with persona-coupling stripped; `blueprint-sdd-step08-agent-pr-review` reshaped for panel-input)

## Key Reviewer Files
- Primary files to review first:
  - `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` (full architectural shape)
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C3 (dispatch matrix)
  - `.agents/personas/data-privacy/PERSONA.md` (new expert, distinguishing posture vs security-paranoid)
  - `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md` (panel-input reshape)
- High-risk files:
  - `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` (additive — must preserve eleven required fields + sealed three-emitter rule + event_id derivation)
  - `AGENTS.md` (persona section — must not break SoD posture or two-human-gates invariant)

## Validation Evidence
- Required commands executed: populated at step07
- Result summary: populated at step07
- Artifact references: see `evidence_manifest.json`

## Risk and Rollback
- Main risks:
  - Expert sprawl over time — mitigated by 8-expert ceiling pinned in ADR §3 (Future Work) and gated by distinct-push-back-triggers admission criterion.
  - Convergence-merge dedup quality — naive string-equality dedup may let semantic duplicates survive; mitigated by priority-order verdict aggregation (`block > revise > pass`); finding-text dedup is a follow-up owned by #361.
  - Per-expert model assignment token cost — mitigated by matrix-capped panel sizes and Haiku-for-low-stakes guidance in heterogeneity ADR amendment.
- Rollback strategy: Single-PR atomic merge. `git revert` of the merge commit is safe — the C7 `expert_verdicts[]` field is additive and optional, so existing consumers tolerate revert. PR #362 stays open until step06 of THIS ticket explicitly closes it; if THIS PR is closed without merge, the repo remains on the stage-persona model.

## Cross-Ticket Amendments
Populated in step06. URLs captured here are validated by AC-005 (`gh api` HTTP-200 per URL).

| Ticket | Action | Comment URL |
|---|---|---|
| #333 | Epic body retitle + scope amendment to factory-execution-layer framing | pending step06 |
| #361 | Dispatch table contract update; empty-findings sentinel; per-expert C7 audit | pending step06 |
| #335 | Per-expert LiteLLM routing key; capacity-sizing note | pending step06 |
| #336 | FR-008 reformulated as panel-disjointness rule | pending step06 |
| #342 | Per-artifact versioning extends to expert-persona files | pending step06 |
| #343 | Phase 1 ingestion schema accounts for additive `expert_verdicts[]` | pending step06 |
| #332 | Epic body framing update | pending step06 |
| #360 | Close as superseded with reference to #364 + cherry-pick list | pending step06 |
| PR #362 | Close as superseded with reference to this PR + cherry-pick list | pending step06 |

## Deferred Proposals
- Proposal 1 (not implemented): Optional `make expert-review` for solo-operator local SDD sessions — held until user demand emerges; separate ticket if pursued.
- Proposal 2 (not implemented): Per-expert prompt-cache discipline — surfaces during #361 implementation if cache contamination shows up in observability.
- Proposal 3 (not implemented): Expert-verdict-to-skill-output feedback loop — held until parallel-then-merge proves insufficient in practice; #361 follow-up.
- Proposal 4 (not implemented): Embedding-based finding-text dedup — escalation path if naive string-equality dedup proves insufficient; #361 follow-up.
- Proposal 5 (not implemented): Compliance / data-protection 9th expert — held; ADR §3 caps at 8 and requires distinct push-back triggers for any future addition.
