# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0` (both resolved — Q-1: Option B, Q-2: Option B)
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes applicable `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — SDD lifecycle template updates, red phase (Issue #238)
- [x] T-101 Add contract test assertions in `tests/blueprint/test_quality_contracts.py` asserting:
      (a) `.spec-kit/templates/blueprint/spec.md` contains `NFR-A11Y-001`
      (b) `.spec-kit/templates/blueprint/tasks.md` contains `T-A02` and `wcag21aa`
      (c) `.spec-kit/templates/blueprint/hardening_review.md` contains `Accessibility Gate`
      (d) `.spec-kit/templates/blueprint/traceability.md` header contains `WCAG SC`
- [x] T-102 Confirm all new contract test assertions FAIL before template edits (red phase verified)

## Slice 1 — SDD lifecycle template updates, green phase (Issue #238)
- [x] T-001 Edit `.spec-kit/templates/blueprint/spec.md`: add `NFR-A11Y-001 MUST define WCAG 2.1 Level AA compliance scope and any known exceptions.` to the standard NFR section; include N/A guidance for non-UI specs (FR-101)
- [x] T-002 Edit `.spec-kit/templates/blueprint/tasks.md`: add T-Axx task block (T-A01 through T-A05); T-A02 MUST explicitly name `wcag21a` and `wcag21aa` tags and `attachTo: document.body` (FR-102)
- [x] T-003 Edit `.spec-kit/templates/blueprint/hardening_review.md`: add "Accessibility Gate" mandatory section with six checklist items referencing SC 4.1.2, 2.1.1, 2.4.7, 1.4.1, 3.3.1, and axe-core scan evidence; include N/A guidance for non-UI specs (FR-103)
- [x] T-004 Edit `.spec-kit/templates/blueprint/traceability.md`: add `WCAG SC` column to the requirement-to-delivery mapping header row (FR-104)
- [x] T-005 Update `scripts/bin/platform/quality/check_spec_pr_ready.py`: validate Accessibility Gate section has no unchecked (non-N/A) boxes in `hardening_review.md` (FR-105)
- [x] T-106 Run `make test-unit-all` — confirm T-101 assertions now PASS (green phase verified)

## Slice 2 — Test infrastructure, red phase (Issue #239)
- [x] T-103 Add contract test assertions verifying:
      (a) `make/platform.mk` contains `touchpoints-test-a11y` target
      (b) `scripts/bin/platform/touchpoints/test_a11y.sh` exists
      (c) `scripts/lib/platform/touchpoints/axe_page_scan.mjs` contains `wcag21a` and `wcag21aa`
      (d) `scripts/lib/platform/touchpoints/axe_preset.ts` contains `WCAG21AA_AXE_CONFIG`
      (e) `make/platform.mk` contains `apps-a11y-smoke` target
- [x] T-104 Confirm all new contract test assertions FAIL before implementation (red phase verified)

## Slice 2 — Test infrastructure, green phase (Issue #239)
- [x] T-006 Add `touchpoints-test-a11y` `.PHONY` target and definition to `make/platform.mk` (FR-201)
- [x] T-007 Write `scripts/bin/platform/touchpoints/test_a11y.sh` with `A11Y_BASE_URL`, `A11Y_ROUTES`, `A11Y_FAIL_ON_IMPACT` variables and `run_cmd node axe_page_scan.mjs` invocation (FR-201)
- [x] T-008 Add `apps-a11y-smoke` `.PHONY` target and definition to `make/platform.mk` (FR-202)
- [x] T-009 Write `scripts/bin/platform/apps/a11y_smoke.sh` wrapping `test_a11y.sh` with smoke-appropriate defaults (FR-202)
- [x] T-010 Write `scripts/lib/platform/touchpoints/axe_page_scan.mjs` with `@axe-core/playwright`, explicit `['wcag2a','wcag2aa','wcag21a','wcag21aa']` tag array, JSON report output, and human-readable violation summary (FR-203)
- [x] T-011 Write `scripts/lib/platform/touchpoints/axe_preset.ts` exporting `WCAG21AA_AXE_CONFIG` and `assertAxeWcag21AA`; include `attachTo: document.body` precondition note (FR-204)
- [x] T-012 Extend `test-smoke-all-local` in `make/platform.mk` to include `apps-a11y-smoke` (FR-205)
- [x] T-107 Run `make test-unit-all` — confirm T-103 assertions now PASS (green phase verified)
- [x] T-013 Run `make quality-docs-sync-core-targets` — verify new targets appear in `docs/reference/generated/core_targets.generated.md`

## Slice 3 — ACR scaffold and quality gate, red phase (Issue #240)
- [x] T-105 Add contract test assertions verifying:
      (a) `docs/platform/accessibility/acr.md` exists and contains SC `4.1.3` (last WCAG 2.1 AA criterion)
      (b) `scripts/bin/platform/quality/check_acr_freshness.py` exists
      (c) `make/platform.mk` contains `quality-a11y-acr-check` target
      (d) `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` contains `quality-a11y-acr-check` in `quality-hooks-fast`
- [x] T-108 Confirm all new contract test assertions FAIL before implementation (red phase verified)

## Slice 3 — ACR scaffold and quality gate, green phase (Issue #240)
- [x] T-014 Write `docs/platform/accessibility/acr.md` with VPAT 2.4 structure pre-populated with all 50 WCAG 2.1 A+AA criterion rows (1.1.1 through 4.1.3) (FR-301)
- [x] T-015 Add `acr_staleness_days: 90` to `blueprint/contract.yaml` under `spec.quality.accessibility`
- [x] T-016 Write `scripts/bin/platform/quality/check_acr_freshness.py` implementing: file-existence check; placeholder detection; staleness check against `ACR_STALENESS_DAYS`; clear diagnostic output per NFR-OPS-001 (FR-302)
- [x] T-017 Add `quality-a11y-acr-check` `.PHONY` target and definition to `make/platform.mk` (FR-302)
- [x] T-018 Write `scripts/bin/platform/quality/sync_acr_criteria.py` with bundled W3C criterion list; preserves existing support/notes/evidence content (FR-303)
- [x] T-019 Add `quality-a11y-acr-sync` `.PHONY` target and definition to `make/platform.mk` (FR-303)
- [x] T-020 Wire `quality-a11y-acr-check` into `quality-hooks-fast` in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; run `make blueprint-render-makefile` to sync `make/blueprint.generated.mk` (FR-305)
- [x] T-021 Update `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` to include ACR review checklist item (FR-304)
- [x] T-109 Run `make test-unit-all` — confirm T-105 assertions now PASS (green phase verified)
- [x] T-022 Run `make quality-docs-sync-core-targets` — verify ACR-related targets appear in `core_targets.generated.md`

## ADR and Architecture
- [x] T-201 Confirm `ADR-20260430-issue-238-239-240-a11y-compliance.md` is written and status updated to `approved` after sign-offs

## Validation and Release Readiness
- [x] T-202 Run `make infra-contract-test-fast` — all contract tests pass (136 passed)
- [x] T-203 Run `make quality-hooks-fast` — all substantive checks pass (quality-spec-pr-ready expected failure until publish; infra-validate fixed)
- [x] T-204 Run `make quality-sdd-check` — clean, no violations
- [x] T-205 Attach evidence to traceability document — fill Validation Summary in `traceability.md`
- [x] T-206 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [x] T-207 Run hardening review validation bundle (`make quality-hardening-review`)

## App Onboarding Minimum Targets (Normative)
- No-impact declared in `plan.md` for the required minimum targets. New targets are additive alongside the existing ladder.
- [x] A-001 Confirm `apps-bootstrap` and `apps-smoke` are operational and unaffected
- [x] A-002 Confirm `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are operational and unaffected
- [x] A-003 Confirm `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are operational and unaffected
- [x] A-004 Confirm `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are operational and unaffected
- [x] A-005 Confirm `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are operational and unaffected

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
