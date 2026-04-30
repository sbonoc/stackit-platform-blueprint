# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 2
- Unresolved alternatives count: 1
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 2
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-20260430-issue-238-239-240-a11y-compliance.md
- ADR status: proposed

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

## Objective
- Business outcome: Blueprint consumers targeting EU markets can demonstrate WCAG 2.1 AA / EN 301 549 §9 conformance (EAA Directive 2019/882/EU, enforcement from June 2025) by following the standard SDD lifecycle, without any manual accessibility scaffold assembly. The lifecycle encodes a11y as a first-class NFR, enforces it through automated test infrastructure, and generates an auditable ACR trail linking spec-level requirements to conformance declarations.
- Success metric: (1) Any newly scaffolded spec using the updated template includes NFR-A11Y-001 and the T-Axx task block by default. (2) `touchpoints-test-a11y` and `apps-a11y-smoke` targets execute axe scans with the explicit WCAG 2.1 AA ruleset on every consumer CI run. (3) `quality-a11y-acr-check` fails when the ACR is missing or stale, blocking PR packaging for UI-layer specs. (4) Zero blueprint-side changes required by consumers who do not have a UI layer.

## Open Questions (Blocking — clears before SPEC_READY=true)

### Q-1: Layer conditionality mechanism
Issues #238–#240 describe NFR-A11Y-001, T-Axx, hardening checklist, and ACR checklist as conditional on `layer: ui | design-system` in `spec.md`. No `layer:` field exists in the current spec.md template or in `quality-spec-pr-ready` validation logic.

- **Option A**: Add a `layer:` field to `spec.md` template; update `quality-spec-pr-ready` to read it and enforce a11y sections only when `layer` includes `ui` or `design-system`. Conditional enforcement; authors must declare the layer explicitly.
- **Option B**: Make all a11y sections unconditional; NFR-A11Y-001 states "MUST define WCAG 2.1 AA compliance scope or declare N/A"; authors in non-UI specs write "N/A"; no new structural field required. Simpler; avoids scope expansion beyond the a11y work item.
- **Agent recommendation**: Option B — avoids adding a `layer:` field (a broader cross-cutting change) to this work item scope; N/A opt-out keeps the template honest without automated field parsing. Adding `layer:` is better addressed as a standalone work item when multiple consumers want it.
- **Blocker for**: FR-101, FR-102, FR-103, FR-105, FR-304, AC-001, AC-002, AC-003, AC-005, AC-012

[NEEDS CLARIFICATION: Choose Option A (conditional layer field) or Option B (unconditional with N/A opt-out) to unblock SPEC_READY]

### Q-2: ACR integration path for consumer fitness check
Issue #240 says to add `quality-a11y-acr-check` to `blueprint-consumer-fitness-status`. No `consumer_fitness_status.sh` script exists in the blueprint codebase.

- **Option A**: Create `scripts/bin/blueprint/consumer_fitness_status.sh` as part of this work item and wire `quality-a11y-acr-check` into it. Significant scope expansion beyond the a11y topic.
- **Option B**: Wire `quality-a11y-acr-check` into `quality-hooks-fast` (and optionally `quality-ci-blueprint`) instead of a fitness-status script; document consumer adoption path. Stays within a11y scope; defers fitness-status script to its own work item.
- **Agent recommendation**: Option B — wiring into quality-hooks-fast achieves the same CI-blocking effect; creating consumer_fitness_status.sh is a substantial new feature that warrants its own SDD work item.
- **Blocker for**: FR-305, AC-011

[NEEDS CLARIFICATION: Choose Option A (create consumer_fitness_status.sh) or Option B (wire into quality-hooks-fast) to unblock SPEC_READY]

## Normative Requirements

### Functional Requirements — Slice 1: SDD lifecycle templates (Issue #238)

- FR-101 MUST add `- NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.` to the standard NFR section of the `spec.md` scaffold template (`.spec-kit/templates/blueprint/spec.md`). [conditionality per Q-1]
- FR-102 MUST add a mandatory accessibility task block (T-A01 through T-A05) to the `tasks.md` scaffold template (`.spec-kit/templates/blueprint/tasks.md`). T-A02 MUST explicitly reference the WCAG 2.1 AA axe ruleset tags (`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`) and the `attachTo: document.body` requirement. [conditionality per Q-1]
- FR-103 MUST add a mandatory "Accessibility Gate" checklist section to the `hardening_review.md` scaffold template (`.spec-kit/templates/blueprint/hardening_review.md`) covering: programmatic name (SC 4.1.2), keyboard operability (SC 2.1.1), focus indicator (SC 2.4.7), colour-only information (SC 1.4.1), error identification (SC 3.3.1), and axe-core WCAG 2.1 AA scan evidence. [conditionality per Q-1]
- FR-104 MUST add a `WCAG SC` column to the traceability matrix header row in the `traceability.md` scaffold template (`.spec-kit/templates/blueprint/traceability.md`); non-UI FR rows carry `N/A`.
- FR-105 MUST update `scripts/bin/platform/quality/check_spec_pr_ready.py` to validate that the Accessibility Gate section in `hardening_review.md` has no unchecked boxes for applicable specs. [conditionality per Q-1]

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
- FR-304 MUST update the PR Packager skill runbook (`.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md`) to include an ACR review checklist item for UI-layer specs. [conditionality per Q-1]
- FR-305 MUST wire `quality-a11y-acr-check` into the quality hook chain; integration target depends on Q-2 resolution.

### Non-Functional Requirements (Normative)

