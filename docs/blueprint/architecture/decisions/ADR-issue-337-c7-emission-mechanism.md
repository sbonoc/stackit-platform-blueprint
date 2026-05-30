# ADR: C7 Lifecycle Event Emission Mechanism

**Status:** approved
**Date:** 2026-05-30
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-019)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed`.

## Context

[`design-contracts.md`](../../autonomous-factory/design-contracts.md) § Contract C7 pins **what** must be emitted (the nine-field lifecycle event schema), **where** (a durable, replayable bus — STACKIT Managed RabbitMQ stream queues per FR-013 / Q-5), and **when** (every persona phase transition during autonomous execution). It deliberately leaves **how** open, on the premise that the implementation mechanism is a Phase 1 detail.

After the Phase 0 ADR set was complete it became clear that "how" is in fact load-bearing for correctness, not just a Phase 1 detail. The earlier ADRs that say "MUST emit a C7 event with X" — [`reject-rerun-cap`](ADR-issue-337-reject-rerun-cap.md), [`per-ticket-wall-clock-cost-ceiling`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md), [`trigger-authorization-model`](ADR-issue-337-trigger-authorization-model.md), [`triage-size-threshold`](ADR-issue-337-triage-size-threshold.md), [`light-decomposition-policy`](ADR-issue-337-light-decomposition-policy.md), and [`reviewer-model-heterogeneity`](ADR-issue-337-reviewer-model-heterogeneity.md) — collectively require that emission happens reliably for events whose triggering condition is observable only by deterministic infrastructure (a webhook handler observing a label, a budget-watcher observing a LiteLLM 429, an audit invariant pairing two C7 events). If the implementation mechanism allows an LLM-driven persona to be the emitter for any of these clauses, the persona becomes a single point of failure for an event whose absence would silently corrupt the metrics dashboard, the rerun-cap counter, the cost ceiling, the rotation audit, and the triage class distribution.

The factory's correctness rests on the C7 event stream being a complete record of what happened. A missing event is indistinguishable from an event that never occurred. LLM hallucination or instruction-following lapses cannot be the failure mode that produces missing events.

## Decision Drivers

- Every C7 event whose emission is required by a prior #337 ADR is something deterministic non-LLM code can observe directly — the orchestrator wraps every persona invocation (so phase boundaries and outcome are knowable from process state, exit code, and the persona's structured output artifact), and the webhook handler observes every GitHub event (so label-driven, trigger-driven, and bot-action-driven events are knowable from the webhook payload). No prior ADR requires emission of an event that only an in-flight persona could observe.
- LLM-driven emission is a hallucination surface: a persona instructed to "emit a C7 event at phase end" can skip the step silently and produce a complete-looking work product. Detection requires cross-checking the persona output against the event stream — circular if the event stream is the source of truth.
- The C7 contract already requires async fire-and-forget transport with subscriber-position tracking on the subscriber side. This means the emitter can be a small, stable, well-tested component independent of the persona runtime — the emitter does not have to be co-located with the persona to satisfy any C7 transport guarantee.
- Personas already produce structured work products that the SDD lifecycle reviews (specs, plans, PRs, triage classifications). Routing emission through deterministic validation of those products gives the same audit signal as in-persona emission but with provenance the orchestrator can attest to.
- Decoupling the persona from the bus removes a security blast radius (no persona ever holds RabbitMQ credentials) and an evolvability cost (C7 schema changes touch the orchestrator and the webhook handler, not every persona file).

## Decision

**Personas MUST NOT emit C7 lifecycle events.** Persona files MUST NOT import a RabbitMQ client, MUST NOT receive bus credentials via ESO or any other secret-projection mechanism, and skill runbooks MUST NOT contain any "emit a C7 event" directive at the persona level. The persona's output contract is the persona's only emission affordance toward C7.

**Two — and only two — emitter components exist on the factory data plane.** Every C7 event on the bus originates from one of:

1. **The factory orchestrator (#333)** — a persistent Deployment in the `autonomous-factory` namespace on the SKE foundation cluster control-plane pool, co-located with the OpenHands Agent Server. The orchestrator is the **single entry point** for autonomous-execution persona invocations: every autonomous trigger flows through the webhook handler (#336) to the orchestrator, the orchestrator invokes OpenHands, and the orchestrator emits the phase-boundary C7 events around the invocation.

2. **The factory webhook handler (#336)** — the GitHub Actions reusable workflows + the in-cluster webhook receiver shipped under Contract C8. The webhook handler emits C7 events for every event whose triggering condition is a GitHub event (label applications, trigger-comment posts, bot-action edits, sign-off comments, PR merges) that the orchestrator does not directly observe, AND for events produced by the #336 C7 ingestion audit invariant (rotation-violation, future schema-violation detections).

**Orchestrator emission responsibilities (the canonical list).**

Each phase boundary produces **EXACTLY ONE** atomic C7 event. The orchestrator constructs the event before invoking the persona, populating the identification fields (`phase`, `persona`, `model` resolved per FR-001 + FR-008 picker, `rerun_round` derived from prior C7 events, `owner_team` snapshotted from the issue at `phase: intake`, `ticket_id`, `parent_ticket_id`, `timestamp`, `emitter: orchestrator`, and the derived `event_id`). It then invokes the persona, awaits exit, and populates the outcome fields (`outcome` plus extension fields) before publishing the event to the durable bus. The idempotency key — `event_id = sha256(ticket_id|phase|rerun_round|emitter)` — carries no `phase-start` / `phase-end` discriminator: each phase boundary maps to one event, not two. The four derivation inputs are all required C7 schema fields (the `event_id` and `emitter` fields were promoted to required in #339 round-13 so the formula is derivable from declared fields; `ticket_id` is the schema-declared work-item identifier — earlier ADR prose used `work_item_id` for the same identifier, but #339 round-13 standardized terminology on `ticket_id` to match the sealed schema field name). The table below pins the **outcome-decision rules** that determine which `outcome` value (and which extension fields) are populated on that single event; the rows do NOT describe separate emissions.

| Outcome-decision condition observed at persona exit | Outcome value + extension fields populated on the single C7 event | Source ADR |
|---|---|---|
| Persona process exited cleanly AND output validates against the skill runbook's output schema | `outcome: success`, plus any extension fields derived from the persona's structured output (e.g., `triage_class` from the triage persona) | C7 schema; FR-009 (triage_class) |
| Persona process exited cleanly BUT output failed schema validation | `outcome: rejected`, `rejection_reason: malformed-output` (non-required extension field per C7 `additionalProperties: true`) | C7 schema |
| Persona process crashed or exceeded its skill runbook wall-clock cap | `outcome: rejected`, `rejection_reason: persona-crash` or `persona-timeout` | C7 schema |
| LiteLLM returned HTTP 429 indicating cost ceiling hit | `outcome: human-handoff`, `pause_reason: ceiling-hit` | FR-007 |

**Webhook handler emission responsibilities (the canonical list).**

| Triggering condition | Webhook handler emits | Source ADR |
|---|---|---|
| Authorized actor applies `agent-ready` to a work item | `trigger-accepted` work message published onto a RabbitMQ work queue that the orchestrator subscribes to (this is NOT a C7 event — it is the trigger-handoff transport) | FR-003 |
| `agent-ready` applied to an `escalate`-classified work item | `phase: intake`, `outcome: human-handoff`, `escalation_reason: escalate-class-blocked` | FR-009 |
| `agent-stop` applied (in-flight invocations aborted within 60s) | `outcome: human-handoff` on every aborted persona's C7 stream record | FR-003 |
| `agent-rerun` applied AFTER the FR-006 rerun cap has been reached on that step | `outcome: rejected`, `rejection_reason: rerun-cap-exceeded` | FR-006 |
| Factory bot attempts to tick a checkbox in a parent issue's `## Integration Acceptance Criteria` | `outcome: rejected`, `rejection_reason: integration-criteria-bot-tick-blocked` | FR-010 |
| C7 ingestion audit invariant detects `step05.model == step08.model` for paired events | `outcome: rejected`, `rejection_reason: rotation-violation` | FR-008 |

