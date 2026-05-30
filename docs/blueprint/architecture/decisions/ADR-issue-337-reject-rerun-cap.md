# ADR: Reject-Rerun Cap

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-006)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed` (listed explicitly in FR-017(b)).

## Context

When a reviewer rejects factory-produced work — by applying an `agent-rerun`-style label or by posting a rejection comment that triggers re-execution — the factory rolls the affected SDD step over and tries again. Without a cap, a persistently misaligned spec or implementation can consume the per-ticket cost ceiling (`$15 USD per work item / per child` per [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md)) in rerun spend alone, hide a deeper "this ticket shouldn't be auto-factored" signal, and exhaust reviewer attention on the same ground.

The cap exists not to bound cost (the FR-007 ceiling already does that) but to **convert a quality signal into a routing signal**: two failed reruns of the same step is strong evidence that the ticket needs human re-scoping rather than another factory pass.

## Decision Drivers

- Two failures on the same step on the same ticket is empirically rare for legitimately auto-factorable work; when it happens it's a routing signal, not a model-quality signal.
- Counters MUST be independent per step type — two `step03-spec-complete` rejections do not exhaust the budget for `step05-implement` reruns on the same ticket, because the failure modes are unrelated.
- Escalation MUST be loud and label-driven so reviewers can filter the PR queue for "needs human re-scope" without scanning comments.
- Escalation MUST stop further reruns on the affected step type — silently allowing a third rerun after escalation would defeat the routing-signal purpose.

## Decision

**Cap value.** The maximum reject-rerun count is **2** before factory escalation.

**Definition of "reject-rerun".** A reject-rerun is a factory-driven re-execution of any SDD step triggered by a reviewer-applied `agent-rerun` (or equivalent) label or comment. Counters MUST be **per work-item per step type** — e.g., two `step03-spec-complete` rerolls and two `step05-implement` rerolls on the same work item are independent counters and neither exhausts the other.

**Escalation operational definition.** When the cap is reached on a step type for a work item, the factory bot MUST:

1. **Apply the `factory-escalated` label** to the issue (and to any open child issues for decomposed parents per FR-010).
2. **Post a PR comment** naming the cap reached, the affected step type, and the rerun history (timestamps + which reviewer triggered each rerun).
3. **Stop accepting further reruns on the affected step type** for the lifetime of that work item — additional `agent-rerun`-style triggers on that step MUST be ignored (no-op) and MUST emit a C7 lifecycle event with `outcome: rejected` (the rerun trigger is rejected) and `rejection_reason: rerun-cap-exceeded` as a non-required extension field (permitted by C7's `additionalProperties: true`) so the audit trail preserves both the schema-valid outcome and the specific cap-hit reason.

**Implementer.** #336 (GitHub Actions webhooks) carries the counter state (keyed by issue number + step type), the cap check, and the escalation actions.

## Options Considered

### Option A — Cap at 2, per work-item per step type, with `factory-escalated` label + comment + stop (chosen)

The decision above.

**Pros:** independent step counters preserve the recovery path for unrelated failures; cap of 2 catches the routing-signal pattern early without burning the FR-007 ceiling on reruns; label-driven escalation is filterable from the PR queue; loud comment carries the rerun history so the escalation reviewer can act without re-deriving it.

**Cons:** counter state lives in #336's webhook layer and must survive webhook-handler restarts. Mitigation: the counter is reconstructible from the C7 lifecycle event stream (every rerun emits an event) — a cold start can replay the stream to rebuild the counter.

### Option B — Single global cap across all step types (rejected)

Cap at 2 reject-reruns total per work item, regardless of which step.

**Rejected:** entangles unrelated failure modes — a spec-step disagreement that took 2 reruns to resolve would leave zero budget for an unrelated impl-step bug, forcing escalation on the wrong step. Per-step counters preserve the recovery path for legitimately decoupled issues.

### Option C — Cap at higher value (3 or 5) (rejected)

Allow more reruns before escalation.

**Rejected:** at $15 ceiling and ~$5–10 typical per-cycle cost, three full reruns at the same step type would alone consume the ceiling — escalation would never fire in time to prevent ceiling-hit. Cap of 2 leaves headroom for the original run + 2 reruns + a small partial run at the next step before ceiling.

### Option D — No cap; rely solely on FR-007 cost ceiling (rejected)

Let the cost ceiling alone bound rerun spend.

**Rejected:** ceiling-hit is a louder, more disruptive signal than rerun-cap-hit (`factory-paused-ceiling` requires human un-pause, whereas `factory-escalated` requires human re-scope) — using cost ceiling for what is fundamentally a quality-signal trigger conflates two different failure modes in telemetry. Rerun cap fires earlier and points at the right intervention.

## Consequences

- Phase 1 ticket #336 implements the per-(issue × step) counter, the cap check at rerun-trigger time, and the three-part escalation action (label + comment + step lockout).
- C7 lifecycle event stream (#339 Contract C7) carries every rerun event and the cap-hit event (with `outcome: rejected` + `rejection_reason: rerun-cap-exceeded`); counter state is reconstructible from the stream on cold start.
- The `factory-escalated` label is the canonical "this ticket needs human re-scope" signal — reviewers MUST filter for it as a routine PR-queue triage step.
- Consumer instances inherit the cap value, the per-(work-item × step) counter shape, and the escalation actions identically (sealed per #339 C8 FR-017(b)).
- Interaction with FR-007 cost ceiling: rerun-cap-hit fires earlier than ceiling-hit on average and is the preferred signal; ceiling-hit remains the backstop for legitimate single-run cost overruns or non-rerun cost paths (e.g., pathologically long step01 intake).
- **Check-order on every persona-invocation trigger.** #336 MUST evaluate FR-006 rerun-cap exhaustion BEFORE evaluating the FR-007 per-ticket ceiling, so the quality-signal escalation (`factory-escalated`) fires before the budget-signal pause (`factory-paused-ceiling`) when both conditions are simultaneously true on the same invocation. Mirrors the matching check-order rule in [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md).

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-006
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md), [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (lifecycle event schema — `outcome` enum)
- Phase 1 implementer: #336 (GitHub Actions webhooks)
