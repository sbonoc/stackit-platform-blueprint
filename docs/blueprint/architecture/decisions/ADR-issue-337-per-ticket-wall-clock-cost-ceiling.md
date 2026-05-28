# ADR: Per-Ticket Wall-Clock + Cost Ceiling

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-007)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `parameterized` (the existence of the cap and the pause/label/comment semantics are identical and sealed; the numeric values are NOT in FR-017(b) and consumers are permitted to override via the #339 C8 consumer overlay schema).

## Context

The factory invokes LLM models on every SDD step transition and may rerun steps under FR-006 (up to 2 reject-reruns per step type). Without a hard per-ticket ceiling, a pathological loop — a model that disagrees with its own previous step output, a degenerate decomposition that produces high-cost children, a failed step01 intake that triggers expensive reruns — could consume arbitrary spend before any human notices. The rerun cap (FR-006) bounds *rerun-driven* spend but does not bound *single-run* spend on a high-cognitive-load ticket; the two mechanisms are complementary.

The ceiling exists to make factory spend **observable and bounded** at the unit of work the user pays per: one issue, one child, one PR cycle.

## Decision Drivers

- The ceiling MUST be expressible in units the user already reasons about — wall-clock minutes (operational cost) and USD (cash cost).
- Decomposed parents MUST NOT be penalized for legitimate fan-out: child ceilings sum to multi-child total, but that total is the same as N independently-budgeted tickets.
- Ceiling-hit MUST pause the work item (not silently continue, not silently kill) so a human can decide whether to raise the ceiling, abandon, or re-scope.
- The escalation pattern (`factory-paused-ceiling` label + comment) MUST be distinguishable from the rerun-cap escalation (`factory-escalated` label per FR-006) so PR-queue triage routes each to the right intervention.
- Concrete numeric values are calibratable from the FR-014 baselines once the first 30 cycles accumulate; consumer instances tune their own values.

## Decision

**Ceiling values for the blueprint instance** (per Q-1 on spec.md):

| Dimension | Value | Scope |
|---|---|---|
| Wall-clock | **90 minutes** | per work item / per child |
| LLM cost | **$15 USD** | per work item / per child |

**Scope rule.** For decomposed parents (via `blueprint-ticket-decompose-light` per FR-010), the ceiling MUST apply per child issue **independently** — children do not sum against the parent. The parent issue itself has its own ceiling that covers only the work executed against the parent issue (typically: triage + decomposition + integration verification deferred to Phase 3). This prevents legitimate fan-out from triggering false ceiling-hits.

**Ceiling-hit response.** When either ceiling is exceeded for a work item, the factory bot MUST:

1. **Pause the work item** — halt in-flight persona invocations within the same 60s window required by `agent-stop` (per [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md)); emit a C7 lifecycle event with `outcome: ceiling-paused`.
2. **Apply the `factory-paused-ceiling` label** to the issue.
3. **Post a PR comment** naming **which ceiling was exceeded** (wall-clock or cost), the **measured value**, the **breakdown by SDD step** (so the human reviewer can see where spend went), and the **un-pause procedure** (apply `agent-resume` label after raising the ceiling via overlay update OR re-scoping the ticket).

**Implementer.** #336 (GitHub Actions webhooks) carries the ceiling check, label/comment actions, and pause action. The C7 event stream (#339 Contract C7) carries the per-step cost/duration measurements that the ceiling check sums.

## Options Considered

### Option A — 90 min wall-clock + $15 USD, per-work-item / per-child scope, pause+label+comment on hit (chosen)

The decision above.

**Pros:** bounds worst-case full-SDD cycle envelope (~40–60 min, ~$5–10 on Sonnet 4.6 default per [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md)) with ~50% headroom for Opus 4.7 escalations on step01/step04 without false halts; child-scoped variant preserves the cost benefit of legitimate decomposition (FR-010 cap of 5 children means worst-case decomposed parent costs 5×$15 = $75, still bounded); pause-not-kill preserves the work-in-progress for human inspection; calibratable from FR-014 baselines.

**Cons:** numeric values are estimates pre-real-factory; first 30 cycles may reveal the headroom is too tight or too loose. Mitigation: values are explicitly parameterized via #339 C8 consumer overlay — consumers (including the blueprint instance itself, as a self-consumer) can tune without ADR amendment.

### Option B — Summed ceiling across all children of a decomposed parent (rejected)

Apply $15 to the parent total, irrespective of child count.

**Rejected:** punishes legitimate fan-out — a 5-child decomposition with each child averaging $4 would trigger a false ceiling-hit despite each child being individually well-scoped. The economic argument for decomposition collapses if children are budgeted as a single pooled spend.

### Option C — Cost ceiling only, no wall-clock ceiling (rejected)

Drop the wall-clock dimension; rely on cost alone.

**Rejected:** a stuck factory pass (e.g., LiteLLM gateway timing out and the bounded retry per FR-001 also timing out) consumes wall-clock without consuming cost; an oncall reviewer waiting for a Draft PR has no signal that the work is stuck. Wall-clock catches operational stuckness; cost catches budget stuckness. The two are uncorrelated failure modes and need separate ceilings.

### Option D — Silent kill on ceiling-hit, no human-reviewable pause (rejected)

Terminate the run; reviewer notices via missing-PR signal.

**Rejected:** kills the work-in-progress evidence the reviewer needs to decide whether to raise the ceiling, abandon, or re-scope; conflates the "ceiling hit" signal with the "factory crashed" signal in telemetry; reduces the rate at which the team can calibrate the right ceiling values. Pause-and-surface is the cheaper-to-recover-from default.

## Consequences

- Phase 1 ticket #336 implements the per-(issue × step) cost+duration accumulator (summed over the C7 event stream), the ceiling check at every persona-completion boundary, and the pause+label+comment action.
- Per-cycle cost telemetry (FR-012 `dashboard target` per Q-4 on spec.md = stackit-managed-grafana) provides the calibration signal — after 30 cycles, ceiling values are re-evaluated against the actual distribution and adjusted via consumer overlay if warranted.
- The `factory-paused-ceiling` label is the canonical "this ticket exhausted its budget; human un-pause needed" signal; reviewers MUST filter for it as a routine PR-queue triage step (distinct from `factory-escalated` per FR-006, which signals "needs re-scope" rather than "needs un-pause").
- Consumer instances inherit the cap structure and pause-label-comment semantics identically (sealed); the numeric values are parameterized — consumers declare their own `spec.factory_contract.ceilings.wall_clock_minutes` and `spec.factory_contract.ceilings.cost_usd` via #339 C8 consumer overlay.
- Interaction with FR-006 rerun cap: rerun-cap-hit typically fires earlier than ceiling-hit (2 reruns at $5–10 each ≈ $10–20, but the cap fires at trigger-time before the third rerun runs) and is the preferred signal for quality issues; ceiling-hit fires for non-rerun cost paths (pathological single-run spend, decomposition gone wide, gateway-retry storms).

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-007, § Clarifications Q-1
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-reject-rerun-cap.md`](ADR-issue-337-reject-rerun-cap.md), [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md), [`ADR-issue-337-light-decomposition-policy.md`](ADR-issue-337-light-decomposition-policy.md), [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (lifecycle event schema — cost/duration fields), § Contract C8 (consumer overlay)
- Phase 1 implementer: #336 (GitHub Actions webhooks)