**Skill runbook output contract.** Every skill runbook under `.agents/skills/<name>/SKILL.md` that is invoked by an autonomous-execution persona MUST declare a **machine-parseable "Required Output Schema"** section in addition to the existing human-readable "Required Report Format." The schema MUST be a JSON Schema document expressed as a fenced ```yaml jsonschema``` code block. The persona's final output MUST contain a fenced ```yaml output``` (or ```json output```) block matching that schema. The orchestrator validates this block and uses it as the input for the `outcome` and any extension fields on the `phase-end` C7 event. Schema authoring is a #333 implementation deliverable — Phase 0 does not author the schemas; this ADR pins the contract that #333 MUST honor.

**Idempotency and replay.** The orchestrator MUST dedupe triggers on `(ticket_id, trigger_label, trigger_event_timestamp)` so that GitHub webhook retries do not produce duplicate persona invocations. The dedupe horizon MUST be at least the longest expected persona wall-clock cap (per FR-007). Cold-start state for the dedupe cache MUST be reconstructible from the C7 event stream within the FR-013 / Q-5 13-month retention window.

**Local execution exemption (unchanged from C7).** This ADR applies exclusively to autonomous execution. Human-assisted local execution (developer invoking SDD skill runbooks via Claude Code / any local CLI) emits no C7 events, because the orchestrator and webhook handler are not part of the local Docker Desktop runtime per SDD-C-014. Local runs remain directly observable by the developer.

