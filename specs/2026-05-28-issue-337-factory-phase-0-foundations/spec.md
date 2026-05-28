# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 7
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 7
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-007 (Clean Architecture dependency direction), SDD-C-008 (test pyramid), SDD-C-015 (app onboarding Make targets), SDD-C-018 (blueprint defect escalation), SDD-C-022 (local smoke gate), SDD-C-023 (filter/transform unit assertions), SDD-C-024 (finding-to-test translation) are not declared applicable: this work item produces governance documentation (10 ADRs, populated `.github/CODEOWNERS`, instrumentation plan, baseline measurements, triage+decomposition data feed) and updates to the #339 design-contracts document — no runtime code, no HTTP routes, no filters, no app onboarding surface, no consumer workaround surface, and no test pyramid beyond `make docs-build` / `make docs-smoke` / `make quality-sdd-check`. SDD-C-013 (STACKIT managed-first) and SDD-C-014 (local-first runtime) are declared applicable because the instrumentation plan selects a STACKIT-managed durable-bus platform (FR-013) and the metrics dashboard target resolves to the existing STACKIT-managed observability module (FR-016).

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

## Objective
- Business outcome: Lock the ten load-bearing architectural decisions, the two-layer CODEOWNERS routing, the durable success-metric instrumentation plan, the pre-factory baseline measurements, and the triage+decomposition data feed that Phase 1 factory tickets (#333, #334, #335, #336) and the deferred Phase 3 ticket (#338) all consume. Output is written governance artifacts (ten ADRs, `.github/CODEOWNERS` populated for the blueprint instance, instrumentation plan document, pre-factory baseline document, triage+decomposition data feed document) plus reciprocal updates to #339's design-contracts.md (resolving Open Decisions Q-2 and Q-3 with the blueprint instance's CODEOWNERS team slugs and dashboard target, and enumerating the ten ADRs as `stable` C8 consumer-shipped surface). This work item ships zero runtime code.
- Success metric: Zero Phase 1 ticket (#333, #334, #335, #336) is blocked at implementation start by an unresolved Phase 0 decision (measured as PR-time changes to any of the ten ADRs, the CODEOWNERS file, or the instrumentation plan that originate from a Phase 1 ticket reaching for missing context rather than from evolving requirements) AND #339 Contract C6 `### Blueprint instance`, C7 `### Blueprint instance`, and C8 ten-ADR enumeration are all populated with concrete values within the same PR cycle that signs off this work item.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-llm-model-router-policy.md` MUST declare the LLM model router policy as: default model `claude-sonnet-4-6`; escalation tier `claude-opus-4-7` for personas executing `blueprint-sdd-step03-spec-complete` and `blueprint-sdd-step04-plan-slicer`; routing rules MUST be expressed against the persona file basename + `## Activation Triggers` section (per #339 Contract C3); fallback behavior on gateway 5xx or model-unavailable MUST be a single bounded retry on the same model before failing the persona invocation upward; the ADR MUST cite #335 as the implementer of the routing rules in the LiteLLM gateway configuration. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed` (consumer instances MUST inherit identically; consumers are permitted to shadow only the per-instance LiteLLM access configuration declared by #339 Contract C8 FR-014).
- FR-002 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` MUST declare the persona/skill contract as: skills are runbooks (verbs); personas are actors with judgment (nouns); personas invoke skills; skills MUST NOT invoke other skills directly (cross-skill composition is a persona responsibility); no AI persona maps 1:1 to a human canonical sign-off role (Product/Architecture/Security/Operations) — sign-offs remain a human-only authority per `AGENTS.md § Sign-off Policy`. Cited by #333. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed`.
- FR-003 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-trigger-authorization-model.md` MUST declare: the `agent-ready` label MUST NOT be applied by any GitHub user whose membership in a designated GitHub team allowlist does not resolve to true at the moment of label application (the team slug name is parameterized per factory instance and MUST be declared via the #339 C8 consumer overlay schema); `agent-stop` label MUST abort in-flight runs within 60 seconds of label application; `agent-stop` cascade MUST propagate from a parent issue to every open child issue created by `blueprint-ticket-decompose-light`. Cited by #336. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed` for the trigger names and cascade semantics; `parameterized` for the team allowlist slug (consumer overlay schema lives in #339 Contract C8).
- FR-004 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-sovereignty-zdr-posture.md` MUST declare that EU sovereignty and zero-data-retention are enforced upstream by the LiteLLM gateway and the model providers it fronts, NOT by the factory runtime itself; the factory MUST NOT store Anthropic API keys, MUST NOT bypass the LiteLLM gateway, and MUST NOT retain prompt or completion content beyond the lifecycle event metadata declared by #339 Contract C7 (which carries no prompt/completion bodies). Cited by #334 and #335. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed` (listed explicitly in FR-017(b)).
- FR-005 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-separation-of-duties-at-factory-velocity.md` MUST declare that every factory-produced spec carries at least two distinct git identities across the four canonical sign-offs (Product/Architecture/Security/Operations), and that the factory bot identity declared per #339 Contract C5 is suppressed from the SoD count (the bot's sign-off comment, if any, MUST NOT count toward the two-distinct-identity requirement) via the exact-string-equality match on GitHub login required by #339 NFR-SEC-001. Cited by #334, #336. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed` (the multi-author SoD identical rule is listed explicitly in FR-017(b)).
- FR-006 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-reject-rerun-cap.md` MUST declare the maximum reject-rerun count as `2` before factory escalation; "reject-rerun" is defined as a factory-driven re-execution of any SDD step in response to a reviewer-applied `agent-rerun` (or equivalent) label or comment, counted per work-item per step type (e.g., two `step03-spec-complete` rerolls and two `step05-implement` rerolls are independent counters); escalation operational definition: the factory bot MUST apply the `factory-escalated` label, MUST post a PR comment naming the cap reached, and MUST stop accepting further reruns on the affected step type for the lifetime of that work item. Cited by #336. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed` (listed explicitly in FR-017(b)).
- FR-007 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md` MUST declare hard ceilings for cumulative factory wall-clock time and cumulative factory LLM cost per work item across all SDD steps and all reruns. For decomposed parents (via `blueprint-ticket-decompose-light`), the ceiling MUST apply per child issue independently (not summed against the parent). When the ceiling is exceeded for a work item, the factory bot MUST pause the work item, apply the `factory-paused-ceiling` label, and post a PR comment naming which ceiling was exceeded with the measured values. Cited by #336. ADR status: approved. Concrete ceiling values: see Open Decision Q-1. Identical-rule classification per #339 C8 FR-017: `parameterized` (the existence of the cap and the pause/label/comment semantics are identical; the numeric values per FR-017(b) are NOT listed and consumers are permitted to override via the #339 C8 consumer overlay schema).
- FR-008 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` MUST declare: AI PR reviewer personas (executing `blueprint-sdd-step08-agent-pr-review`) MUST run on a different model family than the implementer persona that produced the change; rotation rule MUST be: implementer on `claude-opus-4-7` (when escalated per FR-001) routes reviewers to `claude-sonnet-4-6`, AND implementer on `claude-sonnet-4-6` (default) routes reviewers to `claude-opus-4-7`; the LiteLLM gateway MUST enforce the rule by reading the implementer model from the lifecycle event stream (#339 Contract C7) and selecting the reviewer model accordingly. Cited by #333, #335. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed`.
- FR-009 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-triage-size-threshold.md` MUST declare the `blueprint-ticket-triage-size` classification rule with EXACTLY FOUR named classes (`small`, `medium`, `large-decomposable`, `escalate`) and MUST pin numeric thresholds for each class across three dimensions (bounded contexts touched; estimated token cost; estimated step count). `escalate` MUST route to fully human-driven completion (no factory execution). Cited by #333, #338. ADR status: approved. Concrete numeric thresholds: see Open Decision Q-2. Identical-rule classification per #339 C8 FR-017: `extensible` (default per FR-017; consumers are permitted to shadow the threshold table to tune for their own ticket-size distribution; the four-class structure and the `escalate`-routes-to-humans semantics are sealed via FR-007(b)-equivalent enumeration in this ADR).
- FR-010 An ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md` MUST declare the `blueprint-ticket-decompose-light` policy with: allowed boundary types `bounded-context | architectural-layer | user-visible-feature-behavior`; maximum fan-out `5` children per parent; refusal criteria (cross-cutting refactor, exploratory architecture work) MUST route to `escalate` per FR-009; grounding contract requires every child sub-ticket body to cite parent spec path (per #339 Contract C2) and boundary type; parent-tracking contract requires parent issue body to carry `## Integration Acceptance Criteria` per #339 Contract C4 and to remain open until all children are merged AND every checkbox is ticked by a human bounded-context reviewer. The ADR MUST EXPLICITLY note that Phase 1 does NOT automate composition verification; composition orchestration is Phase 3 (#338). Cited by #333, #338. ADR status: approved. Identical-rule classification per #339 C8 FR-017: `sealed` for the boundary-type enumeration, fan-out cap, refusal-criteria-routes-to-escalate semantics, and the grounding/parent-tracking contracts; `extensible` for the per-instance boundary catalogue (consumers populate their own bounded-context list).
- FR-011 `.github/CODEOWNERS` MUST be populated with two routing layers replacing the current placeholder content: (a) `# === Gate 1: Spec sign-off layer ===` mapping the four canonical sign-off roles (Product, Architecture, Security, Operations) to GitHub team slugs of the blueprint instance; (b) `# === Gate 2: Bounded-context merge layer ===` per bounded context defined for the blueprint repo, routing to the senior engineers responsible for that context. Each team named in any of the two layers MUST resolve to a real GitHub team with at least two members. Existing ownership boundaries declared in `AGENTS.md` (docs, scripts, Make targets) MUST be preserved. The concrete blueprint-instance team slugs and bounded-context enumeration: see Open Decision Q-3. The two-layer routing **shape** (gate 1 four-role mapping; gate 2 per-bounded-context ≥ 2 members each) is the #339 Contract C6 identical rule and applies to every consumer instance; this work item does NOT author any consumer-instance CODEOWNERS values.
- FR-012 An instrumentation plan document MUST exist at `docs/blueprint/autonomous-factory/instrumentation-plan.md` declaring: (a) primary metric `P50 lead time from agent-ready label application to PR merge`, measured per child and per parent-aggregate for decomposed tickets; (b) guardrail metrics `first-review rejection rate < 25%`, `post-merge defect rate ≤ pre-factory baseline`, `reviewer wall-time per PR (spec gate and merge gate) ≤ pre-factory baseline`; (c) data sources `GitHub Issues/PR events for lifecycle stamps`, `GitHub Actions run logs for CI evidence`, `LiteLLM gateway usage logs for model/cost attribution`, `the #339 Contract C7 durable-bus lifecycle event stream as the canonical event spine`; (d) dashboard target, retention, and owner — see Open Decision Q-4; (e) reporting cadence `weekly`; (f) per-`owner_team` breakdown shape for every metric (the blueprint instance reports a single `owner_team` while it is the sole factory; the breakdown shape MUST be in place from day one so consumer instances inherit it without re-instrumentation). The document MUST be carried by the Operations sign-off.
- FR-013 The instrumentation plan from FR-012 MUST conclude with the concrete STACKIT-managed durable-bus platform pick (or an explicit SKE-hosted fallback) as a Phase 0 prerequisite of #335 and #336. The pick MUST satisfy the #339 Contract C7 emission-transport rule (durability, replayability, async fire-and-forget, independent subscriber consumer-position tracking). The Grafana dashboard MUST subscribe to the bus rather than receive synchronous writes. Concrete platform pick: see Open Decision Q-5.
- FR-014 A pre-factory baseline document MUST exist at `docs/blueprint/autonomous-factory/pre-factory-baselines.md` recording baseline values for: (a) P50 lead time, current SDD workflow; (b) first-review rejection rate, current SDD workflow; (c) reviewer wall-time per PR, current SDD workflow; (d) post-merge defect rate (defects opened within 30 days of merge), current SDD workflow. The baseline measurement window: see Open Decision Q-6. Each baseline value MUST be presented with an explicit per-`owner_team` breakdown row (single row while the blueprint repo is the sole factory operator).
- FR-015 A triage+decomposition data feed document MUST exist at `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` recording, for the last 30 ticket cycles (where "ticket cycle" is defined as one merged PR closing one or more issues), what `blueprint-ticket-triage-size` (per FR-009 thresholds) WOULD HAVE classified the ticket as (one of `small | medium | large-decomposable | escalate`) and, when classified `large-decomposable`, what boundary set `blueprint-ticket-decompose-light` (per FR-010) WOULD HAVE proposed. The document MUST be machine-readable (a Markdown table with one row per ticket cycle is acceptable) so that Phase 3 (#338) composition orchestration design can consume it as evidence. The document MUST carry an explicit caveat that these are retrospective hypothetical classifications, not factory-produced classifications.
- FR-016 #339 Contract C6 `### Blueprint instance` subsection MUST be updated in the same PR cycle as this work item to record the blueprint's resolved gate 1 team slugs (per FR-011) and the bounded-context enumeration (per FR-011 / Open Decision Q-3); #339 Contract C7 `### Blueprint instance` subsection MUST be updated in the same PR cycle to record `stackit-managed-grafana` (via the existing observability module) as the dashboard target, the retention, and the dashboard owner (per FR-012 / Open Decision Q-4). The update MUST also resolve the #339 Contract C7 `### Open Decisions` durable-bus platform pick to the value selected by FR-013 / Open Decision Q-5.
- FR-017 #339 Contract C8 MUST be updated in the same PR cycle as this work item to enumerate the ten ADRs (FR-001 through FR-010) under category (a) of FR-013 (`documentation and ADRs under docs/blueprint/autonomous-factory/ and docs/blueprint/architecture/decisions/`) with stability tier `stable` and extensibility tier per each ADR's classification declared in FR-001 through FR-010. The instrumentation plan (FR-012), pre-factory baselines (FR-014), and triage+decomposition data feed (FR-015) MUST also be enumerated under category (a) with stability tier `stable` and extensibility tier `extensible` (default per #339 FR-017).
- FR-018 The blueprint repo MUST have a `.agents/personas/` directory existing at the path declared by #339 Contract C8 (this work item creates an empty placeholder structure only — concrete persona files are owned by #333) AND a `.agents/personas/consumer/` directory existing per the #339 FR-018 namespaced discovery convention with a `.gitkeep` placeholder. No persona content is authored by this work item; the empty-directory structure satisfies the discoverability precondition for the #336 GitHub Actions workflow and the #335 OpenHands loader.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The FR-004 sovereignty/ZDR ADR MUST NOT introduce any factory-side egress allowlist, key-storage, or content-retention mechanism; it MUST cite the LiteLLM gateway and #334 (Secrets Manager + ESO + egress NetworkPolicy + factory bot identity on the existing SKE foundation cluster) as the enforcement points and MUST NOT duplicate their controls in factory code or configuration.
- NFR-SEC-002 The FR-005 SoD ADR MUST reference #339 NFR-SEC-001 verbatim for the exact-string-equality match rule on the factory bot GitHub login and MUST NOT introduce substring, regex, or display-name heuristics.
- NFR-OBS-001 Every metric named in FR-012 and every baseline named in FR-014 MUST be expressed as a measurable expression over the #339 Contract C7 lifecycle event stream OR over GitHub event payloads, with the source-of-truth field explicitly named in the instrumentation plan; metrics with no expressible source MUST NOT be listed.
- NFR-REL-001 Each of the ten ADRs (FR-001 through FR-010) MUST be revertible in isolation by reverting its single ADR file plus any reciprocal update to #339 design-contracts.md scoped to that ADR; the `.github/CODEOWNERS` change (FR-011) MUST be revertible in isolation by reverting the CODEOWNERS file plus the matching #339 Contract C6 `### Blueprint instance` revert (FR-016).
- NFR-OPS-001 All artifacts produced by this work item MUST be discoverable via `make docs-build` and MUST pass `make docs-smoke` with no link or anchor regressions; the ten ADRs and the three `docs/blueprint/autonomous-factory/` documents (instrumentation plan, pre-factory baselines, triage+decomposition data feed) MUST be linked from the autonomous-factory landing page if one exists, or have their landing-page status recorded as deferred follow-up under `### Open Decisions`.
- NFR-OPS-002 The bootstrap template mirror under `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/` MUST be synchronized for any consumer-shipped document added by this work item (per the `template_sync_allowlist` extension required by #339 Contract C8 enumeration). ADRs are NOT mirrored per the existing blueprint convention (ADR files are not enumerated in `template_sync_allowlist`).
- NFR-A11Y-001 N/A — internal governance documentation. No UI surface is introduced or modified by this work item.

## Normative Option Decision
- Option A: Single Phase 0 work item producing all ten ADRs, the CODEOWNERS, the instrumentation plan, the baseline measurements, the triage+decomposition data feed, and the reciprocal #339 design-contracts.md updates in one signed-off PR.
- Option B: Ten separate ADR work items (one per ADR), with the CODEOWNERS, instrumentation plan, baselines, and data feed each as additional standalone work items, ordered serially.
- Selected option: OPTION_A
- Rationale: the ten ADRs are tightly coupled (e.g., the model router policy, reviewer model heterogeneity, and reject-rerun cap all reference the same lifecycle event stream and the same LiteLLM gateway; the CODEOWNERS, instrumentation plan, and baselines all resolve #339 Open Decisions in the same PR cycle); ten separate sign-off cycles would multiply review burden without reducing risk; the issue is explicitly framed as one Phase 0 ticket; Option B would block Phase 1 by an order of magnitude longer than Option A. Mitigation for the larger-PR blast radius: every artifact is independently revertible per NFR-REL-001.

## Contract Changes (Normative)
- Config/Env contract: introduces no new `blueprint/contract.yaml` keys directly (the LiteLLM access shape and consumer overlay schemas are owned by #339 / #335). The `template_sync_allowlist` MUST be extended to include the three `docs/blueprint/autonomous-factory/` documents authored here (instrumentation-plan.md, pre-factory-baselines.md, triage-decomposition-data-feed.md).
- API contract: none.
- OpenAPI / Pact contract path: none
- Event contract: no new event types defined; references the #339 Contract C7 lifecycle event schema as the source-of-truth for all metrics declared by FR-012.
- Make/CLI contract: no new Make targets introduced.
- Docs contract: introduces ten ADRs under `docs/blueprint/architecture/decisions/` (one summary ADR per FR-001 through FR-010, plus the meta-ADR at `ADR-issue-337-factory-phase-0-foundations.md` per the ADR path declared in the Spec Readiness Gate); introduces three documents under `docs/blueprint/autonomous-factory/` (instrumentation-plan.md, pre-factory-baselines.md, triage-decomposition-data-feed.md); modifies `.github/CODEOWNERS`; modifies `docs/blueprint/autonomous-factory/design-contracts.md` (C6 `### Blueprint instance`, C7 `### Blueprint instance`, C7 `### Open Decisions`, C8 ADR enumeration) per FR-016, FR-017; modifies `blueprint/contract.yaml` `template_sync_allowlist`; creates empty `.agents/personas/consumer/` directory per FR-018.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 All ten ADR files named in FR-001 through FR-010 exist under `docs/blueprint/architecture/decisions/`, each with `Status: approved` and each carrying all four canonical sign-off phrases recorded in the PR comment thread.
- AC-002 `.github/CODEOWNERS` contains both routing layers per FR-011; the file contains zero `@your-org/...` placeholder text; every team slug named in any of the two layers resolves to a real GitHub team carrying at least two members (verified by Operations during sign-off).
- AC-003 `docs/blueprint/autonomous-factory/instrumentation-plan.md` exists per FR-012, names a concrete durable-bus platform per FR-013, names a concrete dashboard target (`stackit-managed-grafana` via the observability module) per FR-012(d), and carries the per-`owner_team` breakdown shape declared in FR-012(f).
- AC-004 `docs/blueprint/autonomous-factory/pre-factory-baselines.md` exists per FR-014 with all four metric baselines recorded and the per-`owner_team` breakdown row populated.
- AC-005 `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` exists per FR-015 with at least 30 ticket-cycle rows (or an explicit `### Sample Size` subsection documenting why fewer were available and why that is acceptable evidence for #338).
- AC-006 `docs/blueprint/autonomous-factory/design-contracts.md` Contract C6 `### Blueprint instance`, Contract C7 `### Blueprint instance`, Contract C7 `### Open Decisions` (durable-bus pick), and Contract C8 ten-ADR enumeration are all updated per FR-016 and FR-017; the matching `evidence_manifest.json` SHA-256 for the design-contracts.md update is regenerated.
- AC-007 `make quality-sdd-check` passes against this work item's `specs/2026-05-28-issue-337-factory-phase-0-foundations/` directory.
- AC-008 `make docs-build` and `make docs-smoke` pass with all new ADRs and `docs/blueprint/autonomous-factory/` documents added.
- AC-009 The `template_sync_allowlist` in `blueprint/contract.yaml` includes the three `docs/blueprint/autonomous-factory/` documents authored here, and the bootstrap template mirror under `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/` contains byte-identical copies (verified by re-running `python3 scripts/lib/docs/sync_blueprint_template_docs.py` and observing zero diff).
- AC-010 `.agents/personas/consumer/.gitkeep` exists per FR-018; `.agents/personas/` directory exists.
- AC-011 The meta-ADR at `docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md` exists with `Status: approved`, links to each of the ten content ADRs by relative path, and links to the three `docs/blueprint/autonomous-factory/` documents by relative path.

## Informative Notes (Non-Normative)
- Context: this work item is the Phase 0 sibling of #339 and ships the load-bearing architectural decisions Phase 1 (#333–#336) depends on. The ten ADRs are the textual record of decisions the user has already pinned in the autonomous-factory initiative memory; this work item captures them as `Status: approved` artifacts so Phase 1 tickets can cite them rather than re-deriving them. The CODEOWNERS file is the compliance-critical artifact that must be in place before the factory opens its first Draft PR (otherwise gate-1 sign-off routing is undefined). The pre-factory baselines and triage+decomposition data feed are the only Phase 0 outputs that require historical evidence rather than forward decisions.
- Tradeoffs: bundling ten ADRs into one PR concentrates review burden in a single sign-off cycle. Mitigation: each ADR is independently revertible (NFR-REL-001) and the artifact set follows the same proven cadence as #339 (eight contracts + one ADR in one PR cycle, signed off in 24h). The alternative (ten separate ADR cycles) would block Phase 1 by 2–3 weeks at current sign-off velocity.
- Clarifications:
  - **[NEEDS CLARIFICATION: Q-1 — Per-ticket wall-clock and cost ceiling concrete values for the blueprint instance (FR-007).]**

    **Options:**
    - **A)** Wall-clock `90 minutes per work item / per child` (decomposed); cost `$15 USD per work item / per child` — chosen to bound a worst-case full-SDD cycle (10 step types × ~5 min average × 2 rerolls) plus a reviewer pass without surfacing cost surprises (Agent recommendation)
    - **B)** Wall-clock `180 minutes`; cost `$30 USD` — looser; trades cost discipline for higher completion rate on first-try-imperfect items
    - **C)** Defer numeric values to a follow-up PR after first 10 factory runs produce empirical data — defers a P0 acceptance criterion

    **Agent recommendation:** Option A because the cap exists to catch runaway loops, not to right-size against unknown future usage; tighter caps surface design flaws earlier; consumers are permitted to override via the C8 consumer overlay per FR-007.

  - **[NEEDS CLARIFICATION: Q-2 — Triage-size threshold numeric values for `blueprint-ticket-triage-size` (FR-009).]**

    **Options:**
    - **A)** `small`: ≤1 bounded context AND ≤50k tokens AND ≤6 SDD step invocations; `medium`: ≤2 contexts AND ≤150k tokens AND ≤12 invocations; `large-decomposable`: ≤4 contexts AND ≤400k tokens AND ≤24 invocations; `escalate`: otherwise — drawn from the rough size of historical PRs in this repo (Agent recommendation)
    - **B)** Two classes only (`autonomous` / `escalate`) with a single combined threshold — simpler but loses the decomposition signal that #338 needs
    - **C)** Defer numeric values until Phase 1 produces first-10-run empirical evidence — defers a P0 acceptance criterion and blocks the FR-015 retrospective classification

    **Agent recommendation:** Option A because FR-015 requires retrospective classification of 30 past tickets, which is impossible without concrete thresholds; the values can be tuned in a subsequent ADR amendment after Phase 1 evidence accumulates.

  - **[NEEDS CLARIFICATION: Q-3 — Blueprint-instance CODEOWNERS team slugs (FR-011): the four gate-1 slugs and the gate-2 bounded-context enumeration with members.]**

    **Options:**
    - **A)** Gate-1: `@sbonoc/factory-product`, `@sbonoc/factory-architecture`, `@sbonoc/factory-security`, `@sbonoc/factory-operations` (resolved by #339 Q-2 — provisional). Gate-2 bounded contexts (provisional from #339): `factory`, `infra`, `docs`, `governance` — each mapped to a real GitHub team of ≥ 2 members. Operations sign-off attests to team provisioning. (Agent recommendation conditional on team provisioning being completed before sign-off)
    - **B)** Single combined team `@sbonoc/blueprint-maintainers` for all roles — fails the multi-author SoD requirement; rejected.
    - **C)** Defer team provisioning to a follow-up PR; ship CODEOWNERS with the four slug names from Option A but record under `### Open Decisions` that team membership must reach ≥ 2 members before the first factory `agent-ready` label is applied — defers an AC-002 acceptance criterion.

    **Agent recommendation:** Option A if the user can provision the teams during this PR cycle; otherwise Option C with the deferred follow-up explicitly tracked.

  - **[NEEDS CLARIFICATION: Q-4 — Instrumentation plan dashboard target, retention, and owner concrete values (FR-012(d)).]**

    **Options:**
    - **A)** Target `stackit-managed-grafana` (via existing OBSERVABILITY_ENABLED module, resolved by #339 Q-3 — provisional); retention `13 months` (matches the #334 LogMe WORM SOC 2 floor for cross-correlation); owner `@sbonoc/factory-operations` (from Q-3 gate-1 slugs) — Agent recommendation
    - **B)** Target `stackit-managed-grafana`; retention `90 days`; owner `@sbonoc/factory-operations` — shorter retention reduces storage cost; loses SOC 2 cross-correlation window with LogMe forensic retention
    - **C)** Self-hosted Grafana in the factory K8s cluster — fails SDD-C-013 managed-first; rejected

    **Agent recommendation:** Option A because retention parity with #334 LogMe is the cheapest way to make incident forensics tractable (one query window covers both audit log and metrics); the storage cost differential at expected event volumes (≤ 1k events/day for a single factory) is negligible.

  - **[NEEDS CLARIFICATION: Q-5 — Concrete STACKIT-managed durable-bus platform pick (FR-013).]**

    **Options:**
    - **A)** STACKIT-managed Kafka (`stackit_kafka_instance` Terraform resource) when the provider exposes the resource as `stable` (verify via availability spike) — first preference per the #339 FR-010 wording and the issue text
    - **B)** SKE-hosted Strimzi (Kafka operator on the factory K8s cluster) if Option A is not provider-stable — preserves Kafka semantics without requiring the managed instance; adds K8s operational ownership to Operations
    - **C)** STACKIT-managed RabbitMQ (durable queues with replay via dead-letter exchange) if Options A and B both fail availability — semantics shift from log-based replay to queue-based redelivery; affects subscriber implementation
    - **D)** Defer pick to a follow-up PR with a 1-week availability spike — blocks AC-003 and #339 C7 `### Open Decisions` resolution

    **Agent recommendation:** Option A if a 1-day availability spike confirms the STACKIT Terraform provider exposes `stackit_kafka_instance` as `stable`; otherwise Option B. Skip Option C unless both A and B fail.

  - **[NEEDS CLARIFICATION: Q-6 — Pre-factory baseline measurement window for FR-014 (last 90 days vs. all-time vs. since SDD enablement).]**

    **Options:**
    - **A)** All merged PRs to `main` since SDD was enabled (commit that introduced `SPEC_READY` gate, on 2026-04-17 — exact commit SHA to be pinned by Operations at sign-off) through the day before this PR is signed off — uses every PR governed by the same SDD process the factory will inherit; sample size is what it is (Agent recommendation)
    - **B)** Last 90 days only — fixed window for repeatability; loses earlier SDD-era PRs and is likely to shrink the sample below statistical relevance
    - **C)** All-time (every merged PR regardless of SDD) — mixes pre-SDD and post-SDD workflows; baseline does not represent the factory's actual comparand

    **Agent recommendation:** Option A because the factory is replacing the SDD-era human workflow specifically; the baseline must measure the same workflow class.

  - **[NEEDS CLARIFICATION: Q-7 — Sample size for the FR-015 triage+decomposition data feed if fewer than 30 ticket cycles exist within the Q-6 window.]**

    **Options:**
    - **A)** Use whatever count is available (≥ 1) and record a `### Sample Size` subsection with the actual count and a note acknowledging the limitation; #338 design treats it as directional, not statistical (Agent recommendation)
    - **B)** Defer FR-015 entirely until 30 ticket cycles accumulate post-Phase-0 — defers AC-005 and removes evidence input from #338 design
    - **C)** Synthesize 30 hypothetical ticket descriptions to reach the count — fabricated evidence; rejected

    **Agent recommendation:** Option A because retrospective classification of even a small real sample is more useful evidence for #338 than no evidence; the limitation is recorded transparently.

