# ADR: LLM Model Router Policy (Per-Step Three-Tier Routing)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-001)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed` (consumers MUST inherit identically; consumers are permitted to shadow only the per-instance LiteLLM access configuration declared by #339 Contract C8 FR-014).

## Context

The factory invokes Claude models through a single LiteLLM gateway per #339 Contract C8 § External service. Without an explicit router policy, every persona invocation would resolve to whatever model the gateway happens to default to — yielding a uniform cost/latency profile that under-serves the highest-cognitive-load SDD steps (`step01-intake`, `step04-plan-slicer`) and over-pays for the lowest-cognitive-load step (`step03-spec-complete`).

The factory's per-ticket cost ceiling is `$15 USD per work item / per child` (Q-1 in spec.md; see [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md)). Hitting that ceiling reliably requires concentrating Opus 4.7 cost only where it materially improves outcomes.

## Decision Drivers

- Concentrate the highest-capability model only on steps where it materially affects outcome quality.
- Default the remaining steps to the mid-tier model so the cycle cost envelope stays well within the FR-007 ceiling.
- Keep the routing rule expressible as a single LiteLLM gateway config so the implementer (#335) does not need bespoke model-selection logic.
- Stay internally consistent with the reviewer-heterogeneity rule (FR-008) — step08 reviewers are governed by FR-008's rotation, not by this FR's table.
- Sovereignty/ZDR is enforced upstream at the LiteLLM gateway (FR-004); the router policy MUST NOT introduce a separate egress path.

## Decision

Three-tier per-step routing scheme:

| Tier | Model | Routed SDD steps |
|---|---|---|
| Escalation | `claude-opus-4-7` | `blueprint-sdd-step01-intake`, `blueprint-sdd-step04-plan-slicer` |
| Default | `claude-sonnet-4-6` | every persona not explicitly routed elsewhere |
| Lightweight | `claude-haiku-4-5` | `blueprint-sdd-step03-spec-complete` |

**Routing rule expression.** Routing rules MUST be expressed against the persona file basename plus the `## Activation Triggers` section per #339 Contract C3 (OpenHands ↔ persona mapping). No bespoke router logic — LiteLLM gateway configuration carries the entire mapping.

**Model identifier resolution.** The identifiers in the table above (`claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`) are family/version names — not deployment IDs. The orchestrator MUST resolve each family/version name to a concrete deployed gateway model ID via the per-instance LiteLLM access configuration declared by #339 Contract C8 FR-014 (model allowlist). The blueprint instance's deployed gateway today exposes the three sanctioned models as `claude-opus-4-7-data-hub-europe`, `claude-sonnet-4-6-data-hub-europe`, and `claude-haiku-4-5-data-hub-europe` (EU + ZDR posture per FR-004), and the team-model allowlist on the issued virtual key MUST contain exactly these three entries; consumer instances MUST declare the equivalent allowlist for their own gateway deployment and MUST NOT pin the suffix shape in any blueprint-owned artifact. This indirection keeps this ADR deployment-agnostic and bounds the rotation surface (FR-008) to the family/version pair regardless of how the gateway happens to name its aliases.

**Step08 (reviewer) governance.** Personas executing `blueprint-sdd-step08-agent-pr-review` are governed by [`ADR-issue-337-reviewer-model-heterogeneity.md`](ADR-issue-337-reviewer-model-heterogeneity.md) rather than by this ADR. In the default-implementer case (`step05` on `claude-sonnet-4-6`), the rotation resolves the step08 reviewer to `claude-opus-4-7`.

**Fallback behaviour.** On gateway 5xx or model-unavailable: a single bounded retry on the same model, then fail the persona invocation upward. No silent fallback to a different model — silent fallbacks would mask FR-008 reviewer-heterogeneity rotation violations and conflate model-cost telemetry.

**Implementer.** #335 (OpenHands + LiteLLM) carries the routing rules into the LiteLLM gateway configuration.

## Options Considered

### Option A — Three-tier per-step routing (chosen)

Step01 (highest-cognitive-load: vague → structured translation) and step04 (architectural decomposition) on Opus; step03 (structured fill-in from intake artifacts) on Haiku; remainder on Sonnet.

**Pros:** concentrates Opus cost on the two steps where it measurably moves the outcome; Haiku on step03 saves ~30% of per-cycle cost versus a Sonnet-everywhere baseline; matches the FR-007 cost ceiling envelope comfortably.

**Cons:** introduces three model identifiers in the gateway config rather than one. Mitigation: the three-line LiteLLM mapping is trivial to maintain.

### Option B — Sonnet-everywhere (rejected)

Default the entire factory to `claude-sonnet-4-6`.

**Rejected:** step01 quality on vague intake materially affects every downstream step; under-investing here pushes failure modes into step04 (where they cost more to correct) or into PR-review reject/rerun cycles (capped at 2 per FR-006, but each rerun consumes the FR-007 ceiling).

### Option C — Opus-on-step01-and-step04 only, Sonnet for step03 (the original proposal before user feedback)

Two-tier: Opus on step01 + step04; Sonnet on everything else including step03.

**Rejected:** over-pays for step03, which is structured fill-in from intake artifacts where the high-ambiguity work has already been resolved at step01. Sonnet quality on step03 is indistinguishable from Haiku for this specific narrow task; the cost difference is real.

### Option D — Per-persona routing (rejected)

Route by individual persona file rather than by SDD step.

**Rejected:** doubles config surface (~30 personas vs ~7 SDD steps) without quality benefit — personas within a single SDD step have correlated cognitive-load profiles.

## Consequences

- Phase 1 ticket #335 reads this ADR to generate the LiteLLM gateway routing rules. The mapping is the entire router state — no separate routing layer is added.
- FR-008 reviewer-heterogeneity rotation stays internally consistent: step03 Haiku output is reviewed by human sign-offs (canonical four phrases), not by step08 AI reviewers, so Haiku does not enter the FR-008 rotation.
- Per-cycle cost (Sonnet-default with Opus on two steps, Haiku on one step) is estimated at $5–10 USD, leaving ~50% headroom against the FR-007 $15 ceiling for legitimate reruns and step variance.
- Telemetry (#339 Contract C7 `model` field) cleanly attributes spend per persona invocation; the three-tier mapping is auditable from the lifecycle event stream without bespoke instrumentation.
- Consumer instances MUST inherit this rule identically — they are permitted to shadow only the per-instance LiteLLM access configuration (gateway URL, auth secret ref, model allowlist) declared by #339 Contract C8 FR-014.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-001
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-reviewer-model-heterogeneity.md`](ADR-issue-337-reviewer-model-heterogeneity.md), [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md), [`ADR-issue-337-sovereignty-zdr-posture.md`](ADR-issue-337-sovereignty-zdr-posture.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C3 (OpenHands ↔ persona mapping), § Contract C8 § External service — LiteLLM access configuration (FR-014)
- Phase 1 implementer: #335 (OpenHands + LiteLLM)
