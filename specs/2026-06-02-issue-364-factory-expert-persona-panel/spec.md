# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none
- Has user-facing flow: false
  <!-- inferred from intake: no UI / frontend / browser signals — defaulted to false — confirm before SPEC_READY -->
  <!-- Signal list — set true if the issue or FR text mentions ANY of: form, wizard, modal,
       dialog, page, screen, UI, frontend, browser, user journey, onboarding, dashboard,
       button, input, component, flow, checkout, login, signup, profile, settings, view,
       layout, render, display; labels: frontend, ui, ux, web, accessibility; any frontend
       framework name. A non-none frontend-stack-profile always implies true. -->
- E2E gate classification: N/A
  <!-- Allowed values: automated | manual | N/A
       automated: Playwright tests cover the full user journey and are wired to CI.
       manual: gate violation when has-user-facing-flow: true and test profile contains playwright;
               only valid when has-user-facing-flow: false.
       N/A: no user-facing flow; gate does not apply (default when has-user-facing-flow: false). -->

## Objective
- Business outcome: Replace the stage-persona model authored in #360 / PR #362 (10 personas, each owning a single SDD step) with a cross-cutting expert-persona panel (8 standing experts dispatched across multiple SDD steps), so the personas layer adds judgment and quality lensing rather than duplicating the procedural verbs already owned by the skills layer. The factory's three layers — SDD step (sealed boundary), skill (deterministic verb), expert persona (standing lens) — become cleanly separated and independently extensible.
- Success metric: After merge, (1) zero `.agents/personas/` files contain `Skills Invoked`, `Activation Triggers`, or `Definition of Done` sections; (2) the SDD-step × expert dispatch matrix is single-sourced in `docs/blueprint/autonomous-factory/design-contracts.md` § C3 and referenced (not duplicated) from `ADR-issue-364-expert-persona-model.md`; (3) `ADR-issue-360-factory-personas-skills-roster.md` carries `Status: superseded by ADR-issue-364-expert-persona-model.md`; (4) cross-ticket amendments for #333, #361, #335, #336, #342, #343, #332 and supersession comments on #360 and PR #362 are visible in the GitHub UI as comments authored within this PR's review window; (5) `make quality-sdd-check`, `make quality-hooks-fast`, and `make quality-hooks-slow` pass on the merge commit.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The repository MUST contain EXACTLY ONE OF the following expert-persona directory shapes: a flat `.agents/personas/<expert-slug>/PERSONA.md` per expert. There MUST be 8 expert personas with slugs `product-pragmatist`, `boundary-hawk`, `security-paranoid`, `data-privacy`, `test-quality-sceptic`, `operability-sre`, `documentation-discipline`, `performance-cost-aware`. Each `PERSONA.md` MUST contain the sections, in order: `# <Expert Title>`, `## Worldview`, `## Default Heuristics`, `## Push-back Triggers`, `## What I Notice That Others Miss`, `## Quality Bar`, `## Communication Style`. Each `PERSONA.md` MUST NOT contain any of the sections `## Skills Invoked`, `## Activation Triggers`, `## Definition of Done`, `## Collaboration & Handoffs`, `## Strict Guardrails`, `## SDD Cycle Stakes`, `## Required Inputs`, `## Role Objective`. The `data-privacy` persona's worldview MUST frame data as a liability and assert data minimization, residency, lawful basis, retention, and subject rights as first-order concerns; its push-back triggers MUST be distinct from `security-paranoid` (which addresses threat actors and attack surface, not lawful-basis / retention / subject-rights posture).
- FR-002 The file `docs/blueprint/autonomous-factory/design-contracts.md` § C3 MUST contain a single authoritative SDD-step × expert matrix table that lists, for each of `step01` through `step08`, (a) the skill that produces the step's draft output, (b) the experts consulted (with one marked as lead voice), and (c) the convergence mode applied (`parallel-then-merge`, `sequential-lens`, or `structured-disagreement`). `ADR-issue-364-expert-persona-model.md` MUST reference this table by file path and section anchor and MUST NOT duplicate the table content.
- FR-003 `ADR-issue-364-expert-persona-model.md` MUST define EXACTLY ONE OF the three convergence patterns as the default (`parallel-then-merge`) and MUST enumerate the steps where each non-default pattern applies (`sequential-lens` reserved for `step05`; `structured-disagreement` reserved for `step08` only — step03 is excluded because its panel size of 1 makes block-conflict impossible). The ADR MUST state that conflicting `block` verdicts SHALL surface at the existing two human gates (spec sign-off, PR merge) and SHALL NOT introduce a new gate.
- FR-004 The expert dispatch contract MUST require every dispatched expert to return a structured verdict object conforming to the schema `{ "verdict": "pass" | "revise" | "block", "findings": Array<Finding> }`. When the expert has no concern, `findings` MUST be the empty array `[]` and `verdict` MUST be `pass`. The dispatch contract MUST NOT permit silent omission of a verdict from a dispatched expert. The contract MUST be expressed as a JSON Schema embedded in `ADR-issue-364-expert-persona-model.md`.
- FR-005 `ADR-issue-360-factory-personas-skills-roster.md` MUST be updated to `Status: superseded by ADR-issue-364-expert-persona-model.md` and MUST link to the superseding ADR in its first body paragraph. `ADR-issue-337-persona-skill-contract.md`, `ADR-issue-337-c7-emission-mechanism.md`, and `ADR-issue-337-reviewer-model-heterogeneity.md` MUST each receive an "Amended by ADR-issue-364-expert-persona-model.md" line in their front-matter or first-section header, naming the clause(s) amended.
- FR-006 The skill runbooks under `.agents/skills/blueprint-*/SKILL.md` touched by #360 / PR #362 (10 net-new SKILL.md files plus content-additions to 8 pre-existing SDD-step skills) MUST be re-homed onto this branch with the following modifications wherever persona-coupling language appears: (a) the `Actor` section MUST cite the orchestrator and the expert panel rather than a named stage-persona (e.g., "tech-lead persona"); (b) the `Composition` section MUST cite the orchestrator's dispatch table as the binding mechanism; (c) `blueprint-sdd-step08-agent-pr-review/SKILL.md` MUST accept a panel-input parameter naming the experts to consult and MUST produce a per-expert verdict array in its `## Required Output Schema`.
- FR-007 The C7 lifecycle event schema MUST be amended to permit (but not require) an `outcome.details.expert_verdicts` array of objects, each conforming to `{ "expert_slug": <string>, "verdict": "pass" | "revise" | "block", "findings_count": <integer> }`. The amendment MUST be authored as an additive change to `ADR-issue-337-c7-emission-mechanism.md` so the field is backwards-compatible with existing C7 events.
- FR-008 At step06 of THIS work item, comment-based amendments MUST be posted to: #333 (epic body retitle proposal + scope amendment), #361 (orchestrator dispatch table reformulation), #335 (per-expert LiteLLM routing + capacity sizing note), #336 (FR-008 audit invariant reformulated as panel-disjointness rule), #342 (per-artifact versioning extends to expert-persona files), #343 (Phase 1 ingestion schema accounts for `expert_verdicts[]`), #332 (epic body framing update). #360 MUST be closed as superseded with a reference to issue #364 and a cherry-pick list. PR #362 MUST be closed as superseded with the same cherry-pick list and a top-comment naming this PR.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The expert-panel dispatch model MUST preserve the existing Separation-of-Duties posture: expert verdicts are bot-authored and MUST NOT count toward the four canonical human sign-off phrases. The two human gates (spec sign-off, PR merge) MUST remain the sole sources of human approval. Any future proposal to expose expert verdicts as auto-promotable sign-offs MUST be filed as a separate ticket and is out of scope here.
- NFR-OBS-001 The C7 emission discipline (one atomic event per SDD step boundary, eleven required fields, phase-enum-keyed audit predicates, `event_id = sha256(ticket_id|phase|rerun_round|emitter)`) MUST remain unchanged. The `outcome.details.expert_verdicts[]` field MUST be additive and MUST NOT alter the `event_id` derivation, the sealed three-emitter rule, or the one-event-per-phase-boundary invariant.
- NFR-REL-001 All amendments enumerated in FR-008 MUST land in a single PR (this one), so no future session reads a half-updated repository state. If the PR is closed without merge, the pivot MUST be considered fully reverted and the repository MUST remain on the pre-pivot stage-persona model with PR #362 as the source of truth for any partial work cherry-picked into this branch.
- NFR-OPS-001 The merge commit MUST pass `make quality-sdd-check`, `make quality-hooks-fast`, and `make quality-hooks-slow` with exit code 0. Bootstrap template mirrors under `scripts/templates/blueprint/bootstrap/` MUST be resynced via `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py` before the merge commit so the docs-check changed gate passes.
- NFR-A11Y-001 N/A — this work item produces only persona files, ADRs, skill runbooks, and GH-issue amendments; there is no user-facing UI surface affected.

