# Architecture

## Context
- Work item: 2026-04-30-issue-238-239-240-a11y-compliance
- Owner: bonos
- Date: 2026-04-30

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: The blueprint SDD lifecycle has no first-class accessibility (a11y) support. There is no standard NFR for WCAG 2.1 AA; no task block prompting axe scans with the correct ruleset; no hardening checklist section for keyboard operability, focus visibility, or programmatic labels; no WCAG SC column in traceability for EAA compliance evidence; no shared axe preset enforcing the explicit `wcag21a`/`wcag21aa` tags; no full-page axe scan infrastructure; and no Accessibility Conformance Report (ACR) scaffold or staleness gate. EU consumers subject to EAA (Directive 2019/882/EU, enforcement June 2025) must build this infrastructure ad-hoc or leave conformance undeclared.
- Scope boundaries: SDD lifecycle template files (`.spec-kit/templates/blueprint/`); platform Make targets (`make/platform.mk`); quality check scripts (`scripts/bin/platform/quality/`); touchpoints scripts and library files (`scripts/bin/platform/touchpoints/`, `scripts/lib/platform/touchpoints/`); ACR scaffold (`docs/platform/accessibility/acr.md`); PR Packager skill runbook.
- Out of scope: consumer-owned `hardening_review.md` and `traceability.md` files (not overwritten on upgrade); `consumer_fitness_status.sh` (separate work item if Q-2 resolves to Option A); `layer:` conditional field in spec.md template (separate work item if Q-1 resolves to Option A with deferral).

## Bounded Contexts and Responsibilities

- **Blueprint SDD lifecycle context** (issue #238): `.spec-kit/templates/blueprint/` — scaffold files are the canonical source; all consumer SDD artifacts are seeded from these templates. Changes here propagate to new work items only; existing artifacts are consumer-owned and unaffected. `quality-spec-pr-ready` enforces structure at publish time.
- **Platform test infrastructure context** (issue #239): `make/platform.mk`, `scripts/bin/platform/touchpoints/`, `scripts/bin/platform/apps/`, `scripts/lib/platform/touchpoints/` — blueprint-managed scripts consumed by consumers in their CI and smoke lanes. `axe_preset.ts` is importable by consumer vitest-axe setup; `axe_page_scan.mjs` is the Playwright runner for full-page scans.
- **Accessibility Conformance Report context** (issue #240): `docs/platform/accessibility/acr.md` — consumer-seeded file; writable by consumer after initial seeding; not overwritten on blueprint upgrade. `quality-a11y-acr-check` is blueprint-managed and validates the file regardless of content; `quality-a11y-acr-sync` regenerates the criterion list from a bundled W3C source.

## High-Level Component Design

- Domain layer: WCAG 2.1 AA compliance obligation and EAA mandate; represented as NFR-A11Y-001 in spec.md and as VPAT 2.4 criterion table in acr.md.
- Application layer: `check_acr_freshness.py` (ACR staleness logic), `sync_acr_criteria.py` (criterion regeneration), `check_spec_pr_ready.py` (Accessibility Gate validation extension), `axe_page_scan.mjs` (Playwright+axe runner), `axe_preset.ts` (shared configuration export).
- Infrastructure adapters: Make targets (`touchpoints-test-a11y`, `apps-a11y-smoke`, `quality-a11y-acr-check`, `quality-a11y-acr-sync`) as the invocation boundary; `test_a11y.sh` and `a11y_smoke.sh` as thin shell wrappers. `@axe-core/playwright` as the browser automation layer (consumer devDependency).
- Presentation/API/workflow boundaries: `make/platform.mk` Make target definitions; `quality-spec-pr-ready` publish gate; PR Packager skill runbook.

## Integration and Dependency Edges

- Upstream dependencies: `@axe-core/playwright` (consumer devDependency, not blueprint-managed); `axe-core` + `vitest-axe` (expected in consumer touchpoints bootstrap); Playwright (already present for `touchpoints-test-e2e`). Bundled W3C WCAG 2.1 criteria list for `sync_acr_criteria.py`.
- Downstream dependencies: `test-smoke-all-local` extended to include `apps-a11y-smoke`; `quality-hooks-fast` (or equivalent, pending Q-2) extended to include `quality-a11y-acr-check`; `docs/reference/generated/core_targets.generated.md` auto-updated by `quality-docs-sync-core-targets`.
- Data/API/event contracts touched: `blueprint/contract.yaml` — new key `spec.quality.accessibility.acr_staleness_days` (default: 90). Make/CLI contract: four new `.PHONY` targets; one extended target (`test-smoke-all-local`).

## Non-Functional Architecture Notes

- Security: no authn/authz or secret handling introduced; `axe_page_scan.mjs` runs against locally accessible URLs only; `check_acr_freshness.py` reads a local file. No new attack surface.
- Observability: `check_acr_freshness.py` diagnostic output names the file path, configured staleness window, days elapsed, and remediation action — self-documenting error messages per NFR-OPS-001. `axe_page_scan.mjs` writes structured `axe-report.json` per route for CI artifact collection.
- Reliability and rollback: all template changes are additive (new sections/columns appended); rollback by reverting the template diff. Make targets are additive; rollback removes the target definitions. `acr.md` is consumer-seeded; rollback deletes the seed on next consumer upgrade if rejected. No database or runtime state involved.
- Monitoring/alerting: `quality-a11y-acr-check` gates PR packaging for UI-layer specs; CI failure surfaces staleness before merge. No paging or alerting change required.

## Risks and Tradeoffs

- Risk 1: `@axe-core/playwright` not present in consumer devDependencies → `axe_page_scan.mjs` fails with module-not-found error. Mitigation: document prerequisite in touchpoints bootstrap guide; the script emits a clear error on import failure.
- Risk 2: ACR staleness gate initially fails for all consumers who adopt `acr.md` without updating the `Report date` — could block PR packaging unexpectedly. Mitigation: `ACR_STALENESS_GRACE_DAYS` configurable (default: 30 day grace on first adoption); document in target help string.
- Tradeoff 1: Combining three issues into one PR increases review surface but ensures the a11y enforcement triangle (spec gate + test infrastructure + ACR trail) ships atomically. Shipping test infrastructure without the ACR or spec gates would create a partial system with no enforcement — deemed higher risk than a larger PR.
- Tradeoff 2: Unconditional a11y sections (Option B per agent recommendation) mean non-UI specs include an NFR that authors must explicitly declare N/A. This is a small author burden but avoids adding a `layer:` conditional mechanism out of scope for this work item.
