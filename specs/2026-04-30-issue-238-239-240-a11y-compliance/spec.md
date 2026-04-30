# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- ADR path: docs/blueprint/architecture/decisions/ADR-20260430-issue-238-239-240-a11y-compliance.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale: SDD-C-009 not applicable (no authn/authz or secret handling); SDD-C-013/SDD-C-014 not applicable (tooling-only, no STACKIT managed service or Kubernetes runtime); SDD-C-022 not applicable (no HTTP route or API endpoint); SDD-C-023 not applicable (no filter or payload-transform logic)

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: tooling-only change; no managed service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Resolved Questions

### Q-1: Layer conditionality — RESOLVED: Option B (2026-04-30, PR #243)

All a11y scaffold sections (NFR-A11Y-001 in spec.md, T-Axx task block in tasks.md, Accessibility Gate in hardening_review.md) are added unconditionally to the standard templates. Authors in non-UI specs declare "N/A" in the NFR body and mark non-applicable checklist items N/A. No `layer:` field is added to the spec.md template in this work item — keeps scope self-contained and avoids a cross-cutting structural change. Decision: product owner via PR #243 comment 2026-04-30.

### Q-2: ACR integration path — RESOLVED: Option B (2026-04-30, PR #243)

`quality-a11y-acr-check` is wired into `quality-hooks-fast` (and documented as an extension point for `quality-ci-blueprint`). No `consumer_fitness_status.sh` script is created in this work item — deferred to a standalone work item. Decision: product owner via PR #243 comment 2026-04-30.

## Objective
- Business outcome: Blueprint consumers targeting EU markets can demonstrate WCAG 2.1 AA / EN 301 549 §9 conformance (EAA Directive 2019/882/EU, enforcement from June 2025) by following the standard SDD lifecycle, without any manual accessibility scaffold assembly. The lifecycle encodes a11y as a first-class NFR, enforces it through automated test infrastructure, and generates an auditable ACR trail linking spec-level requirements to conformance declarations.
- Success metric: (1) Any newly scaffolded spec using the updated template includes NFR-A11Y-001 and the T-Axx task block by default. (2) `touchpoints-test-a11y` and `apps-a11y-smoke` targets execute axe scans with the explicit WCAG 2.1 AA ruleset on every consumer CI run. (3) `quality-a11y-acr-check` in `quality-hooks-fast` fails when the ACR is missing or stale, blocking builds. (4) Zero blueprint-side structural changes required for consumers to consume this upgrade.

## Normative Requirements

### Functional Requirements — Slice 1: SDD lifecycle templates (Issue #238)

- FR-101 MUST add `- NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.` to the standard NFR section of the `spec.md` scaffold template (`.spec-kit/templates/blueprint/spec.md`); unconditional — authors in non-UI specs write "N/A" in the NFR body.
- FR-102 MUST add a mandatory accessibility task block (T-A01 through T-A05) to the `tasks.md` scaffold template (`.spec-kit/templates/blueprint/tasks.md`); unconditional. T-A02 MUST explicitly reference the WCAG 2.1 AA axe ruleset tags (`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`) and the `attachTo: document.body` requirement.
- FR-103 MUST add a mandatory "Accessibility Gate" checklist section to the `hardening_review.md` scaffold template (`.spec-kit/templates/blueprint/hardening_review.md`) covering: programmatic name (SC 4.1.2), keyboard operability (SC 2.1.1), focus indicator (SC 2.4.7), colour-only information (SC 1.4.1), error identification (SC 3.3.1), and axe-core WCAG 2.1 AA scan evidence; unconditional — non-UI hardening reviewers mark non-applicable items N/A.
- FR-104 MUST add a `WCAG SC` column to the traceability matrix header row in the `traceability.md` scaffold template (`.spec-kit/templates/blueprint/traceability.md`); non-UI FR rows carry `N/A`.
- FR-105 MUST update `scripts/bin/platform/quality/check_spec_pr_ready.py` to validate that the Accessibility Gate section in `hardening_review.md` has no unchecked boxes; non-applicable items MUST be explicitly marked `N/A` rather than left unchecked.

### Functional Requirements — Slice 2: Test infrastructure (Issue #239)

