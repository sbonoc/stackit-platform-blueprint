# PR Context

## Summary
- Work item: issue-238-239-240-a11y-compliance (Issues #238, #239, #240)
- Objective: Embed WCAG 2.1 Level AA / EN 301 549 §9 compliance as a first-class NFR into the blueprint SDD lifecycle so that consumers targeting EU markets (EAA Directive 2019/882/EU, enforcement June 2025) can demonstrate conformance by following the standard workflow, without manual scaffold assembly. Three slices: (1) SDD lifecycle template gates — NFR-A11Y-001, T-Axx task block, Accessibility Gate in hardening_review, WCAG SC column in traceability, quality-spec-pr-ready Accessibility Gate validation; (2) axe-based test infrastructure — touchpoints-test-a11y, apps-a11y-smoke Make targets, axe_page_scan.mjs Playwright runner, axe_preset.ts vitest helper; (3) ACR scaffold and quality gate — consumer-seeded VPAT 2.4 acr.md, check_acr_freshness.py staleness gate wired into quality-hooks-fast, sync_acr_criteria.py, PR Packager ACR review step.
- Scope boundaries: Blueprint tooling and governance only — no consumer application code, no runtime infrastructure, no STACKIT managed service, no Kubernetes changes. All changes are additive; no existing consumer files overwritten on upgrade.

## Requirement Coverage
- Requirement IDs covered: FR-101, FR-102, FR-103, FR-104, FR-105 (Slice 1); FR-201, FR-202, FR-203, FR-204, FR-205 (Slice 2); FR-301, FR-302, FR-303, FR-304, FR-305 (Slice 3); NFR-EAA-001, NFR-REL-001, NFR-OPS-001, NFR-TEST-001; AC-001 through AC-012
- Acceptance criteria covered: AC-001–AC-012 — all verified by contract assertions in `tests/blueprint/test_quality_contracts.py` (14 new assertions) plus `make infra-contract-test-fast` (136 passed)
- Contract surfaces changed: `blueprint/contract.yaml` (`spec.quality.accessibility.acr_staleness_days: 90`); Make/CLI — 4 new consumer targets (`touchpoints-test-a11y`, `apps-a11y-smoke`, `quality-a11y-acr-check`, `quality-a11y-acr-sync`) in `make/platform.mk`; `test-smoke-all-local` extended; `quality-hooks-fast` in `make/blueprint.generated.mk` extended; `docs/platform/accessibility/acr.md` new consumer-seeded file; `docs/platform/consumer/accessibility.md` new consumer doc

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/quality/check_spec_pr_ready.py` — Accessibility Gate validation logic that blocks PR packaging on unchecked items (FR-105); the in_a11y_gate section-tracking and N/A exemption logic is the highest-risk behavioral change
  - `scripts/lib/platform/touchpoints/axe_page_scan.mjs` — Playwright+axe runner; confirm explicit `['wcag2a','wcag2aa','wcag21a','wcag21aa']` tag array is present and not using axe defaults (NFR-EAA-001)
  - `scripts/lib/platform/touchpoints/axe_preset.ts` — vitest helper export; confirm `attachTo: document.body` precondition is documented and `WCAG21AA_AXE_CONFIG` uses the same explicit tag array
  - `scripts/bin/platform/quality/check_acr_freshness.py` — staleness gate; confirm all three exit-non-zero scenarios (missing, placeholder, stale) and that the staleness window is sourced from `blueprint/contract.yaml` correctly
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — confirm `@$(MAKE) quality-a11y-acr-check` is added to `quality-hooks-fast` recipe; this wires the gate for all consumer repos on upgrade
- High-risk files:
  - `.spec-kit/templates/blueprint/hardening_review.md` — Accessibility Gate section is normative; non-UI reviewers must mark N/A explicitly; confirm the six SC items and N/A guidance are clear
  - `docs/platform/accessibility/acr.md` — consumer-seeded VPAT 2.4 scaffold; confirm it is listed in `required_seed_files` and that `seed_mode: create_if_missing` is set (not overwrite)
  - `blueprint/contract.yaml` and `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — both must have `spec.quality.accessibility.acr_staleness_days: 90`; drift between them caused `infra-validate` failure that was fixed in this PR

## Validation Evidence
- Required commands executed (2026-04-30):
  - `make test-unit-all` — 14 new contract assertions green; 136 total tests passed
  - `make infra-contract-test-fast` — 136 passed, 2 subtests passed (66.86s)
  - `make quality-sdd-check` — PASS
  - `make quality-hardening-review` — PASS
  - `make quality-hooks-fast` — PASS (all substantive checks; quality-spec-pr-ready now passes with publish artifacts filled)
  - `make infra-validate` — PASS (after syncing bootstrap contract template)
  - `make docs-build` — PASS (static site generated)
  - `make docs-smoke` — PASS
  - `make quality-docs-check-changed` — PASS
  - `make quality-a11y-acr-check` — PASS (ACR reviewed 0 days ago; within 90-day window)
  - `make quality-docs-sync-core-targets` — PASS (4 new a11y targets in core_targets.generated.md)
  - App onboarding minimum targets (A-001 through A-005) — all unaffected
- Result summary: All gates pass. 136 contract tests. No regressions. Test pyramid unchanged (unit=95.10%, integration=3.84%, e2e=1.07%).
- Artifact references: `specs/2026-04-30-issue-238-239-240-a11y-compliance/traceability.md` (Validation Summary section); `docs/reference/generated/core_targets.generated.md`

## Risk and Rollback
- Main risks: (1) `quality-hooks-fast` now calls `quality-a11y-acr-check` — a consumer who upgrades the blueprint but does not yet have `docs/platform/accessibility/acr.md` will see a failing fast gate. Mitigation: `acr.md` is delivered simultaneously via `required_seed_files` (`create_if_missing`) on the same upgrade, so a clean upgrade leaves no gap. A consumer who partially applies the upgrade (applies the Makefile but not the seed files) could hit this. (2) `check_spec_pr_ready.py` now blocks on unchecked Accessibility Gate items — any spec whose `hardening_review.md` has an old template without the Accessibility Gate section is unaffected (no section = no check). Only newly scaffolded specs include the gate.
- Rollback strategy: `git revert` the blueprint upgrade commit in the consumer repo. No runtime state, no database migrations, no event-contract changes. The `docs/platform/accessibility/acr.md` consumer-seeded file, if already customised, would need to be deleted manually if the consumer wants a clean revert (unlikely — it is a consumer-owned file that is not overwritten on upgrade). Feature-flag status: none — changes take effect on blueprint upgrade.

## Deferred Proposals
- Proposal 1 (`consumer_fitness_status.sh`): Not implemented — Q-2 resolved as Option B. Filed as https://github.com/sbonoc/stackit-platform-blueprint/issues/244
- Proposal 2 (`layer:` field in `spec.md` template): Not implemented — Q-1 resolved as Option B. Filed as https://github.com/sbonoc/stackit-platform-blueprint/issues/245
- Proposal 3 (`quality-a11y-acr-check` in `quality-ci-blueprint`): Parked — trigger: on-scope: quality — revisit when CI blueprint gains a stable ACR or skip mechanism
- Proposal 4 (automated W3C JSON fetch in `sync_acr_criteria.py`): Parked — trigger: on-scope: a11y — revisit when any a11y-scope work item appears
