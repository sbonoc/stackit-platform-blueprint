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
- Requirement IDs covered: FR-001..FR-012, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001..AC-015 (assertion evidence populated in step07)
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
- Main risks: expert sprawl over time, convergence-merge dedup quality, and per-expert model assignment token cost.
  - Expert sprawl over time — mitigated by 8-expert ceiling pinned in ADR §3 (Future Work) and gated by distinct-push-back-triggers admission criterion.
  - Convergence-merge dedup quality — naive string-equality dedup may let semantic duplicates survive; mitigated by priority-order verdict aggregation (`block > revise > pass`); finding-text dedup is a follow-up owned by #361.
  - Per-expert model assignment token cost — mitigated by matrix-capped panel sizes and Haiku-for-low-stakes guidance in heterogeneity ADR amendment.
- Rollback strategy: Single-PR atomic merge. `git revert` of the merge commit is safe — the C7 `expert_verdicts[]` field is additive and optional, so existing consumers tolerate revert. PR #362 stays open until step06 of THIS ticket explicitly closes it; if THIS PR is closed without merge, the repo remains on the stage-persona model.

## Cherry-Pick Ledger
Procedural-contract sub-section per FR-006: salvage-of-record from PR #362.
Each row records the path to the salvaged runbook, the originating PR #362
commit-sha (or `(new on this branch)` when no #362 ancestor exists), and the
stripping-edit commit-sha on this branch where persona-coupling language was
removed and the `expert_verdicts`/`expert_slug` schema fragment added per
FR-006(a)/(b)/(c). The stripping-edit commits land in slice 3 of this PR.

| Runbook path | PR #362 commit-sha | Stripping-edit commit-sha on this branch |
|---|---|---|
| `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step02-resolve-questions/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step04-plan-slicer/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step06-document-sync/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-sdd-traceability-keeper/SKILL.md` | (new on this branch) | (no persona-coupling; no stripping needed) |
| `.agents/skills/blueprint-agent-handoff/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-agent-secret-scan/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-agent-stop-cleanup/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-human-review-prep/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-pr-review-respond/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-spec-review-prep/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-spec-revision-handoff/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-ticket-decompose-light/SKILL.md` | (new on this branch) | be866a22 |
| `.agents/skills/blueprint-ticket-triage-size/SKILL.md` | (new on this branch) | be866a22 |

Provenance note: The 18 SKILL.md files were authored fresh on this branch
during prior step01/step02/step04 spec-scaffolding work (no PR #362 ancestor
commits exist on this branch's history). PR #362 remains the upstream
reference for any reader comparing the stage-persona and expert-persona
runbook layouts; this PR's slice 3 commit is the authoritative stripped form.

## Cross-Ticket Amendments
Populated in step06. URLs captured here are validated by AC-005 (`gh api` HTTP-200 per URL).

| Ticket | Action | Comment URL |
|---|---|---|
| #333 | Epic body retitle + scope amendment to factory-execution-layer framing | https://github.com/sbonoc/stackit-platform-blueprint/issues/333#issuecomment-4609429813 |
| #361 | Dispatch table contract update; empty-findings sentinel; per-expert C7 audit | https://github.com/sbonoc/stackit-platform-blueprint/issues/361#issuecomment-4609432549 |
| #335 | Per-expert LiteLLM routing key; capacity-sizing note | https://github.com/sbonoc/stackit-platform-blueprint/issues/335#issuecomment-4609432659 |
| #336 | FR-008 reformulated as panel-disjointness rule | https://github.com/sbonoc/stackit-platform-blueprint/issues/336#issuecomment-4609432786 |
| #342 | Per-artifact versioning extends to expert-persona files | https://github.com/sbonoc/stackit-platform-blueprint/issues/342#issuecomment-4609435187 |
| #343 | Phase 1 ingestion schema accounts for additive `expert_verdicts[]` | https://github.com/sbonoc/stackit-platform-blueprint/issues/343#issuecomment-4609435346 |
| #332 | Epic body framing update | https://github.com/sbonoc/stackit-platform-blueprint/issues/332#issuecomment-4609435497 |
| #360 | Close as superseded with reference to #364 + cherry-pick list | https://github.com/sbonoc/stackit-platform-blueprint/issues/360#issuecomment-4609437220 |
| PR #362 | Close as superseded with reference to this PR + cherry-pick list | https://github.com/sbonoc/stackit-platform-blueprint/pull/362#issuecomment-4609502873 |

## Deferred Proposals
- Proposal 1 (not implemented): Optional `make expert-review` for solo-operator local SDD sessions — held until user demand emerges; separate ticket if pursued.
- Proposal 2 (not implemented): Per-expert prompt-cache discipline — surfaces during #361 implementation if cache contamination shows up in observability.
- Proposal 3 (not implemented): Expert-verdict-to-skill-output feedback loop — held until parallel-then-merge proves insufficient in practice; #361 follow-up.
- Proposal 4 (not implemented): Embedding-based finding-text dedup — escalation path if naive string-equality dedup proves insufficient; #361 follow-up.
- Proposal 5 (not implemented): Compliance / data-protection 9th expert — held; ADR §3 caps at 8 and requires distinct push-back triggers for any future addition.
- Proposal 6 (filed as **#368**): First-run cost telemetry + step02 routing-quality fixture. Surfaced during PR #365 review: ~36 expert-step instantiations per work item with Opus-heavy step01/step08 fan-outs is materially more expensive than the stage-persona model; and the substring-match routing algorithm (ADR §4.2) may not match real step02 question text. #368 lands the per-expert token / cost telemetry on C7 events and a ≥25-row routing-quality fixture under #361's scope so the embedding-vs-substring decision can be made against evidence rather than speculation. Blocked by #361.
