# Architecture

## Context
- Work item: 2026-06-02-issue-364-factory-expert-persona-panel
- Owner: bonos (solo operator)
- Date: 2026-06-02

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2 (informational — this work item ships specs, ADRs, persona files, and docs, no runtime code)
- Frontend stack profile: vue_router_pinia_onyx (informational — no UI work)
- Test automation profile: pytest_vitest_playwright_pact (informational — verification is structural: grep + file-existence + ADR-text assertions, not unit/integration tests against runtime code)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: The current factory roster authored under #360 / PR #362 conflates two layers — procedural skill (verb) and standing expert persona (lens) — into a single artifact shape ("stage persona"). The result is persona files that read like skill runbooks (Skills Invoked sequences, Activation Triggers, Definition of Done checklists) and do not earn their keep over the skill layer. The factory needs the personas layer to add judgment and quality lensing, not to duplicate the verbs the skills layer already owns. Without this pivot, every future SDD step's persona file recreates the same conflation, and the orchestrator (#361) has to bind to stage-personas rather than to a clean dispatch table.
- Scope boundaries: This work item delivers the **spec, ADR, persona files, skill runbook edits, design-contracts § C3 reshape, AGENTS.md persona section update, MEMORY.md updates, and cross-ticket GH amendments**. It atomically replaces the stage-persona model on the repo. It does NOT ship runtime orchestrator code (#361), LiteLLM routing changes (#335), webhook FR-008 reformulation implementation (#336), or upgrade-process versioning extension (#342) — those land in their respective tickets, each amended via comment from step06 of this ticket.
- Out of scope: Expert-panel consultation in human-driven local SDD sessions (`local-cli` emitter from #347); brain ingestion schema update for `expert_verdicts[]` (Epic #343); a compliance/data-protection expert as 8th panel member; per-expert prompt-cache discipline implementation; expert-verdict-to-skill-output feedback loop.

## Bounded Contexts and Responsibilities

The factory execution layer is the single bounded context affected. Within it, the architectural shift moves the personas sub-layer from being a 1:1 stage-owner roster to being a cross-cutting standing-expert panel.

- **SDD step layer** (sealed): Defines the lifecycle phases (intake → spec → plan → implement → review → package → agent-pr-review) and the C7 emission boundary. Unchanged by this ticket. Sealed; changes require a separate ADR.
- **Skill layer** (extensible): Owns procedural verbs invoked at each step. Each skill produces a structured output to its `## Required Output Schema`. The 10 skills from #360 are re-homed here with persona-coupling language stripped. The `blueprint-sdd-step08-agent-pr-review` skill is reshaped to accept a panel-input parameter and produce a per-expert verdict array.
- **Expert persona layer** (extensible — new shape): Owns judgment and quality lensing. 8 standing experts (Product Pragmatist, Boundary Hawk, Security Paranoid, Data Privacy, Test-Quality Sceptic, Operability/SRE, Documentation Discipline, Performance/Cost-Aware), each consulted at the SDD steps where their lens matters per the matrix in design-contracts § C3. Data Privacy is distinguished from Security Paranoid by its focus on data-as-liability (minimization, residency, lawful basis, retention, subject rights) rather than threat-actor / attack-surface posture; both are first-class panel members from day one given the factory's EU-sovereign / GDPR / C5 / ISO 27001 / SOC 2 stance baked into the existing #337 ADRs.
- **Orchestrator** (out of scope here — lives in #361): Binds steps to skills and experts via a single dispatch table `step → {skill, expert_panel, convergence_mode, model_per_expert}`. This ticket only delivers the spec amendment for #361; the runtime code ships under #361 itself.

## High-Level Component Design
- Domain layer: Not applicable — no runtime domain code in this ticket. The domain model the ticket *describes* is the expert-persona panel: a `Panel` is an ordered list of `Expert` references with one `lead`; an `Expert` is a `PERSONA.md` file plus a runtime model assignment; a `Verdict` is `{ verdict: "pass" | "revise" | "block", findings: Array<Finding> }` always returned (empty `findings: []` when silent).
- Application layer: Not applicable in this ticket. The dispatch application logic — fan-out to experts in parallel, merge findings by dedup-and-priority, surface block conflicts to humans — is specified here for #361 but implemented there.
- Infrastructure adapters: Not applicable in this ticket. Per-expert LiteLLM routing keys are described here and implemented under #335.
- Presentation/API/workflow boundaries: Not applicable — no UI, no API surface, no workflows added.

## Integration and Dependency Edges
- Upstream dependencies: This ticket's outputs are consumed by:
  - **#361 (orchestrator)** — reads the dispatch contract (panel shape, convergence modes, empty-findings sentinel) from this ticket's ADR; spec amendment comment lands during step06.
  - **#335 (OpenHands + LiteLLM)** — reads the per-expert routing requirement and capacity-sizing note from this ticket's ADR; comment lands during step06.
  - **#336 (webhooks)** — reads the FR-008 panel-disjointness reformulation from this ticket's ADR; comment lands during step06.
  - **#342 (upgrade process)** — reads the per-artifact versioning expansion (expert-persona files as a new artifact category) from this ticket's ADR; comment lands during step06.
  - **#343 (Central Brain, Draft)** — reads the additive C7 `expert_verdicts[]` field shape from this ticket's ADR; comment lands during step06 so the brain's Phase 1 ingestion schema accounts for it when promoted from Draft.
- Downstream dependencies: This ticket is blocked by:
  - **Nothing structurally** — all referenced ADRs are merged, no in-flight code depends on PR #362.
  - **Soft sequencing** — PR #362 is closed (not merged) at step06 of this ticket; nothing else depends on PR #362.
- Data/API/event contracts touched: One additive event-contract change — C7 `outcome.details.expert_verdicts: Array<{ expert_slug: string, verdict: enum, findings_count: integer }>`, authored as an amendment to `ADR-issue-337-c7-emission-mechanism.md`. Existing C7 emitters and consumers remain valid (additive optional field).

## Non-Functional Architecture Notes
- Security: Separation-of-Duties posture preserved. Expert verdicts are bot-authored and MUST NOT count toward the four canonical human sign-off phrases. The two human gates (spec sign-off, PR merge) remain the sole sources of human approval. The `agent-stop` GitHub label semantics from `ADR-issue-337-trigger-authorization-model.md` are unchanged: it is a human-applied abort signal, never emitted by personas or the orchestrator.
- Observability: C7 emission discipline preserved verbatim — one atomic event per SDD step boundary, eleven required fields, phase-enum-keyed audit predicates, `event_id = sha256(ticket_id|phase|rerun_round|emitter)`. The `outcome.details.expert_verdicts[]` field is additive and MUST NOT alter the `event_id` derivation or the sealed three-emitter rule (orchestrator + webhook handler + local-cli). Per-expert verdict attribution becomes queryable post-merge: "show me everything Boundary Hawk blocked in the last 30 days" is a legitimate audit query against the C7 log.
- Reliability and rollback: Single-PR atomicity is the reliability strategy. All amendments (FR-008) land in this one PR. If the PR is closed without merge, the repository remains on the stage-persona model authored in PR #362 (which itself stays open until step06 of this ticket explicitly closes it). Rollback after merge would be a `git revert` of the merge commit — the additive C7 field tolerates rollback since existing consumers ignore the optional field.
- Monitoring/alerting: No new alerts. Quality-hooks-fast and quality-hooks-slow gates apply at PR-merge time as today.

## Risks and Tradeoffs
- Risk 1 — Expert sprawl over time: The 7-expert roster is sized for distinguishable postures; the temptation to add a fourth "QA Engineer" or "Solutions Architect" expert will recur. Mitigation: the ADR pins an 8-expert ceiling and requires any new expert to demonstrate distinct push-back triggers that the existing 7 do not cover. Below-distinction experts must be rejected or merged into an existing one.
- Risk 2 — Convergence-merge dedup quality: The default `parallel-then-merge` pattern requires merging verbatim findings across N experts. A naive dedup (string equality) will let semantically-duplicate findings ("missing log on error path" vs "error path has no observability") survive as two findings. Mitigation: ship a priority-order merger (`block > revise > pass`) for the verdict aggregation; finding dedup is a follow-up problem owned by #361's orchestrator implementation, not this ticket.
- Risk 3 — Per-expert model assignment cost: Panel sizes per step are `8 / dynamic / 1 / 4 / 5 / 3 / 4 / 8` for step01–step08; step01 and step08 are both all-8 fan-outs because they are the two judgment-heaviest steps (artifacts authored / full PR review). Total expert-step instantiations per work item ≈ 36 (step02 averaging ~3). Mitigation: the matrix caps panel sizes per step; step03 is intentionally minimal (1 expert); the heterogeneity ADR amendment encourages assigning cheaper models (Haiku) to high-volume, low-stakes experts (e.g., Documentation Discipline, Performance/Cost-Aware) and stronger models (Opus) only to high-stakes experts (Security Paranoid, Data Privacy, Boundary Hawk).
- Tradeoff 1 — Attribution vs simplicity: Per-expert verdict attribution in C7 audit is a strict win for debuggability but adds shape to the event payload. Accepted — the additive optional field shape keeps existing consumers unaffected while making attribution available to consumers who want it.
- Tradeoff 2 — Spec authoring effort here vs implementation effort in #361: This ticket carries a heavy spec/ADR load so #361 inherits an implementation-ready contract. Accepted — concentrating the architectural reasoning in one place prevents the dispatch contract from being re-litigated in #361.
- Tradeoff 3 — Cross-ticket amendments batched in step06: Posting amendment comments in a single batch at step06 of this ticket means the world sees the pivot atomically alongside the spec/ADR, rather than amendments arriving piecemeal. Accepted — coherent visibility is worth the small risk of step06 forgetting one ticket; the `pr_context.md` checklist (AC-005) enumerates all required URLs so the merge gate catches omissions.
