# ADR — V-gate E2E Classification Enforcement (issue #353)

- Status: approved
- Date: 2026-06-01
- Deciders: platform-team
- Spec: specs/2026-06-01-issue-353-vgate-e2e-classification/spec.md
- ADR technical decision sign-off: approved

## Context

The blueprint `vitest_playwright_pact` test automation profile names Playwright as the E2E tool, but no governance rule prevents a consumer team from classifying the E2E gate for a user-facing flow as permanently `manual`. Because `make quality-sdd-check` has no corresponding check, this classification passes silently — browser-rendering defects accumulate undetected until a human manually tests the exact flow or a user reports the failure.

Five design questions must be resolved before implementation begins.

## Decision D-1 — Explicit flag vs heuristic detection for user-facing flows

**Decided:** Explicit `has-user-facing-flow` flag in the spec.md Implementation Stack Profile (Option A from Q-1).

**Rationale:** Deterministic, unit-testable, requires a conscious opt-in choice by the spec author. The flag follows the same pattern as `SPEC_READY_EXCEPTION` — explicit field, enumerated values, machine-checkable. Heuristic keyword scanning of FR text (Option B) produces unpredictable gate behaviour on edge-case FR phrasings and is difficult to cover comprehensively with tests.

**Trade-off:** False negatives (author forgets to set `has-user-facing-flow: true`) are bounded by code review and template seeding. Heuristics trade predictability for coverage, which is the wrong trade here.

## Decision D-2 — Profile scope: contains "playwright" vs exact string match

**Decided:** The check applies to any spec whose test automation profile string contains the substring `playwright` (Option A from Q-2).

**Rationale:** The check intent is "Playwright is available as the E2E tool for this work item." That intent is expressed by any profile string that names playwright — the canonical `pytest_vitest_playwright_pact` and any custom profile string a consumer team might define. An exact match would silently exempt custom profiles carrying Playwright, defeating the enforcement.

**Trade-off:** Substring match is slightly more permissive. A profile named `playwright_custom_v2` would trigger the check; this is correct — if you name playwright in your profile, the rule applies.

## Decision D-3 — Two classification values vs three (`manual-with-target` rejected)

**Decided:** `E2E gate classification` accepts only two values: `automated` (passes) and `manual` (violation when `has-user-facing-flow: true` + playwright profile). The `manual-with-target` value considered during spec drafting is rejected.

**Rationale:** `manual-with-target` partially contradicts the objective. It allows a team to declare a future date, pass every machine check, and ship the work item with zero Playwright coverage — which is exactly the accumulation of browser-rendering defects the issue was opened to prevent. The loophole is not closed by requiring a date; it is replaced with a documented deferral. Teams that cannot automate a user-facing flow in the current work item should set `has-user-facing-flow: false` with a justification comment — the honest declaration that the flow is not yet in a testable end-to-end state.

**Trade-off:** There is no machine-sanctioned deferred-automation path for post-gate work items. Teams must choose: automate now, or declare the flow not yet ready. This is intentional — the rule's value is precisely that it does not offer a comfortable middle option.

## Decision D-4 — Forward-only guard (`_VGATE_GATE_SINCE`)

**Decided:** The V-gate classification check applies only to work items whose slug date is on or after `_VGATE_GATE_SINCE` (the merge date of this PR). Pre-existing specs are grandfathered.

**Rationale:** Consistent with the pattern established in issue #352 (`_SPEC_COMPLETE_GATE_SINCE`). Retroactive enforcement on existing specs would create a batch of violations with no corresponding PR or author to address them, and would break CI for ongoing work items mid-flight.

**Trade-off:** Existing specs with permanently-manual E2E gates are not corrected. Considered acceptable; the check prevents future accumulation.

## Decision D-5 — Shift-left inference of `has-user-facing-flow` at step01 intake

**Decided:** The step01 intake SKILL.md MUST include a named signal list and inference step that pre-sets `has-user-facing-flow` from the issue content before the author sees the spec for the first time.

**Rationale:** The largest residual failure mode (R-2) is an author passively accepting `has-user-facing-flow: false` as the default without considering whether the work item has a user-facing flow. A passive default is invisible — authors don't engage with it. An agent-inferred `true` with an annotation comment is visible — the author must consciously override it to `false` and explain why. This changes the cognitive load from opt-in (remember to set `true`) to opt-out (override an active inference), which is the correct posture for a security/quality control. The frontend-stack cross-check adds a second signal: a non-`none` frontend stack profile with `has-user-facing-flow: false` is always a contradiction and MUST surface a clarification block.

**Trade-off:** The inference is heuristic — it will produce false positives (issue mentions "login page" in a description context where there is no new UI) and false negatives (UI work with no keyword signals). These are acceptable: false positives prompt the author to actively set `false` with a comment (good forcing function); false negatives fall through to the quality gate (enforcement backstop). The signal list is intentionally broad to minimise false negatives.

## Consequences

- `check_sdd_assets.py` gains a new `_check_vgate_classification` function and `_VGATE_GATE_SINCE` constant.
- Both spec templates gain two new Implementation Stack Profile fields (`has-user-facing-flow`, `E2E gate classification`); all future scaffolds will seed them with the signal list in the inline comment.
- `AGENTS.md` gains a mandatory Playwright E2E artifact rule scoped to `has-user-facing-flow: true`, with three explicit MUST clauses (full user journey, rendered DOM/screen state, wired to automated CI gate).
- `blueprint-sdd-step01-intake/SKILL.md` gains a V-gate inference step (signal list + frontend-stack cross-check) and a mandatory intake-report line item — shifting enforcement left to the moment an issue is first processed.
- Consumer teams starting new work items with a user-facing flow must set `E2E gate classification: automated` and deliver a Playwright test within the same work item. There is no machine-sanctioned deferred path.
- No retroactive changes to any existing spec, consumer repo, or CI workflow.