- NFR-EAA-001 MUST ensure all a11y gates target WCAG 2.1 Level AA / EN 301 549 §9 as the conformance baseline; no gate MUST pass on the axe default ruleset without the explicit `wcag21a` and `wcag21aa` tags.
- NFR-REL-001 MUST ensure zero impact on existing consumer specs, `hardening_review.md` files, and `traceability.md` files — template changes apply only to newly scaffolded files; existing consumer-owned files are not overwritten on blueprint upgrade.
- NFR-OPS-001 MUST make the ACR staleness window configurable via `blueprint/contract.yaml` (`acr_staleness_days`, default: 90); diagnostic output MUST include the configured window and days elapsed.
- NFR-TEST-001 MUST ensure all new Make targets and scripts are testable by contract assertions in `tests/blueprint/test_quality_contracts.py` and `tests/platform/` without a live browser; script existence, template content strings, and Make target resolution MUST be assertable in CI without Playwright launch.

## Normative Option Decision
- Option A: Conditional activation via `layer:` field in spec.md + create consumer_fitness_status.sh
- Option B: Unconditional a11y sections with N/A opt-out + wire ACR check into quality-hooks-fast
- Selected option: OPEN_QUESTION — pending Q-1 and Q-2 resolution
- Rationale: see Open Questions section

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` — add `acr_staleness_days: 90` under `spec.quality.accessibility`
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: new targets `touchpoints-test-a11y`, `apps-a11y-smoke`, `quality-a11y-acr-check`, `quality-a11y-acr-sync` (all additive); `test-smoke-all-local` extended to include `apps-a11y-smoke`
- Docs contract: `docs/platform/accessibility/acr.md` new consumer-seeded file; `docs/reference/generated/core_targets.generated.md` auto-updated by `quality-docs-sync-core-targets`

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 MUST: the `.spec-kit/templates/blueprint/spec.md` template contains `NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.` [per Q-1 resolution]
- AC-002 MUST: the `.spec-kit/templates/blueprint/tasks.md` template contains a T-Axx block with T-A01 through T-A05; T-A02 explicitly names tags `wcag21a` and `wcag21aa` and `attachTo: document.body` [per Q-1 resolution]
- AC-003 MUST: the `.spec-kit/templates/blueprint/hardening_review.md` template contains an "Accessibility Gate" section with all six checklist items [per Q-1 resolution]
- AC-004 MUST: the `.spec-kit/templates/blueprint/traceability.md` template header row contains a `WCAG SC` column
- AC-005 MUST: `quality-spec-pr-ready` validates the Accessibility Gate section has no unchecked boxes for applicable specs [per Q-1 resolution]; `make infra-contract-test-fast` passes after implementation
- AC-006 MUST: `touchpoints-test-a11y` Make target resolves; `test_a11y.sh` script exists; axe scan uses explicit WCAG 2.1 AA tag array in `axe_page_scan.mjs`
- AC-007 MUST: `apps-a11y-smoke` Make target resolves; `make test-smoke-all-local --dry-run` includes `apps-a11y-smoke`
- AC-008 MUST: `axe_page_scan.mjs` source contains `wcag21a` and `wcag21aa` in the `runOnly.values` array; assertion verifiable by contract test string match
- AC-009 MUST: `axe_preset.ts` exports `WCAG21AA_AXE_CONFIG` with `values: ['wcag2a','wcag2aa','wcag21a','wcag21aa']`; contract test asserts string presence
- AC-010 MUST: `docs/platform/accessibility/acr.md` scaffold contains all 50 WCAG 2.1 A+AA success criteria rows (1.1.1 through 4.1.3) with SC, Name, Level columns pre-populated
- AC-011 MUST: `quality-a11y-acr-check` exits 1 when ACR missing, exits 1 when `Report date` is a placeholder, exits 1 when date is older than `ACR_STALENESS_DAYS` days, exits 0 when date is within window; unit-testable without live browser [per Q-2 resolution]
- AC-012 MUST: PR Packager skill runbook includes ACR review checklist item for UI-layer specs [per Q-1 resolution]

## Informative Notes (Non-Normative)
- Context: EAA (Directive 2019/882/EU) mandates EN 301 549 / WCAG 2.1 AA for private-sector digital products/services in the EU market; enforcement began June 2025. Blueprint currently has no a11y NFR, no standard axe test infrastructure, and no ACR scaffold — each consumer builds this independently, inconsistently, or not at all. This three-issue bundle closes all three structural gaps in one PR.
- Tradeoffs: Combining three issues into one PR increases review surface but eliminates the risk of shipping test infrastructure without the lifecycle gates or ACR trail, which would create a partial a11y system with no enforcement at spec time. The issues are tightly coupled (the quality gate in #238 validates the task block that references the test infrastructure from #239; the ACR gate in #240 references evidence from both).
- Clarifications: `@axe-core/playwright` is expected as a devDependency in the consumer touchpoints bootstrap; blueprint does not manage consumer package.json directly. Consumers adding `touchpoints-test-a11y` must add `@axe-core/playwright` to their `package.json` — document in touchpoints bootstrap guide.

## Explicit Exclusions
- Does NOT create `scripts/bin/blueprint/consumer_fitness_status.sh` — this is a separate feature warranting its own SDD work item (pending Q-2 resolution selecting Option B).
- Does NOT add a `layer:` field to `spec.md` template if Option B is selected for Q-1.
- Does NOT add `quality-a11y-acr-check` to `quality-ci-blueprint` (risk of false positives in blueprint's own CI where no consumer acr.md exists); scoped to consumer-side quality hooks.
- Does NOT implement `quality-a11y-acr-sync` automated W3C JSON fetch at CI time; criterion list is bundled statically.
- Does NOT migrate or validate existing consumer `hardening_review.md` or `traceability.md` files on blueprint upgrade.
