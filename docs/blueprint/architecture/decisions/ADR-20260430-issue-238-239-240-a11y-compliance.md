# ADR: Accessibility Compliance — SDD Lifecycle Gates, Test Infrastructure, and ACR Scaffold

- **Status:** proposed
- **ADR technical decision sign-off:** pending
- **Date:** 2026-04-30
- **Issues:** https://github.com/sbonoc/stackit-platform-blueprint/issues/238, https://github.com/sbonoc/stackit-platform-blueprint/issues/239, https://github.com/sbonoc/stackit-platform-blueprint/issues/240
- **Work item:** `specs/2026-04-30-issue-238-239-240-a11y-compliance/`

## Context

The European Accessibility Act (Directive 2019/882/EU) mandates EN 301 549 / WCAG 2.1 AA
conformance for private-sector digital products and services in the EU market, with
enforcement from June 2025. Blueprint consumers targeting the EU market must be able to
demonstrate conformance — but the blueprint SDD lifecycle currently treats accessibility as
implicit quality rather than a first-class concern. Concretely:

- No standard `NFR-A11Y-001` in the spec.md template — authors omit it and produce specs
  with no enforceable a11y contract.
- No `T-Axx` task block in tasks.md — axe scan tasks and keyboard testing tasks are
  routinely omitted or under-specified (missing the explicit `wcag21a`/`wcag21aa` tags and
  the `attachTo: document.body` requirement that are the two most common misconfiguration
  points causing axe scans to pass while missing real WCAG 2.1 AA violations).
- No "Accessibility Gate" checklist in hardening_review.md — hardening reviewers are not
  prompted to verify keyboard operability, focus visibility, or programmatic labels.
  A component missing a programmatic label (SC 4.1.2 — Name, Role, Value) can pass every
  automated gate, pass hardening review, and reach production.
- No WCAG SC column in traceability.md — the traceability matrix cannot serve as
  EAA compliance evidence without SC-level linkage from requirements to WCAG success criteria.
- No full-page axe scan infrastructure — component-level axe catches isolated violations
  but misses context-dependent violations (heading hierarchy, skip-link presence, landmark
  structure, focus order across composed pages).
- No Accessibility Conformance Report (ACR) scaffold or staleness gate — consumers who need
  an ACR must author it from scratch, maintain it manually, and have no automated gate
  that catches a stale or missing ACR before a release.

Three issues address these gaps as a combined bundle: #238 (SDD lifecycle templates),
#239 (test infrastructure), #240 (ACR scaffold and quality gate).

## Resolved Design Decisions

### Q-1: Layer conditionality — Option B (2026-04-30, PR #243)

All a11y scaffold sections (NFR-A11Y-001 in spec.md, T-Axx task block in tasks.md,
Accessibility Gate in hardening_review.md) are added **unconditionally** to the standard
templates. Authors in non-UI specs declare "N/A" in the NFR body and mark non-applicable
checklist items N/A. No `layer:` field is added to the spec.md template in this work
item — scope is kept self-contained and a cross-cutting structural change is avoided.
Decision: product owner via PR #243 comment 2026-04-30.

### Q-2: ACR integration path — Option B (2026-04-30, PR #243)

`quality-a11y-acr-check` is wired into `quality-hooks-fast` in `make/blueprint.generated.mk`
(and its template source). No `consumer_fitness_status.sh` script is created in this work
item — deferred to a standalone work item when a broader set of consumer fitness checks
is identified. Decision: product owner via PR #243 comment 2026-04-30.

## Decision

**Embed WCAG 2.1 AA as a first-class SDD concern via three coordinated delivery slices.**

### Slice 1: SDD lifecycle templates (Issue #238)

Add the following unconditionally to the standard blueprint scaffold templates:

- `spec.md`: `- NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.` in the standard NFR section; authors in non-UI specs write "N/A".
- `tasks.md`: T-Axx task block (T-A01 through T-A05); T-A02 must explicitly name `['wcag2a','wcag2aa','wcag21a','wcag21aa']` and `attachTo: document.body`.
- `hardening_review.md`: "Accessibility Gate" section with six mandatory checklist items (SC 4.1.2, 2.1.1, 2.4.7, 1.4.1, 3.3.1, plus axe-core scan evidence); non-UI reviewers mark non-applicable items N/A.
- `traceability.md`: `WCAG SC` column header in the requirement-to-delivery mapping table.

Extend `check_spec_pr_ready.py` to fail on unchecked (non-N/A) Accessibility Gate items in
`hardening_review.md` — same pattern as existing findings/proposals validation.

