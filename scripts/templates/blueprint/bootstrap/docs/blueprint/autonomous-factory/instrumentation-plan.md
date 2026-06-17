# Autonomous Factory Instrumentation Plan

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-012, FR-013, FR-016)
**Meta-ADR:** `ADR-issue-337-factory-phase-0-foundations.md`
**Owner:** `@sbonoc/factory-operations`

## Purpose

This plan declares the metrics, data sources, dashboard target, retention, owner, and reporting cadence required to evaluate whether the autonomous factory is delivering on its success metric ("Zero Phase 1 ticket is blocked at implementation start by an unresolved Phase 0 decision"; downstream: positive impact on lead time and reviewer load relative to the FR-014 pre-factory baselines) and to detect regressions early enough to act.

The plan is the canonical owner of all telemetry decisions for the factory. Phase 1 tickets (#333, #334, #335, #336) implement the emission paths it specifies; Phase 3 ticket (#338) consumes its measurement results to design composition orchestration.

## Primary Metric

**P50 lead time from `agent-ready` label application to PR merge.**

- **Measurement unit:** wall-clock minutes.
- **Per-child / per-parent split:** measured per child issue independently for decomposed tickets (per `ADR-issue-337-light-decomposition-policy.md`); a parent-aggregate value (max child lead time) is also reported for decomposed parents so the integration-AC delay is visible.
- **Source-of-truth field:** `(pr.merged_at - issue.labeled_event.created_at)` derived from **GitHub Issues / PR events** — the `labeled` event with `label.name == 'agent-ready'` on the work-item issue (GitHub Issues API) and `pr.merged_at` on the resulting PR (GitHub Pulls API), joined by work-item ID. `#339 Contract C7` is NOT the source for this metric: the C7 eleven-field schema represents persona-phase emissions only (its `phase` enum is the eight SDD persona phases) and does not model GitHub-issue label-application or PR-merge events. Per the **Data Sources** rule below ("direct queries against GitHub events ... are permitted only when the same value cannot be derived from the C7 stream alone"), GitHub events are the correct source-of-truth here.
- **Reporting cadence:** weekly P50 reported on the dashboard with rolling 7-day, 30-day, and 90-day windows.

## Guardrail Metrics

| Metric | Threshold | Source-of-truth | Notes |
|---|---|---|---|
| First-review rejection rate | `< 25%` | C7 lifecycle event stream: count of events with `phase: agent-pr-review` and `outcome: rejected` and `rerun_round: 0`, divided by count of all C7 events with `phase: agent-pr-review` and `rerun_round: 0`, per work item | Reject = AI reviewer (`phase: agent-pr-review`) rejects the implementer's first attempt; the `rerun_round: 0` filter excludes reruns. The C7 `outcome` enum and the C7 `phase` field carry the required signal natively. |
| Post-merge defect rate | `≤ pre-factory baseline (see pre-factory-baselines.md)` | GitHub Issues events: count of issues opened with label `defect-fix` within 30 days of a merged factory PR, divided by count of factory PRs merged in the same 30-day window | Defect-fix label MUST be applied per the AGENTS.md defect-classification policy. |
| Reviewer wall-time per PR (spec gate) | `≤ pre-factory baseline` | GitHub Pulls API + Issues comments: `(first_sign_off_comment.created_at - pr.created_at)` per PR. Sign-off comments are human-only per AGENTS.md and are NOT C7 events (C7 emission is exclusive to autonomous execution per `design-contracts.md` § C7 emission rule), so the source-of-truth MUST be GitHub events directly. | Sign-off comments = the four canonical phrases. |
| Reviewer wall-time per PR (merge gate) | `≤ pre-factory baseline` | GitHub Pulls API + Issues comments: `(pr.merged_at - last_sign_off_comment.created_at)` per PR. Same rationale as the spec-gate row — human sign-off comments are not C7-emitted. | Captures the post-sign-off integration-review delay. |

Any guardrail breach for two consecutive weekly reports MUST trigger an `@sbonoc/factory-operations` review of factory behavior in the affected dimension; the review outcome MUST be one of (a) tune ceiling values per `ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`, (b) tune triage thresholds per `ADR-issue-337-triage-size-threshold.md`, (c) revert a specific ADR per NFR-REL-001, or (d) escalate to factory-architecture for design change.

## Data Sources

| Source | Used for | Owner |
|---|---|---|
| **GitHub Issues / PR events** | lifecycle stamps (label applications, PR opens/merges, issue closes); reviewer comment timestamps for wall-time computation; defect-fix label counts for defect rate | GitHub platform |
| **GitHub Actions run logs** | CI evidence (which jobs ran, pass/fail status, duration); cross-correlation with C7 events when factory reruns are triggered by CI signal | GitHub platform |
| **LiteLLM gateway usage logs** | model attribution (which model handled each persona invocation, prompt tokens, completion tokens, USD cost); enforced #339 NFR-SEC-001 exact-string bot-identity match | LiteLLM gateway (per `ADR-issue-337-sovereignty-zdr-posture.md`) |
| **#339 Contract C7 durable-bus lifecycle event stream** | canonical persona-phase event spine — every persona invocation (one event per phase transition with `phase`, `persona`, `outcome`, `rerun_round`, `owner_team`), every triage/decomposition decision, every rerun, and every ceiling-hit emits a C7 event with the eleven-field schema; this is the **system-of-record** for all factory-internal metrics that derive from persona-phase emissions | orchestrator service (#333) for phase-boundary events; webhook handler (#336) for GitHub-observable events (per `ADR-issue-337-c7-emission-mechanism.md`) |

The **C7 event stream is the canonical event spine for persona-phase emissions.** GitHub Issues / PR events (label applications, PR opens/merges, sign-off comments) are NOT C7 events — they are external lifecycle stamps that the C7 schema does not model (the `phase` enum is the eight SDD persona phases; there is no `event_type` or `label` field). For metrics whose source-of-truth is a GitHub event (the primary metric and both reviewer-wall-time guardrail rows), the GitHub Issues / PR events source is authoritative. For metrics whose source-of-truth is a persona-phase emission (the first-review rejection rate and per-`owner_team` derivation), C7 is authoritative.

## Dashboard Target, Retention, Owner

| Field | Value | Rationale |
|---|---|---|
| **Target** | `stackit-managed-grafana` (via the existing `OBSERVABILITY_ENABLED` module) | Managed-first per SDD-C-013; EU sovereignty satisfied by STACKIT-managed posture; no bespoke compliance work; reuses the existing observability surface. |
| **Retention** | `13 months` | Parity with the #334 LogMe WORM SOC 2 floor for incident-forensics cross-correlation — one query window covers both audit log and metrics. Storage-cost differential at expected event volumes (≤ 1k events/day per factory instance) is negligible against the forensics benefit. |
| **Owner** | `@sbonoc/factory-operations` | Natural on-call owner per the Q-3 gate-1 team assignment (sign-off authority for Operations sits with the same team that operates the factory runtime). |

## Bus-Subscribes-To-Dashboard Rule

The Grafana dashboard MUST subscribe to the durable bus (see next section) rather than receive synchronous writes from the factory runtime. Synchronous writes would couple factory wall-clock latency to dashboard availability and would block compliance with the #339 Contract C7 emission-transport rule.

## Durable-Bus Platform Pick (FR-013)

**Selected platform:** **STACKIT Managed RabbitMQ** (per Q-5 on spec.md, decided 2026-05-28).

### Why RabbitMQ

The factory bus is a fan-out problem with replay (durable fan-out from one publisher to N subscribers — the dashboard, the audit-log indexer, the cost meter, future Phase 3 composition orchestrator — where any subscriber, including a newly attached one, must be able to replay historic ranges from a known offset per C7 § Replayability). RabbitMQ **stream queues** match this shape natively: they are log-structured (offset-addressable), persist events to disk before producer return, and let any consumer attach at an arbitrary offset within the configured retention window. LogMe WORM (#334) is the long-tail audit-of-record for compliance retention beyond the bus's 13-month window — not a substitute for in-bus replayability.

### How the C7 emission-transport rule maps to RabbitMQ stream queues

| #339 Contract C7 rule | RabbitMQ stream-queue realization |
|---|---|
| Durability (survives broker restart) | stream queues (`x-queue-type: stream`) persist events to disk before publisher confirm; segment files are replicated across the managed-cluster nodes |
| Replayability (a new subscriber can catch up from a known offset) | streams are log-structured and offset-addressable — any consumer (including one that has never previously connected) can attach with `x-stream-offset` set to a timestamp, first-message, last-message, or numeric offset and consume from that point forward within the configured 13-month retention window |
| Async fire-and-forget from the factory runtime | publisher confirms with `mandatory=false` — the runtime emits and returns without blocking on subscriber acknowledgement |
| Independent subscriber consumer-position tracking | per-consumer offset tracking is the subscriber's responsibility (per C7); streams expose explicit offset management so each subscriber can checkpoint and resume independently |
| Per-ticket ordering when required | routing-key partitioning on the work-item ID across stream consumer groups — all events for a given ticket land on the same partition and are consumed in publish order, while different tickets fan out across consumers in parallel |

### Documented fallback (parameterized escape hatch)

**SKE-hosted Strimzi Kafka** (Q-5 Option B') is the documented fallback if a 1-day capacity spike reveals a blocking RabbitMQ limitation. Trigger thresholds for switching to the fallback (to be measured and documented as part of the first 30 cycles of live-factory operation):

- **max-message-size**: RabbitMQ default is 128 MiB — switch if any C7 event payload exceeds this. (C7 payloads are eleven structured fields; no realistic event approaches this floor.)
- **max-queues per broker**: STACKIT Managed RabbitMQ exposes per-tier limits — switch if subscriber count exceeds the limit, which would require Phase 3 to add a fan-out layer that doesn't exist in the Phase 1 design.
- **routing-throughput**: switch if sustained C7 emission rate exceeds the broker's published per-connection throughput limit by ≥ 2×.

### Stackit-managed-grafana subscription path

The Grafana dashboard subscribes to RabbitMQ via a thin metric-extractor sidecar that consumes the lifecycle event queue, transforms C7 events into Prometheus-compatible time series, and writes to the managed observability backend. This sidecar runs on the existing SKE foundation cluster (per #334) and inherits its NetworkPolicy posture; it carries no factory-decision logic and emits no events of its own.

**Implementation owner.** The sidecar is owned by #334 (factory runtime — same ticket that provisions the RabbitMQ Managed binding, the LogMe WORM audit-of-record, and the cluster-side NetworkPolicy). The sidecar is co-located with the bus subscriber/audit infrastructure rather than with the emission path (#335) because it consumes the C7 stream and writes to managed-grafana — it carries no OpenHands/LiteLLM runtime concerns.

## Per-`owner_team` Breakdown

Every metric above MUST be reported with an explicit per-`owner_team` breakdown row in the dashboard, even when the factory has a single `owner_team`. **For the blueprint instance**, the breakdown carries a single row with `owner_team = @sbonoc/factory-operations` while the blueprint is the sole factory operator.

The breakdown shape MUST be in place from day one so consumer instances inherit it without re-instrumentation. Consumer instances populate their own `owner_team` values via the #339 C8 consumer overlay — adding additional rows to the breakdown is mechanical and requires no dashboard schema change.

`owner_team` is derived from the C7 event stream's `owner_team` field (one of the eleven required fields in the C7 schema). It is snapshotted at C7 event-emission time on the first C7 event of the work item (`phase: intake`, the persona invocation triggered by the `agent-ready` label being applied) so retroactive team-membership changes do not rewrite history.

## Reporting Cadence

**Weekly.** A scheduled Grafana panel snapshot is delivered to the `@sbonoc/factory-operations` team channel every Monday at 09:00 Europe/Berlin, summarizing the seven preceding days against rolling 30-day and 90-day windows.

The weekly report MUST include:

1. P50 lead time (primary metric) per `owner_team`.
2. All four guardrail metrics per `owner_team`, with explicit pass/fail against the threshold.
3. Top-3 ceiling-hit and rerun-cap-hit work items from the week, with C7 event-stream links.
4. Triage class distribution from the week (counts of `small`/`medium`/`large-decomposable`/`escalate` per `ADR-issue-337-triage-size-threshold.md`).

Two consecutive weekly reports with the same guardrail breach MUST trigger the `@sbonoc/factory-operations` review described under **Guardrail Metrics** above.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-012, § FR-013, § FR-016, § Clarifications Q-4, Q-5
- Meta-ADR: `ADR-issue-337-factory-phase-0-foundations.md`
- Related ADRs: `ADR-issue-337-llm-model-router-policy.md`, `ADR-issue-337-reviewer-model-heterogeneity.md`, `ADR-issue-337-reject-rerun-cap.md`, `ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`, `ADR-issue-337-triage-size-threshold.md`, `ADR-issue-337-light-decomposition-policy.md`, `ADR-issue-337-sovereignty-zdr-posture.md`
- Design contracts: [`design-contracts.md`](design-contracts.md) § Contract C7 (eleven-field lifecycle event schema, emission-transport rule, blueprint-instance subsection), § Contract C8 (consumer overlay schema)
- Companion document: [`pre-factory-baselines.md`](pre-factory-baselines.md) (the baseline values these metrics MUST be measured against)
- Phase 1 implementers: #333 (orchestrator service — phase-boundary C7 emission per `ADR-issue-337-c7-emission-mechanism.md`; persona/skill discovery; FR-008 reviewer-rotation picker), #334 (factory runtime — SKE foundation cluster consumption, ESO + Secrets Manager, **LogMe WORM at the 13-month SOC 2 retention floor — required for the C7 emission-transport replayability split documented above**, egress NetworkPolicy, factory bot identity, RabbitMQ Managed binding, metric-extractor sidecar), #335 (OpenHands + LiteLLM — runtime target only; NOT a C7 emitter), #336 (GitHub Actions webhooks — event sources AND webhook-side C7 emission for GitHub-observable events per `ADR-issue-337-c7-emission-mechanism.md`)
- Phase 3 consumer: #338 (composition orchestration design — consumes the FR-015 data feed for evidence)
