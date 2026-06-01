# ADR — V-gate E2E Classification Enforcement (issue #353)

- Status: proposed
- Date: 2026-06-01
- Deciders: platform-team
- Spec: specs/2026-06-01-issue-353-vgate-e2e-classification/spec.md

## Context

The blueprint `vitest_playwright_pact` test automation profile names Playwright as the E2E tool, but no governance rule prevents a consumer team from classifying the E2E gate for a user-facing flow as permanently `manual`. Because `make quality-sdd-check` has no corresponding check, this classification passes silently — browser-rendering defects accumulate undetected until a human manually tests the exact flow or a user reports the failure.

Three design questions must be resolved before implementation begins.

## Decision D-1 — Explicit flag vs heuristic detection for user-facing flows

**Decided:** Explicit `has-user-facing-flow` flag in the spec.md Implementation Stack Profile (Option A from Q-1).

**Rationale:** Deterministic, unit-testable, requires a conscious opt-in choice by the spec author. The flag follows the same pattern as `SPEC_READY_EXCEPTION` — explicit field, enumerated values, machine-checkable. Heuristic keyword scanning of FR text (Option B) produces unpredictable gate behaviour on edge-case FR phrasings and is difficult to cover comprehensively with tests.

**Trade-off:** False negatives (author forgets to set `has-user-facing-flow: true`) are bounded by code review and template seeding. Heuristics trade predictability for coverage, which is the wrong trade here.

**Status:** decided — pending user confirmation before implementation begins.

## Decision D-2 — Profile scope: contains "playwright" vs exact string match

**Decided:** The check applies to any spec whose test automation profile string contains the substring `playwright` (Option A from Q-2).

**Rationale:** The check intent is "Playwright is available as the E2E tool for this work item." That intent is expressed by any profile string that names playwright — the canonical `pytest_vitest_playwright_pact` and any custom profile string a consumer team might define. An exact match would silently exempt custom profiles carrying Playwright, defeating the enforcement.

**Trade-off:** Substring match is slightly more permissive. A profile named `playwright_custom_v2` would trigger the check; this is correct — if you name playwright in your profile, the rule applies.

**Status:** proposed.

## Decision D-3 — Date validation depth: format-only vs future-date check

**Decided:** `E2E automation target` is validated for presence and ISO 8601 format (`\d{4}-\d{2}-\d{2}`) only. Past dates are not rejected by the machine gate (Option A from Q-3).

**Rationale:** A check that rejects past dates would cause spurious gate failures for work items that were created before a target date expired but haven't been resolved yet. The appropriate escalation for a missed automation target is a governance/step07-triage action (surfaced in the deferred proposals section), not a hard machine failure that blocks all local development on the branch. The machine gate's job is to enforce that an intention was stated — step07 triage enforces that the intention was kept.

**Trade-off:** Past dates silently pass the format check. This is accepted; the deferred-proposals list records `automation-target future-date enforcement` as a follow-up for a future work item.

**Status:** proposed.

## Decision D-4 — Forward-only guard (`_VGATE_GATE_SINCE`)

**Decided:** The V-gate classification check applies only to work items whose slug date is on or after `_VGATE_GATE_SINCE` (the merge date of this PR). Pre-existing specs are grandfathered.

**Rationale:** Consistent with the pattern established in issue #352 (`_SPEC_COMPLETE_GATE_SINCE`). Retroactive enforcement on existing specs would create a batch of violations with no corresponding PR or author to address them, and would break CI for ongoing work items mid-flight.

**Trade-off:** Existing specs with permanently-manual E2E gates are not corrected. Considered acceptable; the check prevents future accumulation.

**Status:** proposed.

## Consequences

- `check_sdd_assets.py` gains a new `_check_vgate_classification` function and `_VGATE_GATE_SINCE` constant.
- Both spec templates gain three new Implementation Stack Profile fields; all future scaffolds will seed them.
- `AGENTS.md` gains a mandatory Playwright E2E artifact rule scoped to `has-user-facing-flow: true`.
- Consumer teams starting new work items with a user-facing flow must consciously choose a V-gate classification and, if deferring automation, commit to an `E2E automation target` date.
- No retroactive changes to any existing spec, consumer repo, or CI workflow.
