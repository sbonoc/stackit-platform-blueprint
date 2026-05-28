# Pre-Factory Baseline Measurements

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-014)
**Meta-ADR:** [`docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md`](../architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md)
**Owner:** `@sbonoc/factory-operations`
**Companion:** [`instrumentation-plan.md`](instrumentation-plan.md)

## Purpose

This document records the measured pre-factory baseline values for the four metrics declared in [`instrumentation-plan.md`](instrumentation-plan.md). Once the autonomous factory is in production (#334, #335, #336 merged), the live metrics MUST be compared against these baselines weekly per the cadence in the instrumentation plan. The factory's success metric depends on improving (or holding) against these baselines; significant regression triggers the `@sbonoc/factory-operations` review process declared in the instrumentation plan.

## Measurement Window

| Field | Value |
|---|---|
| Window start | **2026-04-17** (commit `df7595c` — *"enforce strict-default sdd and dedicated spec scaffolding branches"* — the commit that introduced the `SPEC_READY` gate per Q-6 on spec.md) |
| Window end | **2026-05-28** (day before this PR was signed off, per Q-6) |
| Window duration | 41 days |
| Scope | all merged PRs into `main` whose `mergedAt` falls within the window |
| Sample size (PRs) | **100** |

The 41-day window deliberately excludes pre-SDD methodology PRs (per Q-6 rationale: anchoring on SDD enablement is the only window that excludes pre-SDD methodology bias). Small-sample risk is acknowledged and is the right trade-off — recording a transparent count is preferred over inflating n by reaching into pre-SDD PRs that ran by different rules.

## Baseline Values

### (a) P50 lead time, current SDD workflow

| Statistic | Value |
|---|---|
| Sample n | 100 |
| Min | 0.19 h (~12 min) |
| P25 | 0.69 h (~42 min) |
| **P50 (median)** | **2.22 h (~2 h 13 min)** |
| P75 | 5.84 h (~5 h 50 min) |
| P90 | 15.43 h |
| Max | 73.64 h (~3 days) |
| Mean | 5.98 h |

**Source-of-truth field:** `(pr.mergedAt - pr.createdAt)` per merged PR (GitHub Pulls API).

**Interpretation for factory comparison:** the factory primary metric is `(pr_merged - agent_ready_label_applied)`; the pre-factory analogue used here is `(pr_merged - pr_created)`. The factory metric is expected to be **slightly shorter** than this baseline because `agent_ready` is applied after intake is complete, whereas the pre-factory `pr_created` event includes intake-in-the-PR. A successful factory therefore needs to beat **2.22 h P50** by a margin that compensates for this scope difference.

### (b) First-review rejection rate, current SDD workflow

| Statistic | Value |
|---|---|
| Sample n | 100 |
| PRs with formal `CHANGES_REQUESTED` review state | **0** |
| Computed first-review rejection rate (formal state) | **NOT MEASURABLE from this window** |
| Proxy: PRs with title prefix `fix(` (defect-fix rate) | 24 / 100 = **24%** |

**Limitation note.** In the SDD-era workflow, rejection is conveyed via PR comments (free-text rejection language, requests for changes in the canonical sign-off thread, or by reverting/reworking commits) rather than via GitHub's formal `CHANGES_REQUESTED` review state. All 407 formal reviews recorded in the window are `state: COMMENTED` (mostly automated bot reviewers — `copilot-pull-request-reviewer[bot]` and `chatgpt-codex-connector[bot]`). The formal-state-based rejection rate is therefore **structurally zero**, not an indication of zero rejection signal in the workflow.

The proxy (`fix(` title prefix) captures defect-fix PRs but does not differentiate "fix of a defect introduced by a prior PR in this window" from "fix of a pre-existing defect from before the window." Per FR-014's measurement scope, the comparable factory metric is the **AI-reviewer (step08) first-attempt rejection rate from C7 events** (per the instrumentation plan), which uses the formal `outcome: reject` field on `step08-agent-pr-review` events; once live, this is directly comparable to a forward measurement of the same proxy in the same SDD-era workflow.

### (c) Reviewer wall-time per PR, current SDD workflow

| Statistic | Value |
|---|---|
| Sample n | 95 (PRs with at least one non-author reviewer event in the window) |
| **P50 (median)** | **0.77 h (~46 min)** |
| P90 | 5.17 h |
| Mean | 2.05 h |

**Source-of-truth field:** `(first_non_author_review.submitted_at - pr.createdAt)` per PR.

**Important caveat.** 5 of 100 PRs had zero non-author reviewer events and are excluded from this statistic. Most "reviewer" events in this window come from automated bot reviewers (`copilot-pull-request-reviewer[bot]` and `chatgpt-codex-connector[bot]`) which respond within seconds; the median is therefore dominated by bot-review timing rather than human-reviewer wall-time. The factory's analogue (per the instrumentation plan) measures `(first_sign_off_comment - pr_opened)` and `(merge_event - last_sign_off_comment)` — both of which capture **human reviewer** wall-time only (sign-off comments are human-only per `AGENTS.md § Sign-off Policy`). The comparable forward measurement is the human-reviewer subset, not the bot-included subset measured here. This baseline is therefore primarily useful as a **lower bound** on what acceptable forward latency looks like.

### (d) Post-merge defect rate, current SDD workflow

| Statistic | Value |
|---|---|
| Sample n | 100 |
| PRs with title prefix `fix(` in the window | 24 |
| Computed proxy defect rate | **24%** of merged PRs in window |

**Source-of-truth field:** PR title prefix matching `^fix\(` (GitHub Pulls API title field).

**Limitation note.** FR-014 calls for defects opened within 30 days of merge. A direct measurement requires either (a) issue labels (e.g., `defect-fix`) consistently applied per the AGENTS.md defect-classification policy, or (b) a backlinking analysis of `fix(` PRs to the specific PRs they fix (via PR-body references or commit messages). Neither is consistently present in this window's PRs; the 24% proxy is **overcounting** (it includes fixes of pre-window defects) and is the most honest figure derivable from PR titles alone.

Per the instrumentation plan, the live-factory measurement uses the explicit `defect-fix` label workflow, which is unambiguous; the comparable forward measurement is **not directly comparable** to the 24% proxy. Treat 24% as a directional ceiling: a factory whose forward `defect-fix` rate exceeds 24% is unambiguously worse than the pre-factory workflow on this dimension; a factory whose forward rate is lower is at-or-better but the exact margin depends on labeling consistency post-Phase 1.

## Per-`owner_team` Breakdown

| `owner_team` | Sample n | P50 lead time | Reviewer wall-time P50 | Proxy defect rate |
|---|---|---|---|---|
| `@sbonoc/factory-operations` (sole pre-factory owner) | 100 | 2.22 h | 0.77 h | 24% |

The single-row breakdown reflects that the blueprint repo is the sole factory operator at baseline time. The per-`owner_team` shape is in place from day one per the instrumentation plan's requirement; consumer instances inherit the shape and populate their own rows via the #339 C8 consumer overlay.

## Sample-Size Caveats and Calibration Path

- **Sample n = 100** is bounded by the GitHub Search API window cap (`is:pr is:merged merged:2026-04-17..2026-05-29 base:main` returns exactly 100 PRs across the 41-day window — this is the full population, not a sampled subset).
- The window is intentionally short (41 days) per Q-6 to preserve methodological purity (SDD-era only). Per Q-7's `### Sample Size` disclosure pattern, the small-n risk is documented and the comparable forward measurements (live factory) will accumulate at ~2.4 PRs/day, producing comparably-sized 30-day rolling windows for forward comparison.
- Baselines (a) and (c) are directly measurable from GitHub Pulls API fields and are robust.
- Baselines (b) and (d) carry structural caveats noted above; the forward measurement specifications in the instrumentation plan resolve the structural ambiguity (formal-state-based or label-driven), so live-factory comparison is well-defined even though the backward comparison is approximate.

## Calibration Trigger (Forward)

After the first 30 ticket cycles of live-factory operation (estimated 1–2 weeks at expected throughput), the `@sbonoc/factory-operations` team MUST re-evaluate these baselines in two dimensions:

1. **Recompute the proxy metrics (b) and (d)** with the live-factory's formal `outcome: reject` events and `defect-fix` labels — these will give the first directly-comparable numbers. If the divergence between forward measurement and backward proxy is large, document the gap and propose a baseline-revision PR.
2. **Tune FR-007 ceilings and FR-009 thresholds** per the calibration path declared in [`ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md`](../architecture/decisions/ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md) and [`ADR-issue-337-triage-size-threshold.md`](../architecture/decisions/ADR-issue-337-triage-size-threshold.md), using the accumulated live-factory cost/duration/triage data.

The calibration is mechanical (overlay updates) and does not require ADR amendment per the parameterized classifications declared in those ADRs.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-014, § Clarifications Q-6, Q-7
- Meta-ADR: [`docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md`](../architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md)
- Companion: [`instrumentation-plan.md`](instrumentation-plan.md) (defines the forward metrics these baselines are compared against)
- Companion: [`triage-decomposition-data-feed.md`](triage-decomposition-data-feed.md) (the FR-015 retrospective classification of the same 100-PR window)
- Source data: `gh pr list --base main --state merged --search "merged:2026-04-17..2026-05-29"` retrieved 2026-05-29
