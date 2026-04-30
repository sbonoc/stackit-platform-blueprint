# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.
- **Current status**: Open questions resolved (Q-1: Option B — unconditional N/A opt-out; Q-2: Option B — wire into quality-hooks-fast). Awaiting SPEC_READY=true (sign-offs pending).

## Constitution Gates (Pre-Implementation)
- Simplicity gate: three slices of additive changes — template section additions, new Make targets and scripts, ACR scaffold and quality gate; no existing logic modified except `quality-spec-pr-ready` extension (unchecked-box validation) and `test-smoke-all-local` extension.
- Anti-abstraction gate: direct Make `.PHONY` targets and shell scripts; `axe_page_scan.mjs` is a single-purpose Node utility; `axe_preset.ts` exports a plain configuration object and one helper function; no wrapper layer or framework indirection.
- Integration-first testing gate: contract assertions in `test_quality_contracts.py` verify Make target existence, script existence, and template content strings before consumer integration is possible; `check_acr_freshness.py` is unit-testable without a live browser.
- Positive-path filter/transform test gate: not applicable — no filter or payload-transform logic introduced.
- Finding-to-test translation gate: the missing a11y gates are not currently failing automated tests; new contract assertions (AC-001 through AC-012) translate the structural gaps into failing assertions before fixes are applied, then turn green with each implementation slice.

## Delivery Slices

### Slice 1 — SDD lifecycle template updates (Issue #238)
1. Edit `.spec-kit/templates/blueprint/spec.md`: add `NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.` to the standard NFR section (FR-101); unconditional — authors in non-UI specs write "N/A".
2. Edit `.spec-kit/templates/blueprint/tasks.md`: add T-Axx accessibility task block (T-A01 through T-A05) (FR-102); T-A02 MUST explicitly name `['wcag2a','wcag2aa','wcag21a','wcag21aa']` and `attachTo: document.body`.
3. Edit `.spec-kit/templates/blueprint/hardening_review.md`: add "Accessibility Gate" mandatory section with six checklist items (SC references: 4.1.2, 2.1.1, 2.4.7, 1.4.1, 3.3.1; plus axe-core scan evidence line) (FR-103); unconditional — non-UI reviewers mark non-applicable items N/A.
4. Edit `.spec-kit/templates/blueprint/traceability.md`: add `WCAG SC` column to the requirement-to-delivery mapping table header (FR-104).
5. Update `scripts/bin/platform/quality/check_spec_pr_ready.py`: validate Accessibility Gate section has no unchecked (non-N/A) boxes in `hardening_review.md` (FR-105).
6. Add contract test assertions in `tests/blueprint/test_quality_contracts.py` verifying template content strings — red phase before template edits, green phase after.

### Slice 2 — Test infrastructure (Issue #239)
1. Add `touchpoints-test-a11y` target to `make/platform.mk` with backing `scripts/bin/platform/touchpoints/test_a11y.sh` (FR-201).
2. Add `apps-a11y-smoke` target to `make/platform.mk` with backing `scripts/bin/platform/apps/a11y_smoke.sh` (FR-202).
3. Write `scripts/lib/platform/touchpoints/axe_page_scan.mjs` using `@axe-core/playwright` with explicit `['wcag2a','wcag2aa','wcag21a','wcag21aa']` tag array; write `artifacts/a11y/axe-report.json`; exit non-zero on `A11Y_FAIL_ON_IMPACT` violations (FR-203).
4. Write `scripts/lib/platform/touchpoints/axe_preset.ts` exporting `WCAG21AA_AXE_CONFIG` and `assertAxeWcag21AA`; include `attachTo: document.body` precondition documentation (FR-204).
5. Extend `test-smoke-all-local` in `make/platform.mk` to include `apps-a11y-smoke` (FR-205).
6. Add contract test assertions verifying target existence, script existence, and `wcag21a`/`wcag21aa` string presence in `axe_page_scan.mjs` — red phase before implementation, green phase after.
7. Run `make quality-docs-sync-core-targets` — verify new targets appear in `docs/reference/generated/core_targets.generated.md`.