**LiteLLM, the OpenHands Agent Server, and workspace pods are all NON-emitters.** LiteLLM is a routing target only. OpenHands runs the persona session but does not hold bus credentials and does not emit C7 events on the persona's behalf. The ephemeral workspace pods that execute personas under OpenHands hold no bus credentials.

## Options Considered

### Option A — Orchestrator + webhook handler are the only emitters (chosen)

The decision above. Two stable components, neither of which is an LLM. Every emission requirement in the #337 ADR set is satisfiable from what these two components can directly observe.

**Pros:** zero LLM hallucination surface on emission completeness; security blast radius for bus credentials is two pods on the control-plane pool; C7 schema evolution touches two codebases not eight skill runbooks; aligns with the existing operational profile (the orchestrator is the same shape as the OpenHands server itself per #335).

**Cons:** the orchestrator must be the only autonomous-execution entry point — running OpenHands directly outside the orchestrator (e.g., a manual debugging session) produces no C7 events. Mitigation: the C7 contract already exempts non-autonomous execution; #335 deploys OpenHands without a public endpoint outside the orchestrator's network path, so unauthorized direct invocation is contained by network policy not by emission policy.

### Option B — Personas emit via a stdout-tailing sidecar in the workspace pod (rejected)

Personas write a structured JSON line to stdout; a sidecar in the workspace pod tails the log and publishes to the bus. This was the original recommendation in the design conversation.

**Rejected:** still places the LLM in the critical path for emission completeness. A persona that forgets to write the log line silently drops the event; a persona that hallucinates a wrong line writes a malformed event the sidecar must reject (producing the same missing-event outcome). The sidecar adds a per-workspace-pod component without solving the underlying problem.

### Option C — OpenHands plugin/hook intercepting persona phase transitions (rejected)

Install a plugin into the OpenHands runtime that fires on persona-phase events.

**Rejected:** tightly couples the emission path to the agent runtime. If OpenHands is ever swapped for another runtime (the OpenClaude and Claude Agent SDK options that were considered and rejected for #335 could re-emerge), the entire emission path must be rebuilt. Decoupling via the orchestrator-wrap keeps emission stable across runtime swaps.

### Option D — Persona calls a CLI tool that publishes to RabbitMQ (rejected)

The persona invokes a small CLI (`factory-emit-c7 …`) at each phase boundary as part of its skill runbook.

**Rejected:** every persona must remember to call it; the CLI must be present in the workspace image (extra surface); the persona holds bus credentials (security cost); a crashed persona between work-complete and CLI-call drops its terminal event with no recovery path.

## Consequences

- Phase 1 ticket #333 grows from "personas + skills + FR-008 picker" to "personas + skills + orchestrator service." The orchestrator service is the canonical autonomous-execution entry point and contains the FR-008 picker as one of its responsibilities. The orchestrator is a persistent Python (matching existing platform tooling) Deployment on the SKE foundation cluster control-plane pool, with ESO-projected RabbitMQ credentials and GitHub App credentials, subscribing to a webhook-handler-published work queue.
- Phase 1 ticket #333 also authors the **machine-parseable output schemas** as fenced ```yaml jsonschema``` blocks in every autonomous-execution skill runbook under `.agents/skills/<name>/SKILL.md` — this is the per-skill output contract the orchestrator validates.
- Phase 1 ticket #335 narrows: deploys OpenHands Agent Server + LiteLLM access configuration only. **No C7 emission code, no bus credentials, no emission ownership.** The `instrumentation-plan.md` line that previously named #335 as the emission owner is corrected by FR-019 to attribute emission to #333 (orchestrator) and #336 (webhook handler) with #335 as the runtime target only.
- Phase 1 ticket #336 grows from "webhook + C7 ingestion audit invariant" to also "publishes the trigger-accepted work message that the orchestrator subscribes to, AND emits the C7 events listed in the webhook handler responsibilities table above." This is a small addition — the webhook handler already observes every triggering condition in that table.
- Phase 1 ticket #334 is unaffected. The metric-extractor sidecar (consumer side of the bus) reads C7 events and writes Grafana time series; #334 already owns this and it does not change.
- The #339 Contract C7 surface gains a new sealed rule (the emission-mechanism rule pinned by this ADR) added in the same PR cycle as this ADR; the rule is cited from `design-contracts.md` § Contract C7 with this ADR as the normative reference.
- Consumer instances inherit this rule identically (sealed under #339 C8 FR-017). Consumer factory deployments MUST run their own orchestrator + their own webhook handler; consumers MUST NOT route C7 emission through any other path.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-019
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (nine-field lifecycle event schema, emission-transport rule, emission-mechanism rule), § Contract C8 (consumer-shipped surface)
- Related ADRs whose "MUST emit a C7 event" clauses are realized by this mechanism: [`ADR-issue-337-reject-rerun-cap.md`](ADR-issue-337-reject-rerun-cap.md) (FR-006), [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md) (FR-007), [`ADR-issue-337-reviewer-model-heterogeneity.md`](ADR-issue-337-reviewer-model-heterogeneity.md) (FR-008), [`ADR-issue-337-triage-size-threshold.md`](ADR-issue-337-triage-size-threshold.md) (FR-009), [`ADR-issue-337-light-decomposition-policy.md`](ADR-issue-337-light-decomposition-policy.md) (FR-010), [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md) (FR-003)
- Related ADRs whose orchestrator-side responsibilities are realized by this mechanism: [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md) (FR-001 — orchestrator resolves family/version → deployment ID), [`ADR-issue-337-reviewer-model-heterogeneity.md`](ADR-issue-337-reviewer-model-heterogeneity.md) (FR-008 — orchestrator-side picker reads prior C7 events)
- Instrumentation plan: `docs/blueprint/autonomous-factory/instrumentation-plan.md` (emission-owner attributions updated by this ADR)
- Phase 1 implementers: #333 (orchestrator service + persona output schemas), #335 (runtime target only — no emission), #336 (webhook handler emission table + trigger-accepted work queue), #334 (unaffected — sidecar remains consumer side)