- FR-201 MUST add a `touchpoints-test-a11y` Make target to `make/platform.mk` backed by `scripts/bin/platform/touchpoints/test_a11y.sh`; the script MUST run `axe_page_scan.mjs` against `A11Y_BASE_URL` (default: `http://localhost:3000`) over `A11Y_ROUTES` (default: `/`) and exit non-zero when any violation's `impact` is in `A11Y_FAIL_ON_IMPACT` (default: `critical,serious`).
- FR-202 MUST add an `apps-a11y-smoke` Make target to `make/platform.mk` backed by `scripts/bin/platform/apps/a11y_smoke.sh`; `test-smoke-all-local` MUST include `apps-a11y-smoke`.
- FR-203 MUST add `scripts/lib/platform/touchpoints/axe_page_scan.mjs` as a blueprint-managed Playwright+axe runner that: uses `@axe-core/playwright` with `runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa'] }`; writes `artifacts/a11y/axe-report.json` per route; prints a human-readable violation summary; exits non-zero on `A11Y_FAIL_ON_IMPACT` violations.
- FR-204 MUST add `scripts/lib/platform/touchpoints/axe_preset.ts` exporting `WCAG21AA_AXE_CONFIG` (with explicit tag array) and `assertAxeWcag21AA(element)` for use in consumer vitest-axe tests; the export MUST document the `attachTo: document.body` precondition.
- FR-205 MUST extend `test-smoke-all-local` in `make/platform.mk` to include `apps-a11y-smoke` alongside the existing `backend-smoke-local-auth-parity` and `apps-smoke` targets.

### Functional Requirements — Slice 3: ACR scaffold and quality gate (Issue #240)

- FR-301 MUST add `docs/platform/accessibility/acr.md` as a **consumer-seeded file** (editable after seeding, not overwritten on blueprint upgrade) pre-populated with all WCAG 2.1 Level A and AA success criteria rows in the VPAT 2.4 structure; columns: SC, Name, Level, Support, Notes, Evidence.
- FR-302 MUST add a `quality-a11y-acr-check` Make target backed by `scripts/bin/platform/quality/check_acr_freshness.py`; the script MUST exit non-zero with a diagnostic message when: `docs/platform/accessibility/acr.md` does not exist; or the `Report date (last reviewed):` field is a placeholder; or the date is older than `ACR_STALENESS_DAYS` (default: 90, sourced from `blueprint/contract.yaml`).
- FR-303 MUST add a `quality-a11y-acr-sync` Make target backed by `scripts/bin/platform/quality/sync_acr_criteria.py` that regenerates the WCAG 2.1 criterion rows in `acr.md` from a bundled W3C WCAG 2.1 criteria list while preserving existing support/notes/evidence cell content.
- FR-304 MUST update the PR Packager skill runbook (`.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md`) to include an ACR review checklist item for UI-layer specs; authors confirm ACR `Report date` has been updated for any spec touching user-facing surfaces.
- FR-305 MUST wire `quality-a11y-acr-check` into `quality-hooks-fast` in `make/blueprint.generated.mk` (and its template source); document as an optional extension into `quality-ci-blueprint` for consumers.

### Non-Functional Requirements (Normative)

- NFR-EAA-001 MUST ensure all a11y gates target WCAG 2.1 Level AA / EN 301 549 §9 as the conformance baseline; no gate MUST pass on the axe default ruleset without the explicit `wcag21a` and `wcag21aa` tags.
- NFR-REL-001 MUST ensure zero impact on existing consumer specs, `hardening_review.md` files, and `traceability.md` files — template changes apply only to newly scaffolded files; existing consumer-owned files are not overwritten on blueprint upgrade.
- NFR-OPS-001 MUST make the ACR staleness window configurable via `blueprint/contract.yaml` (`acr_staleness_days`, default: 90); diagnostic output MUST include the configured window and days elapsed.
- NFR-TEST-001 MUST ensure all new Make targets and scripts are testable by contract assertions in `tests/blueprint/test_quality_contracts.py` and `tests/platform/` without a live browser; script existence, template content strings, and Make target resolution MUST be assertable in CI without Playwright launch.