## Explicit Exclusions
- Excluded item 1: implementation of any of the ten ADRs (e.g., wiring the LiteLLM router rules, implementing the reject-rerun counter, building the trigger authorization workflow, emitting lifecycle events to the durable bus) — all owned by Phase 1 tickets #333, #334, #335, #336.
- Excluded item 2: authoring the ten persona files (`po-analyst.md` and siblings) or any of the ten new skill runbooks — owned by #333.
- Excluded item 3: provisioning the factory bot GitHub account, scoping its PAT, configuring ESO + Secrets Manager on the existing SKE foundation cluster, or applying the egress NetworkPolicy — owned by #334.
- Excluded item 4: deploying OpenHands Agent Server, configuring LiteLLM gateway routing rules, or implementing factory bot git identity — owned by #335.
- Excluded item 5: implementing the GitHub Actions webhooks (3-way triage, `spec-signed-off` auto-trigger, `agent-stop` cascade, step08 insertion, reject-rerun cap enforcement) — owned by #336.
- Excluded item 6: composition orchestration for decomposed parents (integration AC authoring, child sequencing, integration verification) — owned by Phase 3 #338, deferred until the FR-015 data feed accumulates real-factory evidence.
- Excluded item 7: any change to the #339 design-contracts.md beyond the C6/C7 `### Blueprint instance` resolutions, C7 `### Open Decisions` durable-bus pick, and C8 ten-ADR enumeration required by FR-016 and FR-017 — other contract sections remain frozen at the #339 sign-off content.
- Excluded item 8: authoring concrete persona files or skill runbook content under `.agents/personas/` — only the empty-directory structure for `.agents/personas/consumer/` is created here per FR-018 to satisfy the loader-discoverability precondition.