## Normative Option Decision
- Option A: Cross-cutting expert-persona panel (7 standing experts, dispatched per SDD step via a matrix; default convergence = parallel-then-merge; always-respond verdict contract).
- Option B: Refine the existing stage-persona model from #360 / PR #362 in place (collapse Skills Invoked / Activation Triggers / DoD sections; keep 1:1 persona-owns-stage mapping; add expert-lens worldview sections additively).
- Selected option: OPTION_A
- Rationale: Option B preserves the structural conflation between layer 2 (skill = procedural verb) and layer 3 (persona = standing lens) that drove the PR #362 disappointment. Option A is the only path that lets the personas layer earn its keep over the skills layer by holding judgment-and-style rather than execution. Option A also unlocks per-expert model assignment (heterogeneity ADR) and per-expert audit attribution in C7 — both of which Option B cannot deliver without re-introducing the stage/lens conflation.

## Contract Changes (Normative)
- Config/Env contract: none.
- API contract: none — no HTTP route changes.
- OpenAPI / Pact contract path: none.
- Event contract: C7 lifecycle event schema gains additive optional field `outcome.details.expert_verdicts: Array<{ expert_slug: string, verdict: enum, findings_count: integer }>`. Authored as amendment to `ADR-issue-337-c7-emission-mechanism.md`. Existing emitters and consumers remain valid.
- Make/CLI contract: none — no new make targets. The orchestrator's dispatch table (delivered in #361) is the runtime contract; this ticket only delivers spec + ADR + persona files + skill runbook edits + GH amendments.
- Docs contract: `docs/blueprint/autonomous-factory/design-contracts.md` § C3 reshaped to single-source the SDD-step × expert matrix; AGENTS.md persona section retitled and rewritten; `MEMORY.md` index updated to reflect the new model.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 [8 expert-persona files exist with the 6 required sections and none of the forbidden sections] — verified by T-101, which MUST assert that for each slug in `{product-pragmatist, boundary-hawk, security-paranoid, data-privacy, test-quality-sceptic, operability-sre, documentation-discipline, performance-cost-aware}` the file `.agents/personas/<slug>/PERSONA.md` exists AND contains the headings `## Worldview`, `## Default Heuristics`, `## Push-back Triggers`, `## What I Notice That Others Miss`, `## Quality Bar`, `## Communication Style` AND contains none of the headings `## Skills Invoked`, `## Activation Triggers`, `## Definition of Done`, `## Collaboration & Handoffs`, `## Strict Guardrails`, `## SDD Cycle Stakes`, `## Required Inputs`, `## Role Objective`. T-101 MUST additionally assert that `data-privacy/PERSONA.md` contains the substrings `data minimization`, `lawful basis`, `retention`, and `subject rights` in its `## Worldview` or `## Default Heuristics` sections to confirm it carries the distinguishing posture (not just the section shape).
- AC-002 [Superseding ADR exists with cross-references to the four amended ADRs] — verified by T-102, which MUST assert that `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` exists with `Status: proposed` (at PR open) or `Status: accepted` (after sign-off) AND contains the substrings "supersedes ADR-issue-360-factory-personas-skills-roster.md", "amends ADR-issue-337-persona-skill-contract.md", "amends ADR-issue-337-c7-emission-mechanism.md", "amends ADR-issue-337-reviewer-model-heterogeneity.md".
- AC-003 [Single-source SDD-step × expert matrix] — verified by T-103, which MUST assert that `docs/blueprint/autonomous-factory/design-contracts.md` contains a `## C3` section heading AND a markdown table with header row beginning with `| SDD step | Skill | Experts consulted | Lead voice | Convergence mode |` (header text MUST match exactly to prevent silent drift) AND that the ADR file references this section by the relative path string `../../autonomous-factory/design-contracts.md`.
- AC-004 [Skill runbooks contain no stage-persona language] — verified by T-104, which MUST assert that `grep -rE "(po-analyst|tech-lead|qa-engineer|implementer-backend|implementer-frontend|implementer-infra|reviewer-security|reviewer-architecture|reviewer-contracts|reviewer-tests|documentation-keeper) persona" .agents/skills/blueprint-*/SKILL.md` returns zero matches.
- AC-005 [Cross-ticket amendments posted and recorded] — verified by T-105, which MUST assert that `pr_context.md` contains a "Cross-Ticket Amendments" section listing comment URLs (one per line) for each of: #333, #361, #335, #336, #342, #343, #332, #360 (close-with-reference), PR #362 (close-with-reference), AND that the URLs return HTTP 200 when fetched via the `gh` CLI.
- AC-006 [Quality gates pass on merge commit] — verified by T-106, which MUST assert that `make quality-sdd-check`, `make quality-hooks-fast`, and `make quality-hooks-slow` each exit 0 on the head of this branch immediately before merge.
- AC-007 [Memory index reflects new model] — verified by T-107, which MUST assert that `/Users/bonos/.claude/projects/-Users-bonos-dev-workspace-stackit-platform-blueprint/memory/MEMORY.md` contains a line referencing the expert-persona-panel model (substring `expert.persona` case-insensitive) AND that `project_autonomous_factory.md`, `project_factory_design_contracts.md`, and `project_factory_c7_emission_mechanism.md` each contain a paragraph noting the post-#364 model. (This AC is satisfied by edits to the user's local memory store; the test harness MUST treat absence of the store as `skip` rather than `fail`, since the store lives outside the repo.)