### Slice 3 — ACR scaffold and quality gate (Issue #240)
1. Write `docs/platform/accessibility/acr.md` with VPAT 2.4 structure; pre-populate all 50 WCAG 2.1 A+AA criterion rows (SC 1.1.1 through 4.1.3) (FR-301).
2. Add `quality-a11y-acr-check` target to `make/platform.mk` backed by `scripts/bin/platform/quality/check_acr_freshness.py` (FR-302).
3. Add `quality-a11y-acr-sync` target backed by `scripts/bin/platform/quality/sync_acr_criteria.py` with bundled W3C criterion list (FR-303).
4. Add `acr_staleness_days: 90` to `blueprint/contract.yaml` under `spec.quality.accessibility`.
5. Wire `quality-a11y-acr-check` into `quality-hooks-fast` in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; run `make blueprint-render-makefile` to sync `make/blueprint.generated.mk` (FR-305).
6. Update `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` to include ACR review checklist item (FR-304).
7. Add contract tests asserting: `acr.md` scaffold criterion rows; `check_acr_freshness.py` script existence; `quality-a11y-acr-check` Make target existence; `quality-hooks-fast` includes `quality-a11y-acr-check`.
8. Run `make quality-docs-sync-core-targets` — verify ACR-related targets appear in `core_targets.generated.md`.

## Change Strategy
- Migration/rollout sequence: Slice 1 (template gates, red→green) → Slice 2 (test infrastructure, red→green) → Slice 3 (ACR scaffold and gate, red→green) → docs sync → quality gates → ADR → publish
- Backward compatibility policy: all template changes are additive; existing consumer-owned `spec.md`, `tasks.md`, `hardening_review.md`, `traceability.md` files are not modified on upgrade. New Make targets are additive. `acr.md` is a new consumer-seeded file; existing repos receive it on next `make blueprint-upgrade-consumer`.
- Rollback plan: revert template diffs; revert `make/platform.mk` target additions; remove new scripts; revert `blueprint/contract.yaml` addition; revert `quality-spec-pr-ready` extension; revert `quality-hooks-fast` extension; run `make blueprint-render-makefile` to re-sync generated file. No data migration or runtime state to reverse.

## Validation Strategy (Shift-Left)
- Unit checks: `make test-unit-all` after each slice red phase (assert fails) and green phase (assert passes)
- Contract checks: `make infra-contract-test-fast` — verifies template content, Make target existence, script existence
- Integration checks: `make quality-docs-sync-core-targets` — verifies new targets are reflected in generated reference docs; `make quality-spec-pr-ready` — verifies Accessibility Gate validation extension
- E2E checks: `make test-smoke-all-local --dry-run` to confirm `apps-a11y-smoke` is included; full axe scan against a live consumer app is out-of-scope for this blueprint CI

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact on the required minimum targets; new targets (`touchpoints-test-a11y`, `apps-a11y-smoke`) are additive alongside the existing ladder.
- Notes: `touchpoints-test-a11y` requires `@axe-core/playwright` as a consumer devDependency; document in touchpoints bootstrap guide. `apps-a11y-smoke` is included in `test-smoke-all-local` which is in scope for HTTP route/filter change smoke gates.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260430-issue-238-239-240-a11y-compliance.md`; no blueprint narrative docs update required beyond ADR.
- Consumer docs updates: `docs/platform/accessibility/acr.md` (new consumer-seeded file); touchpoints bootstrap guide updated to document `@axe-core/playwright` prerequisite and `axe_preset.ts` usage; `docs/reference/generated/core_targets.generated.md` auto-updated by `quality-docs-sync-core-targets`.
- Mermaid diagrams updated: `architecture.md` bounded context section (this file); no separate Docusaurus diagram update required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP route, query/filter, or API endpoint in scope. `test-smoke-all-local` extension is validated by dry-run Make invocation.
- Publish checklist:
  - include requirement/contract coverage (FR-101–FR-105, FR-201–FR-205, FR-301–FR-305, NFR-EAA-001, NFR-REL-001, NFR-OPS-001, NFR-TEST-001, AC-001–AC-012)
  - include key reviewer files (template diffs, new scripts, axe_preset.ts, acr.md, quality-spec-pr-ready extension, ADR)
  - include validation evidence (make test-unit-all, make infra-contract-test-fast, make quality-sdd-check)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: `axe_page_scan.mjs` writes structured JSON per route to `artifacts/a11y/`; `check_acr_freshness.py` diagnostic output is self-describing; no structured log fields, metrics, or traces added.
- Alerts/ownership: no alerting change; CI failure via `quality-hooks-fast` surfaces ACR staleness before merge.
- Runbook updates: touchpoints bootstrap guide; PR Packager skill runbook (ACR review step).

## Risks and Mitigations
- Risk 1: consumer missing `@axe-core/playwright` — axe_page_scan.mjs fails with import error → mitigation: clear error message; document prerequisite in bootstrap guide; `touchpoints-test-a11y` can be skipped until dependency is added.
- Risk 2: ACR staleness gate immediately fails on consumer adoption → mitigation: `ACR_STALENESS_GRACE_DAYS` grace window (configurable); document adoption path.
- Risk 3: non-UI specs receive a11y NFR and task block they must explicitly mark N/A → mitigation: template includes inline N/A guidance; small author overhead accepted as the cost of keeping scope self-contained (Option B decision).
