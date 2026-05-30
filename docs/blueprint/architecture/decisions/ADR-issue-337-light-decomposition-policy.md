# ADR: Light Decomposition Policy (`blueprint-ticket-decompose-light`)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-010)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed` for the boundary-type enumeration, fan-out cap, refusal-criteria-routes-to-escalate semantics, and grounding/parent-tracking contracts; `extensible` for the per-instance bounded-context catalogue (consumers populate their own bounded-context list).

## Context

[`ADR-issue-337-triage-size-threshold.md`](ADR-issue-337-triage-size-threshold.md) routes `large-decomposable` tickets to `blueprint-ticket-decompose-light` — a Phase 1 skill that breaks a parent ticket into a small set of child sub-tickets along a single named axis. Without an explicit policy, the decomposer could (a) propose arbitrary boundary types, producing children with no shared vocabulary across factory cycles; (b) fan out to arbitrarily many children, multiplying per-child cost ceilings (FR-007); (c) accept cross-cutting refactor work the decomposition shape can't actually decompose, producing children that re-aggregate into the same hairball; (d) lose the parent ↔ child grounding link that #339 Contract C2 requires for traceability.

**Scope deliberately limited to Phase 1.** This ADR pins decomposition *triggering* and *child-spawning*. Composition orchestration — the inverse problem of merging decomposed children back together with integration verification — is Phase 3 (#338) and deferred until the FR-015 data feed accumulates real-factory evidence about which decompositions actually work.

## Decision Drivers

- A small named set of boundary types makes decomposition shape inspectable and FR-015 retrospective classification reproducible.
- Fan-out cap bounds the per-parent cost worst case (5 children × $15 = $75) and the reviewer attention worst case (5 PRs to integrate).
- Refusal criteria that route to `escalate` (per FR-009) prevent the decomposer from forcing decomposition on work that isn't actually decomposable along one of the allowed boundary axes.
- Grounding contract (child → parent reference + boundary type) is what makes the decomposition auditable from the C2 spec contract alone — no out-of-band tracking required.
- Parent-tracking contract (`## Integration Acceptance Criteria` + parent-stays-open-until-children-merge-AND-human-ticks-the-criteria) is the *only* Phase 1 protection against children that compile-and-test in isolation but don't actually compose together.

## Decision

**Allowed boundary types.** A `blueprint-ticket-decompose-light` invocation MUST decompose along **exactly one** of:

| Boundary type | Decomposes by |
|---|---|
| `bounded-context` | one child per bounded context touched by the parent |
| `architectural-layer` | one child per architectural layer (e.g., domain / application / infrastructure / interface) |
| `user-visible-feature-behavior` | one child per independently-shippable user-visible behavior |

Decomposition along any other axis is FORBIDDEN. Mixed-axis decompositions (e.g., "two children by bounded context and three by layer") are FORBIDDEN — the single axis is what makes the children's relationship to the parent inspectable.

**Fan-out cap.** Maximum **5 children per parent**. A decomposition proposal exceeding 5 children MUST refuse (route the parent to `escalate` per FR-009) rather than truncate.

**Refusal criteria.** The decomposer MUST refuse (route the parent to `escalate` per FR-009) when any of:

- The proposed children would each themselves be `large-decomposable` per FR-009 thresholds — recursive decomposition is not supported in Phase 1.
- The work is **cross-cutting refactor** (changes that fan into every bounded context regardless of axis chosen, e.g., a logging-format change, a naming-convention sweep, a dependency-version bump touching every module).
- The work is **exploratory architecture** (the parent ticket is fundamentally a design-investigation task whose output is a decision rather than code).
- No single allowed boundary type produces ≤ 5 children that collectively cover the parent scope.

**Grounding contract** (child sub-ticket bodies). Every child sub-ticket body MUST cite:

1. The **parent spec path** (e.g., `specs/2026-05-28-issue-337-factory-phase-0-foundations/`), per #339 Contract C2's child-spec convention.
2. The **boundary type** used to spawn the child (`bounded-context | architectural-layer | user-visible-feature-behavior`).
3. The **specific boundary value** for this child (e.g., `bounded-context: factory`, `architectural-layer: infrastructure`, `user-visible-feature-behavior: agent-stop cascade UI`).

**Parent-tracking contract** (parent issue body). The parent issue body MUST carry:

1. A `## Integration Acceptance Criteria` section per #339 Contract C4 enumerating the cross-child invariants that must hold once all children merge (e.g., "calling the new `/foo` endpoint produced by child A from the new client produced by child B succeeds end-to-end").
2. A `## Children` checklist enumerating each child issue by number.

The parent issue MUST remain open until:

1. **All children are merged** (their PRs closed via merge, not via close-without-merge), AND
2. **Every `## Integration Acceptance Criteria` checkbox is ticked by a human bounded-context reviewer** (per FR-011 gate-2 routing — a human in the relevant bounded-context team, not a factory bot, ticks each box).

The factory bot MUST NOT tick any checkbox in `## Integration Acceptance Criteria`. A C7 lifecycle event with `outcome: rejected` (the bot's tick attempt is rejected) and `rejection_reason: integration-criteria-bot-tick-blocked` as a non-required extension field (permitted by C7's `additionalProperties: true`) MUST be emitted if a bot tick is attempted.

**Phase 1 / Phase 3 boundary.** Phase 1 does **NOT** automate composition verification. The factory does not attempt to verify that the children's contracts compose; it relies on the human-tick contract above. **Composition orchestration is Phase 3 (#338)** — Phase 3 consumes FR-015's accumulated decomposition evidence to design automated integration verification. Until Phase 3 ships, decomposed parents are merged by human integration review.

**Implementer.** #333 (Personas + Skills) authors the `blueprint-ticket-decompose-light` skill against this ADR; #336 (GitHub Actions webhooks) carries the parent-stays-open enforcement and the bot-tick-block enforcement; #338 (Phase 3) consumes the FR-015 evidence to design composition orchestration.

## Options Considered

### Option A — Single-axis decomposition from `{bounded-context, architectural-layer, user-visible-feature-behavior}`, fan-out 5, refusal routes to escalate, human-tick integration ACs (chosen)

The decision above.

**Pros:** small named axis set makes shape inspectable; fan-out cap bounds cost and reviewer load; refusal-routes-to-escalate prevents pathological decompositions; grounding contract preserves parent ↔ child auditability via C2; human-tick integration ACs prevent silent compose-failures in Phase 1 without requiring Phase 3 to ship first; the data feed FR-015 generates is rich enough to inform Phase 3 design.

**Cons:** the three-axis enumeration is opinionated and may not match every consumer's preferred decomposition mental model. Mitigation: the three axes cover the dominant decomposition patterns observed in software (vertical-slice features, horizontal-layer refactors, business-domain splits); the four-class triage scheme already routes unfit work to `escalate`, so the cost of "wrong axis for this ticket" is bounded by escalation rather than by forced decomposition.

### Option B — Open-ended axis (decomposer picks any boundary it sees fit) (rejected)

Let the model name its own boundary type per decomposition.

**Rejected:** breaks FR-015 retrospective classification (every retrospective decomposition would need an ad-hoc boundary name); makes cross-cycle comparison impossible; obscures Phase 3 composition-design evidence by introducing per-cycle decomposition vocabulary. The fixed three-axis set is what makes the data feed useful.

### Option C — Higher fan-out cap (10+) (rejected)

Allow up to 10 children per parent.

**Rejected:** 10 × $15 = $150 worst-case per-parent cost; 10 PRs is past the threshold where human integration review reliably catches cross-child contract violations; the marginal value of children 6–10 over routing-to-escalate is low because at that fan-out the parent is almost certainly cross-cutting work that the three allowed axes don't truly decompose.

### Option D — Allow recursive decomposition (children can themselves be `large-decomposable`) (rejected)

Let the decomposer spawn `large-decomposable` children, which then trigger their own decomposition.

**Rejected:** unbounded depth multiplies cost (5^N children); composition complexity grows exponentially; the integration AC contract degrades because parent-of-parent ACs would need to compose across N levels of children. Single-level decomposition with `escalate` as the recursive-case escape valve is the only Phase 1 shape that's both auditable and bounded.

### Option E — Bot can tick integration ACs after CI passes (rejected)

Let the bot tick `## Integration Acceptance Criteria` boxes if green-CI succeeds across all children.

**Rejected:** CI green tells you the code compiles and the existing tests pass; it does not tell you that the cross-child contract holds (the contract may not be tested at all, or the test may not exist yet because it was supposed to be part of the integration step). The whole point of integration ACs is that they're the cross-cutting tests the parent specifies and the human verifies; bot-ticking collapses that into "did CI pass," which is what the existing PR review already checks. Until Phase 3 builds explicit composition-verification machinery, the bot tick provides no compliance value.

## Consequences

- Phase 1 ticket #333 authors the `blueprint-ticket-decompose-light` skill against this ADR's axis enumeration, fan-out cap, refusal criteria, and grounding contract.
- Phase 1 ticket #336 enforces the parent-stays-open rule (parent issue MUST NOT be auto-closed by child PR merges) and the bot-tick-block on `## Integration Acceptance Criteria`. The parent-stays-open enforcement is realized as a pre-close hook on every child PR whose body references a parent issue via #339 Contract C2; the hook MUST block GitHub's `closes #N` / `fixes #N` auto-close behavior whenever any `## Integration Acceptance Criteria` checkbox on the referenced parent remains unchecked. (Children themselves close normally on merge; only parent auto-close is blocked.)
- Phase 1 ticket #333 authors the canonical **bounded-context catalogue** for the blueprint instance — `factory`, `infra`, `docs`, `governance` per FR-011 / Q-3 on spec.md — as a sealed `.agents/factory/bounded-contexts.yaml` (or equivalent) artifact consumed by both the decomposition skill (this ADR) and the CODEOWNERS two-layer router (FR-011). Consumer instances override the catalogue via #339 C8 consumer overlay per FR-017.
- FR-015 retrospective classification (in `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md`) records what boundary set this ADR's policy WOULD HAVE proposed for historical `large-decomposable` tickets — Phase 3 design consumes this evidence.
- C7 lifecycle event stream (#339 Contract C7) carries the `boundary_type` and `boundary_value` fields on decomposition events; per-axis distribution is auditable from the event stream.
- Consumer instances inherit the axis enumeration, fan-out cap, refusal-routes-to-escalate, grounding contract, parent-tracking contract, and bot-tick-block identically (sealed); only the per-instance **bounded-context catalogue** is parameterized — each consumer enumerates its own bounded contexts (the blueprint instance's are `factory`, `infra`, `docs`, `governance` per FR-011 / Q-3 on spec.md).
- The user-tick integration AC contract is the load-bearing Phase 1 protection against compose-failures; **this contract MUST NOT be relaxed until Phase 3 (#338) ships verified composition orchestration**.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-010, § FR-015
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-triage-size-threshold.md`](ADR-issue-337-triage-size-threshold.md), [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md) (agent-stop cascade), [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md) (per-child scope rule)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C2 (child-spec convention), § Contract C4 (integration acceptance criteria), § Contract C7 (lifecycle event schema — decomposition `boundary_type` / `boundary_value` fields)
- Phase 1 implementers: #333 (Personas + Skills — decomposition skill), #336 (GitHub Actions webhooks — parent-stays-open + bot-tick-block enforcement)
- Phase 3 consumer: #338 (composition orchestration design)
