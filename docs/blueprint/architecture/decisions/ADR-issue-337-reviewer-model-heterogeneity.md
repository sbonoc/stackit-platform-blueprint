# ADR: Reviewer Model Heterogeneity (AI PR Reviewer Rotation)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-008)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed`.

## Context

[`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md) routes implementer personas to one of three models (Opus 4.7 / Sonnet 4.6 / Haiku 4.5) by SDD step. AI PR reviewer personas — those executing `blueprint-sdd-step08-agent-pr-review` — sit a layer above the implementer: their job is to find what the implementer's model missed.

If the reviewer runs on the same model family as the implementer, the reviewer inherits the implementer's blind spots. A Sonnet implementer that misreads a spec requirement is statistically more likely to be reviewed cleanly by another Sonnet instance reading the same requirement the same way; the diversity argument that gives multi-author code review its value collapses when both authors are the same model. Worse, this homogeneity is invisible at the PR surface — every reviewer comment looks "different" but the underlying model gradients are correlated.

This ADR pins the rotation rule so the heterogeneity is structural, not optional.

## Decision Drivers

- AI reviewer value comes from being a *different* eye on the work; same-model review is theatre.
- The rotation MUST be expressible from the lifecycle event stream alone (#339 Contract C7 carries the implementer's `model` field per emitted persona event), so the LiteLLM gateway can resolve reviewer-model selection without bespoke state.
- Symmetric rotation (Opus ↔ Sonnet) keeps the model space simple and the rule trivially auditable from C7 events; asymmetric rules (e.g., "always review with Opus") would pay Opus prices on every step08 invocation including reviews of Sonnet-default work, which is unjustifiable.
- Haiku is intentionally **not** in the rotation: Haiku is reserved for the lightweight `step03-spec-complete` fill-in step per the router policy; the spec-step output is reviewed by human sign-offs (the canonical four phrases), not by step08 AI reviewers, so Haiku never needs to be paired with a step08 reviewer.

## Decision

**Rotation rule.** AI PR reviewer personas (executing `blueprint-sdd-step08-agent-pr-review`) MUST run on a **different model family** than the implementer persona that produced the change being reviewed.

**Pairings** (symmetric):

| Implementer model (step05) | Reviewer model (step08) |
|---|---|
| `claude-opus-4-7` | `claude-sonnet-4-6` |
| `claude-sonnet-4-6` | `claude-opus-4-7` |

**Enforcement.** The LiteLLM gateway MUST enforce the rotation by reading the implementer `model` field from the lifecycle event stream (#339 Contract C7) for the corresponding `step05-implement` event on the same work item, and selecting the reviewer model accordingly. No bespoke rotation state outside the gateway and the event stream.

**Default implementer case.** Per [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md), `step05-implement` defaults to `claude-sonnet-4-6` (Sonnet is the default tier for all personas not explicitly routed elsewhere). The rotation therefore resolves the step08 reviewer to `claude-opus-4-7` in the default case.

**Escalated implementer case.** When `step05-implement` is explicitly routed to `claude-opus-4-7` (e.g., consumer-overlay escalation for high-risk surfaces; the blueprint instance does not currently escalate step05 to Opus), the rotation resolves the step08 reviewer to `claude-sonnet-4-6`.

**Haiku-implementer case.** Not applicable — `step05-implement` is never routed to Haiku per the router policy (Haiku is reserved for `step03-spec-complete`), and step03 output is reviewed by human sign-offs rather than by step08 AI reviewers.

**Implementer.** #335 (OpenHands + LiteLLM) carries the rotation logic into the gateway configuration; #333 (Personas + Skills) authors the step08 reviewer persona that the gateway selects the model for.

## Options Considered

### Option A — Symmetric Opus ↔ Sonnet rotation enforced at the gateway (chosen)

The decision above.

**Pros:** structural heterogeneity guarantee; reviewer-model selection is one C7 query away (no separate state); symmetric rule is trivially auditable ("did this event pair differ in `model` field" is a 5-line check); Haiku stays out of the rotation cleanly because it never reviews step08 output.

**Cons:** marginal cost increase versus Sonnet-on-Sonnet review (Opus reviews of Sonnet implementations cost ~3× Sonnet review). Mitigation: step08 token budget per review is small (the reviewer reads the diff, not the full codebase); the cost differential is bounded and stays well within the FR-007 ceiling envelope.

### Option B — Always review with Opus regardless of implementer (rejected)

Skip rotation; pin step08 to Opus always.

**Rejected:** pays Opus prices on every review including reviews of step05 Sonnet defaults; on a step that fires up to 1× per work item (no rerun cap on step08 itself), this would cost 30–50% of the per-cycle envelope on review alone. The heterogeneity argument is the only argument that justifies cost differential; Opus-everywhere wins on capability but loses the heterogeneity property when the implementer is already Opus.

### Option C — Random rotation among the three tiers (rejected)

Pick a random model from `{Opus, Sonnet, Haiku}` for the reviewer.

**Rejected:** Haiku reviews of Opus-implemented work would catastrophically under-perform — Haiku does not have the capability to find errors Opus didn't notice in the first place. Random rotation only makes sense among models of comparable capability; the Opus ↔ Sonnet pair is the only such pair we have.

### Option D — Same-model review with a different system prompt (rejected)

Use the same model but prompt it differently for review ("read this critically", "find errors", etc.).

**Rejected:** does not address the underlying gradient-correlation problem; reviewer comments look diverse but the model weights are identical, so missed-bug patterns are correlated. The diversity must come from the model family, not from prompt phrasing.

## Consequences

- Phase 1 ticket #335 implements the gateway-side rotation: at step08 persona invocation, look up the most recent `step05-implement` C7 event for the same work item, read its `model` field, select the *other* member of the `{Opus, Sonnet}` pair.
- Phase 1 ticket #333 authors the step08 reviewer persona — the persona file MUST NOT pin a specific model in its frontmatter; model selection is the gateway's job per this ADR.
- C7 event stream pairs (`step05-implement` event + `step08-agent-pr-review` event for the same work item) MUST carry different `model` values; this is auditable from the event stream and any pair that violates it is a gateway-side bug.
- Telemetry (#339 Contract C7) cleanly separates implementer spend from reviewer spend; the per-cycle cost envelope for the default case (Sonnet implementer + Opus reviewer on step08) is ~$6–11, within the FR-007 $15 ceiling.
- Consumer instances inherit this rule identically (sealed); the rotation always resolves over whichever model the consumer's implementer is routed to per their own router-policy overlay.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-008
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md), [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (lifecycle event schema — `model` field), § Contract C3 (OpenHands ↔ persona mapping)
- Phase 1 implementers: #333 (Personas + Skills — step08 reviewer persona), #335 (OpenHands + LiteLLM — rotation enforcement)