## Normative Option Decision
- Option A: Conditional activation via `layer:` field in spec.md + create consumer_fitness_status.sh
- Option B: Unconditional a11y sections with N/A opt-out + wire ACR check into quality-hooks-fast
- Selected option: OPTION_B
- Rationale: Unconditional templates keep scope self-contained and avoid a cross-cutting `layer:` field change that warrants its own work item. Wiring `quality-a11y-acr-check` into `quality-hooks-fast` achieves the same CI-blocking effect without creating `consumer_fitness_status.sh`, which is a substantial new feature deferred to a standalone work item. Decision by product owner via PR #243 comment 2026-04-30.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` — add `acr_staleness_days: 90` under `spec.quality.accessibility`
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: new consumer-side targets `touchpoints-test-a11y`, `apps-a11y-smoke`, `quality-a11y-acr-check`, `quality-a11y-acr-sync` (in `make/platform.mk`, additive); `test-smoke-all-local` extended to include `apps-a11y-smoke`; `quality-hooks-fast` in `make/blueprint.generated.mk` extended to include `quality-a11y-acr-check`
- Docs contract: `docs/platform/accessibility/acr.md` new consumer-seeded file; `docs/reference/generated/core_targets.generated.md` auto-updated by `quality-docs-sync-core-targets`

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 MUST: the `.spec-kit/templates/blueprint/spec.md` template contains `NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.`
- AC-002 MUST: the `.spec-kit/templates/blueprint/tasks.md` template contains a T-Axx block with T-A01 through T-A05; T-A02 explicitly names tags `wcag21a` and `wcag21aa` and `attachTo: document.body`
- AC-003 MUST: the `.spec-kit/templates/blueprint/hardening_review.md` template contains an "Accessibility Gate" section with all six checklist items
- AC-004 MUST: the `.spec-kit/templates/blueprint/traceability.md` template header row contains a `WCAG SC` column
- AC-005 MUST: `quality-spec-pr-ready` validates the Accessibility Gate section has no unchecked (non-N/A) boxes; `make infra-contract-test-fast` passes after implementation
- AC-006 MUST: `touchpoints-test-a11y` Make target resolves; `test_a11y.sh` script exists; axe scan uses explicit WCAG 2.1 AA tag array in `axe_page_scan.mjs`
- AC-007 MUST: `apps-a11y-smoke` Make target resolves; `make test-smoke-all-local --dry-run` includes `apps-a11y-smoke`
- AC-008 MUST: `axe_page_scan.mjs` source contains `wcag21a` and `wcag21aa` in the `runOnly.values` array; assertion verifiable by contract test string match
- AC-009 MUST: `axe_preset.ts` exports `WCAG21AA_AXE_CONFIG` with `values: ['wcag2a','wcag2aa','wcag21a','wcag21aa']`; contract test asserts string presence
- AC-010 MUST: `docs/platform/accessibility/acr.md` scaffold contains all 50 WCAG 2.1 A+AA success criteria rows (1.1.1 through 4.1.3) with SC, Name, Level columns pre-populated
- AC-011 MUST: `quality-a11y-acr-check` exits 1 when ACR missing, exits 1 when `Report date` is a placeholder, exits 1 when date is older than `ACR_STALENESS_DAYS` days, exits 0 when date is within window; unit-testable without live browser; wired into `quality-hooks-fast`
- AC-012 MUST: PR Packager skill runbook includes ACR review checklist item prompting authors to confirm `Report date` is updated for UI-facing specs

## Informative Notes (Non-Normative)
- Context: EAA (Directive 2019/882/EU) mandates EN 301 549 / WCAG 2.1 AA for private-sector digital products/services in the EU market; enforcement began June 2025. Blueprint currently has no a11y NFR, no standard axe test infrastructure, and no ACR scaffold — each consumer builds this independently, inconsistently, or not at all. This three-issue bundle closes all three structural gaps in one PR.
- Tradeoffs: Unconditional templates (Option B) mean non-UI specs include sections that authors mark N/A — a small friction, but avoids adding a `layer:` structural field that is a broader cross-cutting concern. Wiring into `quality-hooks-fast` (Option B) is simpler than creating a new `consumer_fitness_status.sh` script; the fitness script surface is deferred to when a broader set of fitness checks is identified.
- Clarifications: `@axe-core/playwright` is expected as a devDependency in the consumer touchpoints bootstrap; blueprint does not manage consumer package.json directly. Consumers adding `touchpoints-test-a11y` must add `@axe-core/playwright` to their `package.json` — document in touchpoints bootstrap guide.

## Explicit Exclusions
- Does NOT create `scripts/bin/blueprint/consumer_fitness_status.sh` — deferred to a standalone work item when a broader set of consumer fitness checks is identified.
- Does NOT add a `layer:` field to `spec.md` template — deferred to a standalone cross-cutting work item.
- Does NOT add `quality-a11y-acr-check` to `quality-ci-blueprint` (risk of false positives in blueprint's own CI where no consumer acr.md exists); scoped to `quality-hooks-fast` (consumer-side) only.
- Does NOT implement `quality-a11y-acr-sync` automated W3C JSON fetch at CI time; criterion list is bundled statically.
- Does NOT migrate or validate existing consumer `hardening_review.md` or `traceability.md` files on blueprint upgrade.