### Slice 2: Test infrastructure (Issue #239)

Add blueprint-managed axe test infrastructure:

- `touchpoints-test-a11y` Make target + `test_a11y.sh` script: Playwright+axe full-page scan
  with configurable `A11Y_BASE_URL`, `A11Y_ROUTES`, `A11Y_FAIL_ON_IMPACT` variables.
- `apps-a11y-smoke` Make target + `a11y_smoke.sh` script: wraps `test_a11y.sh` with
  smoke-appropriate defaults; extended into `test-smoke-all-local`.
- `axe_page_scan.mjs`: `@axe-core/playwright` runner with `runOnly: { type: 'tag',
  values: ['wcag2a','wcag2aa','wcag21a','wcag21aa'] }`; writes `artifacts/a11y/axe-report.json`
  per route; exits non-zero on `A11Y_FAIL_ON_IMPACT` violations.
- `axe_preset.ts`: exports `WCAG21AA_AXE_CONFIG` and `assertAxeWcag21AA` for consumer
  vitest-axe tests; documents `attachTo: document.body` precondition.

### Slice 3: ACR scaffold and quality gate (Issue #240)

- `docs/platform/accessibility/acr.md`: consumer-seeded VPAT 2.4 scaffold pre-populated
  with all 50 WCAG 2.1 A+AA success criteria rows (SC 1.1.1 through 4.1.3); not overwritten
  on blueprint upgrade after initial seeding.
- `quality-a11y-acr-check` + `check_acr_freshness.py`: fails when ACR missing, date
  unpopulated, or older than `ACR_STALENESS_DAYS` (default: 90, from `blueprint/contract.yaml`);
  wired into `quality-hooks-fast`.
- `quality-a11y-acr-sync` + `sync_acr_criteria.py`: regenerates criterion rows from bundled
  W3C WCAG 2.1 list; preserves existing support/notes/evidence content.
- PR Packager skill runbook update: ACR review checklist item prompting authors to confirm
  `Report date` is updated for any spec touching user-facing surfaces.

## Options Considered

### Q-1 — Option A: Conditional activation via `layer:` field

- Adds `layer: ui | design-system | backend | ...` to spec.md template.
- `quality-spec-pr-ready` reads the field and enforces a11y sections only for UI layers.
- More precise; no N/A burden on non-UI specs; reusable for future layer-aware quality checks.
- Requires additional structural change beyond a11y scope; `layer:` field warrants own ADR.
- Not selected.

### Q-1 — Option B (selected): Unconditional sections with N/A opt-out

- All scaffolded specs include NFR-A11Y-001; non-UI authors write "N/A".
- No new `layer:` field or conditional parsing required.
- Small author burden for non-UI specs; keeps scope self-contained.
- **Selected** — decision by product owner via PR #243 comment 2026-04-30.

### Q-2 — Option A: Create consumer_fitness_status.sh

- New `scripts/bin/blueprint/consumer_fitness_status.sh` with `blueprint-consumer-fitness-status` Make target.
- Provides a unified consumer fitness check surface extensible by future checks.
- Significant scope expansion beyond a11y topic; warrants its own SDD work item.
- Not selected.

### Q-2 — Option B (selected): Wire into quality-hooks-fast

- `quality-a11y-acr-check` wired directly into `quality-hooks-fast`.
- Same CI-blocking effect; no new script or target required.
- `consumer_fitness_status.sh` deferred to a standalone work item.
- **Selected** — decision by product owner via PR #243 comment 2026-04-30.

## Consequences

- **Positive:** every new spec scaffolded after this blueprint upgrade prompts the author to declare WCAG 2.1 AA conformance scope or explicitly declare N/A — closing the silent-omission gap.
- **Positive:** the shared `axe_preset.ts` normalises the ruleset and `attachTo` convention across all consumer unit tests immediately after adoption.
- **Positive:** `quality-a11y-acr-check` in `quality-hooks-fast` turns ACR maintenance from a manual discipline into a CI-blocking check.
- **Neutral:** existing consumer `hardening_review.md`, `tasks.md`, `traceability.md` files are unaffected; only newly scaffolded files receive the new sections.
- **Neutral:** non-UI specs receive NFR-A11Y-001 and Accessibility Gate sections that authors mark N/A; one extra N/A declaration per non-UI spec.
- **Negative:** `@axe-core/playwright` is a consumer devDependency not managed by blueprint; adoption requires a consumer package.json addition.
