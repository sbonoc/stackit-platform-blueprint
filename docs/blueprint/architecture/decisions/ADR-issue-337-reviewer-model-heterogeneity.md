# ADR: Reviewer Model Heterogeneity (AI PR Reviewer Rotation)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-008)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed`.
**Amended-by:** [`ADR-issue-364-expert-persona-model.md`](ADR-issue-364-expert-persona-model.md) — the FR-008 reviewer-heterogeneity audit invariant continues to pair the `phase: implement` C7 event with the `phase: agent-pr-review` event on the same `ticket_id` and assert distinct `model` values. Under the expert-panel model the AI PR reviewer is no longer a single stage-persona — it is an 8-expert panel dispatched by `blueprint-sdd-step08-agent-pr-review` (Contract C3 row 8, structured-disagreement convergence). The audit predicate operates on the `persona` (= skill basename) and `model` fields of the orchestrator-emitted events; per-expert model assignment within the panel is governed by ADR-issue-364 § 4 and may apply per-expert routing keys (e.g., Haiku for low-stakes lenses, Sonnet/Opus for high-stakes lenses) without affecting the pairing assertion. Per-expert capacity sizing and routing-key shape land in ticket #335.

## Context

[`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md) routes implementer personas to one of three models (Opus 4.7 / Sonnet 4.6 / Haiku 4.5) by SDD step. AI PR reviewer personas — those executing `blueprint-sdd-step08-agent-pr-review` — sit a layer above the implementer: their job is to find what the implementer's model missed.

If the reviewer runs on the same model family as the implementer, the reviewer inherits the implementer's blind spots. A Sonnet implementer that misreads a spec requirement is statistically more likely to be reviewed cleanly by another Sonnet instance reading the same requirement the same way; the diversity argument that gives multi-author code review its value collapses when both authors are the same model. Worse, this homogeneity is invisible at the PR surface — every reviewer comment looks "different" but the underlying model gradients are correlated.

This ADR pins the rotation rule so the heterogeneity is structural, not optional.

## Decision Drivers

- AI reviewer value comes from being a *different* eye on the work; same-model review is theatre.
- The rotation MUST be expressible from the lifecycle event stream alone (#339 Contract C7 carries the implementer's `model` field per emitted persona event), so the factory orchestrator can resolve reviewer-model selection and the #336 C7-ingestion path can audit the resulting pair without bespoke state outside the event stream.
- Symmetric rotation (Opus ↔ Sonnet) keeps the model space simple and the rule trivially auditable from C7 events; asymmetric rules (e.g., "always review with Opus") would pay Opus prices on every step08 invocation including reviews of Sonnet-default work, which is unjustifiable.
- Haiku is intentionally **not** in the rotation: Haiku is reserved for the lightweight `step03-spec-complete` fill-in step per the router policy; the spec-step output is reviewed by human sign-offs (the canonical four phrases), not by step08 AI reviewers, so Haiku never needs to be paired with a step08 reviewer.

## Decision

**Rotation rule.** AI PR reviewer personas (executing `blueprint-sdd-step08-agent-pr-review`) MUST run on a **different model family** than the implementer persona that produced the change being reviewed.

**Pairings** (symmetric):

| Implementer model (step05) | Reviewer model (step08) |
|---|---|
| `claude-opus-4-7` | `claude-sonnet-4-6` |
| `claude-sonnet-4-6` | `claude-opus-4-7` |

**Model identifier resolution.** The identifiers in the pairings table are family/version names — not deployment IDs. Per-instance gateway-ID resolution is delegated to [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md) § Decision — Model identifier resolution. The orchestrator-side picker MUST resolve the `model` field read from the most-recent `phase: implement` C7 event AND the chosen reviewer model through the same indirection, so the rotation invariant holds at the family/version layer regardless of consumer-side alias naming.

**Enforcement.** Rotation enforcement is split across two independent points:

1. **Picker (factory orchestrator, #333).** When the orchestrator is about to invoke `blueprint-sdd-step08-agent-pr-review` for a given work item, it MUST — **before constructing the `phase: agent-pr-review` C7 event and before invoking the persona** — query the #339 Contract C7 stream for the most recent C7 event with `phase: implement` on the same work item, read its `model` field, select the opposite member of the `{claude-opus-4-7, claude-sonnet-4-6}` pair, and pass that model as the `model` parameter on the LiteLLM request AND populate it on the about-to-be-emitted C7 event's `model` field (per [`ADR-issue-337-c7-emission-mechanism.md`](ADR-issue-337-c7-emission-mechanism.md) § Orchestrator emission responsibilities — identification fields populated before persona invocation). The orchestrator MUST NOT pin the reviewer model in the persona frontmatter.
2. **Audit invariant (C7 ingestion, #336).** The #336 webhook + C7 event-ingestion path MUST observe every emitted C7 event with `phase: agent-pr-review`, pair it with the matching C7 event with `phase: implement` for the same `ticket_id`, and assert the `model` field on the `implement` event differs from the `model` field on the `agent-pr-review` event. Violations MUST: apply the `factory-escalated` label to the work item (cascading to children for decomposed parents per FR-010), post a PR comment naming the violating pair, and emit a C7 event with `outcome: rejected` + `rejection_reason: rotation-violation` (non-required extension field per C7's `additionalProperties: true`). The audit predicate is written against C7 `phase` enum values — `implement` and `agent-pr-review` — rather than the originating skill basenames (`step05-implement`, `step08-agent-pr-review`); the `step0N-` prefix is stripped from skill basenames to yield the enum value per the round-12 phase-enum-naming convention in #339 design-contracts.md § Contract C7, so the predicate matches the values that the orchestrator actually emits on the C7 stream.

LiteLLM is the routing target, not the enforcement point. The deployed LiteLLM team allowlist already rejects unknown or cross-family model strings (HTTP 401 `team_model_access_denied`); that rejection is a separate, complementary gate that catches orchestrator-side string errors but MUST NOT be relied on to satisfy the rotation invariant on its own.

**Rationale for split.** Treating the rotation as enforced inside LiteLLM by having the gateway read the C7 stream was infeasible against the deployed gateway (virtual keys are scoped to `llm_api_routes` only — no callbacks, no admin) and conflated the routing layer with the orchestration layer. The picker / audit-invariant split keeps LiteLLM stateless while preserving the structural-heterogeneity guarantee through independent observation.

**Default implementer case.** Per [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md), `step05-implement` defaults to `claude-sonnet-4-6` (Sonnet is the default tier for all personas not explicitly routed elsewhere). The rotation therefore resolves the step08 reviewer to `claude-opus-4-7` in the default case.

**Escalated implementer case.** When `step05-implement` is explicitly routed to `claude-opus-4-7` (e.g., consumer-overlay escalation for high-risk surfaces; the blueprint instance does not currently escalate step05 to Opus), the rotation resolves the step08 reviewer to `claude-sonnet-4-6`.

**Haiku-implementer case.** Not applicable — `step05-implement` is never routed to Haiku per the router policy (Haiku is reserved for `step03-spec-complete`), and step03 output is reviewed by human sign-offs rather than by step08 AI reviewers.

**Implementer.** #333 (Personas + Skills) carries the orchestrator-side picker logic that selects the reviewer model AND authors the step08 reviewer persona; #336 (Webhook + C7 ingestion) carries the audit invariant that rejects rotation violations on the C7 stream; #335 (OpenHands + LiteLLM) provides the routing target only (no rotation state on the gateway).

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

- Phase 1 ticket #333 carries the orchestrator-side picker: at step08 persona invocation, look up the most recent C7 event with `phase: implement` for the same work item, read its `model` field, select the *other* member of the `{Opus, Sonnet}` pair, and pass that model on the LiteLLM request. The step08 reviewer persona file MUST NOT pin a specific model in its frontmatter; model selection is the orchestrator's job per this ADR.
- Phase 1 ticket #336 carries the audit invariant on the C7 ingestion path: every observed C7 event with `phase: agent-pr-review` is paired with the matching C7 event with `phase: implement` for the same `ticket_id`; the pair MUST satisfy `model` on the `implement` event different from `model` on the `agent-pr-review` event. Violations trigger the `factory-escalated` label, a PR comment naming the violating pair, and a C7 event with `outcome: rejected` + `rejection_reason: rotation-violation`. The audit is an independent observer of the picker, not the picker itself; both layers are required.
- Phase 1 ticket #335 deploys the LiteLLM gateway and the team-model allowlist that constrains the picker to the sanctioned model identifiers; no rotation state lives on the gateway.
- C7 event stream pairs (the `phase: implement` event + the `phase: agent-pr-review` event for the same work item) MUST carry different `model` values; this is auditable from the event stream and any pair that violates it is a gateway-side bug.
- Telemetry (#339 Contract C7) cleanly separates implementer spend from reviewer spend; the per-cycle cost envelope for the default case (Sonnet implementer + Opus reviewer on step08) is ~$6–11, within the FR-007 $15 ceiling.
- Consumer instances inherit this rule identically (sealed); the rotation always resolves over whichever model the consumer's implementer is routed to per their own router-policy overlay.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-008
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md), [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (lifecycle event schema — `model` field), § Contract C3 (OpenHands ↔ persona mapping)
- Phase 1 implementers: #333 (Personas + Skills — step08 reviewer persona + orchestrator-side picker), #336 (Webhook + C7 ingestion — audit invariant), #335 (OpenHands + LiteLLM — routing target only)
