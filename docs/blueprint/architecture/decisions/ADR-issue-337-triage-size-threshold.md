# ADR: Triage Size Threshold (`blueprint-ticket-triage-size`)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-009)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `extensible` for the threshold table (consumers are permitted to shadow per their own ticket-size distribution); `sealed` for the four-class structure and the `escalate`-routes-to-humans semantics (enumerated explicitly in this ADR per the FR-009 four-class requirement).

## Context

The factory triages every incoming issue into a size class that determines its execution path: small/medium tickets go to single-pass factory execution; large tickets go through `blueprint-ticket-decompose-light` (per [`ADR-issue-337-light-decomposition-policy.md`](ADR-issue-337-light-decomposition-policy.md)); the largest tickets go to humans. Without a fixed four-class scheme and concrete numeric thresholds, triage becomes a per-ticket judgment call — inconsistent classifications break the FR-015 retrospective-classification audit and the FR-010 light-decomposition trigger.

The four-class scheme exists so the routing decision is **mechanical** (no model judgement needed for triage itself) and **reproducible** (the same ticket triaged twice gets the same class, and FR-015 retrospective classification is reproducible from issue text alone).

## Decision Drivers

- Triage MUST NOT itself consume significant model spend — the classification function is structural (count bounded contexts, estimate tokens, estimate step count), not generative.
- The four-class structure MUST be load-bearing for the FR-010 light-decomposition policy (the `large-decomposable` class is the trigger) — collapsing to fewer classes removes the trigger.
- `escalate` MUST be a real routing destination that produces no factory execution; otherwise pathological tickets exhaust ceilings under FR-007.
- Numeric thresholds are estimates pre-real-factory; consumers (including the blueprint as a self-consumer) MUST be able to tune them from accumulated baseline data without ADR amendment.
- The four classes themselves and the `escalate`-is-human-only rule MUST NOT drift across consumers, because PR-queue triage tooling, the C7 event stream's class label, and FR-015's retrospective classification all assume the same vocabulary.

## Decision

**Four-class classification scheme** for `blueprint-ticket-triage-size`:

| Class | Routing |
|---|---|
| `small` | single-pass factory execution |
| `medium` | single-pass factory execution |
| `large-decomposable` | route to `blueprint-ticket-decompose-light` (FR-010) |
| `escalate` | route to fully human-driven completion — **no factory execution** |

**Thresholds for the blueprint instance** (per Q-2 on spec.md). A ticket is classified into the lowest class whose AND-conjoined thresholds it satisfies:

| Class | Bounded contexts touched | Estimated token cost | Estimated SDD step invocations |
|---|---|---|---|
| `small` | ≤ 1 | ≤ 50k | ≤ 6 |
| `medium` | ≤ 2 | ≤ 150k | ≤ 12 |
| `large-decomposable` | ≤ 4 | ≤ 400k | ≤ 24 |
| `escalate` | otherwise (any dimension exceeds `large-decomposable`'s threshold) |

**Classification semantics.** All three dimensions are evaluated as an AND-conjunction — a ticket classified `small` MUST satisfy *all three* `small` thresholds; if any one dimension exceeds, the ticket promotes to the next class. The `escalate` class is the fall-through: any dimension exceeding the `large-decomposable` threshold routes the ticket to humans.

**`escalate` routing rule.** `escalate`-classified tickets MUST NOT receive factory execution. The factory bot MUST apply the `factory-escalate-human` label and post a PR/issue comment naming which threshold dimension triggered escalation. No `agent-ready` label may be applied to an `escalate`-classified ticket; if applied, the trigger MUST be no-op'd and a C7 lifecycle event emitted with `outcome: escalate-class-blocked`.

**Calibration path.** Threshold values are calibratable from FR-014 baselines once the first 30 cycles accumulate. Consumers (including the blueprint instance as a self-consumer) override values via `spec.factory_contract.triage.thresholds` in the #339 C8 consumer overlay — the four-class structure and the `escalate`-is-human-only rule are sealed and MUST NOT be overridden.

**Implementer.** #333 (Personas + Skills) authors the `blueprint-ticket-triage-size` skill runbook against this ADR's table. #338 (Phase 3) consumes the FR-015 retrospective classifications (which use this ADR's thresholds) as design evidence.

## Options Considered

### Option A — Four classes with AND-conjoined thresholds across three dimensions (chosen)

The decision above.

**Pros:** mechanical classification (no model needed); the `large-decomposable` class is load-bearing for FR-010's trigger; AND-conjunction means any single dimension's blowup correctly promotes class; `escalate` is a real routing destination; FR-015 retrospective classification is reproducible from issue text alone; thresholds are tunable per consumer.

**Cons:** three-dimensional AND requires estimating all three for every ticket, even small ones. Mitigation: for small tickets, the estimation is trivial (one-bounded-context, low-token, few-step is obvious from the issue text); the cost only matters at the boundaries.

### Option B — Single-dimension classification (token-count only) (rejected)

Classify by estimated token cost alone.

**Rejected:** misses the bounded-context fan-out that drives decomposition value — a 50k-token ticket touching 4 bounded contexts is fundamentally different from a 50k-token ticket touching 1, and the routing recommendation differs. Token count is necessary but not sufficient.

### Option C — Three classes (drop `escalate`) (rejected)

Collapse to `small`/`medium`/`large` with `large` always routing through decomposition.

**Rejected:** removes the human-only escape valve; pathological tickets (exploratory architecture, cross-cutting refactors that span the entire repo) would be force-decomposed into children that themselves fail FR-009 thresholds — a recursive loop. `escalate` is the load-bearing class that prevents this loop.

### Option D — Five-or-more classes (rejected)

Add an `xs` or `xl` class to give finer-grained routing.

**Rejected:** adds classification ambiguity without adding routing destinations — finer classes still route to the same three execution paths (single-pass / decompose / escalate). Four classes is the minimum count that matches the three routing destinations plus the human escape valve.

## Consequences

- Phase 1 ticket #333 authors the `blueprint-ticket-triage-size` skill against this ADR's thresholds; the skill is invoked by a triage persona on every `agent-ready`-eligible issue before any other factory work begins.
- FR-015 retrospective classification of historical tickets (in `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md`) uses these exact thresholds, making the retrospective evidence directly comparable to live-factory classifications.
- The `factory-escalate-human` label is the canonical "do not run the factory on this; route to a human owner" signal; reviewers/PMs MUST treat it as routing intent, not as a failure signal.
- C7 lifecycle event stream (#339 Contract C7) carries the triage `outcome` field with one of `{small, medium, large-decomposable, escalate}` — the dashboard derived from FR-012/Q-4 (`stackit-managed-grafana`) reports class-distribution-over-time as a calibration signal.
- Consumer instances inherit the four-class structure and `escalate`-is-human-only semantics identically (sealed); thresholds are parameterized per consumer overlay.
- Phase 3 ticket #338 (composition orchestration design) consumes the FR-015 data feed as evidence — the AND-conjoined three-dimension thresholds give #338 a richer signal than single-dimension classification would, because cross-context cycles are exactly the work whose composition is hardest to automate.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-009, § FR-015, § Clarifications Q-2
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-light-decomposition-policy.md`](ADR-issue-337-light-decomposition-policy.md), [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (lifecycle event schema — triage `outcome` field), § Contract C8 (consumer overlay — `spec.factory_contract.triage.thresholds`)
- Phase 1 implementer: #333 (Personas + Skills — triage skill)
- Phase 3 consumer: #338 (composition orchestration design)