## Informative Notes (Non-Normative)
- Context: This ticket is the architectural pivot decided after review of #360 / PR #362. The stage-persona model authored there was diagnosed as "pipeline stages dressed in role names" — personas duplicating procedural verbs already owned by skills. The expert-persona model separates the three layers cleanly: SDD step (sealed boundary) → skill (deterministic verb) → expert persona (standing lens).
- Tradeoffs: (a) Higher LLM call volume per SDD step (1 skill + N expert reviews vs 1 stage-persona) — mitigated by capping N per step via the matrix; step08 fans out to all 8 as designed. (b) Convergence merger is new code surface — landed in #361, not here. (c) Risk of expert sprawl — held by the 8-expert ceiling stated in the ADR (the panel is now AT the ceiling on day one; any 9th expert MUST demonstrate distinct push-back triggers that the existing 8 do not cover, or MUST replace an underperforming existing expert). (d) Harder attribution of bad output — mitigated by per-expert verdict in C7 audit.
- Clarifications: none open at intake.

## Explicit Exclusions
- Excluded item 1: Expert-panel consultation for human-driven local SDD sessions (the `local-cli` C7 emitter from #347). Solo operators driving SDD locally continue to do so without panel dispatch. Optional future work (`make expert-review`) is flagged in the ADR's "Future Work" section but is out of scope here.
- Excluded item 2: Factory runtime implementation. The orchestrator dispatch table (`step → {skill, expert_panel, convergence, model_per_expert}`) lives in #361's spec; this ticket only delivers the spec, ADR, persona files, skill runbook edits, and GH amendments. The orchestrator code itself ships under #361.
- Excluded item 3: Per-expert LiteLLM model assignment implementation. Routing keys and capacity-sizing notes are amended into #335 via comment here; the OpenHands / LiteLLM wiring itself ships under #335.
- Excluded item 4: Brain ingestion schema update for `expert_verdicts[]`. Epic #343 receives a comment here; the schema work itself is part of #343's Phase 1 when that epic is promoted from Draft.

## Potential Deferred Proposals
- Expert-panel consultation in human-driven local SDD sessions: out of scope per Excluded item 1; future work flagged in ADR.
- Per-expert prompt-cache discipline (separate caches per expert worldview to avoid contamination): noted as observability concern in ADR but out of scope for spec; will surface naturally during #361 orchestrator implementation.
- Expert-verdict-to-skill-output feedback loop (have skills regenerate when ≥2 experts block): not designed here; treated as a #361 follow-up if parallel-then-merge proves insufficient.
