# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-101 | SDD-C-005, SDD-C-008 | `NFR-A11Y-001` line in spec.md template (unconditional; N/A opt-out for non-UI) | `.spec-kit/templates/blueprint/spec.md` | `test_quality_contracts.py::test_spec_template_exposes_a11y_nfr` | ADR-20260430-issue-238-239-240-a11y-compliance.md | newly scaffolded specs include NFR-A11Y-001 |
| FR-102 | SDD-C-005, SDD-C-008 | T-Axx task block with wcag21aa and attachTo: document.body (unconditional) | `.spec-kit/templates/blueprint/tasks.md` | same test class | same ADR | newly scaffolded tasks.md includes T-A02 with explicit WCAG 2.1 AA ruleset |
| FR-103 | SDD-C-005, SDD-C-008 | "Accessibility Gate" section in hardening_review.md template (unconditional) | `.spec-kit/templates/blueprint/hardening_review.md` | same test class | same ADR | newly scaffolded hardening_review.md includes Accessibility Gate checklist |
| FR-104 | SDD-C-005, SDD-C-008 | `WCAG SC` column header in traceability.md template (unconditional) | `.spec-kit/templates/blueprint/traceability.md` | same test class | same ADR | newly scaffolded traceability.md includes WCAG SC column |
| FR-105 | SDD-C-008, SDD-C-012 | `check_spec_pr_ready.py` Accessibility Gate validation (no unchecked non-N/A boxes) | `scripts/bin/platform/quality/check_spec_pr_ready.py` | `make infra-contract-test-fast` contract suite | ADR | `quality-spec-pr-ready` blocks PR packaging on unchecked Accessibility Gate items |
| FR-201 | SDD-C-005, SDD-C-008 | `touchpoints-test-a11y` Make target + `test_a11y.sh` | `make/platform.mk`; `scripts/bin/platform/touchpoints/test_a11y.sh` | contract test: target and script existence | `docs/reference/generated/core_targets.generated.md` | target resolves; runs axe page scan |
| FR-202 | SDD-C-005, SDD-C-008 | `apps-a11y-smoke` Make target + `a11y_smoke.sh` | `make/platform.mk`; `scripts/bin/platform/apps/a11y_smoke.sh` | contract test: target and script existence | `core_targets.generated.md` | target resolves; included in `test-smoke-all-local` |
| FR-203 | SDD-C-008 | `axe_page_scan.mjs` with explicit WCAG 2.1 AA tag array | `scripts/lib/platform/touchpoints/axe_page_scan.mjs` | contract test: `wcag21a` and `wcag21aa` string present in file | ADR | writes `artifacts/a11y/axe-report.json`; exits non-zero on impact violations |
| FR-204 | SDD-C-008 | `axe_preset.ts` exporting `WCAG21AA_AXE_CONFIG` | `scripts/lib/platform/touchpoints/axe_preset.ts` | contract test: `WCAG21AA_AXE_CONFIG` string present in file | ADR (consumer adoption guide) | importable by consumer vitest-axe setup |
| FR-205 | SDD-C-005, SDD-C-008 | `test-smoke-all-local` extended to include `apps-a11y-smoke` | `make/platform.mk` | contract test: `apps-a11y-smoke` present in `test-smoke-all-local` recipe | `core_targets.generated.md` | `make test-smoke-all-local --dry-run` includes `apps-a11y-smoke` |
| FR-301 | SDD-C-005, SDD-C-011 | `acr.md` consumer-seeded VPAT 2.4 scaffold | `docs/platform/accessibility/acr.md` | contract test: file exists; SC `4.1.3` row present | ADR; `docs/platform/accessibility/acr.md` itself | seeded on consumer init; not overwritten on upgrade |
| FR-302 | SDD-C-008, SDD-C-012 | `quality-a11y-acr-check` + `check_acr_freshness.py` | `make/platform.mk`; `scripts/bin/platform/quality/check_acr_freshness.py` | unit test: exit codes for missing/stale/fresh ACR | `core_targets.generated.md` | exits non-zero with diagnostic message on stale/missing ACR |
| FR-303 | SDD-C-005 | `quality-a11y-acr-sync` + `sync_acr_criteria.py` | `make/platform.mk`; `scripts/bin/platform/quality/sync_acr_criteria.py` | contract test: target and script existence | `core_targets.generated.md` | regenerates criterion rows from bundled W3C list |
| FR-304 | SDD-C-016 | PR Packager skill ACR review checklist item | `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` | `quality-spec-pr-ready` validation | skill runbook | PR Packager skill prompts ACR review for UI-facing specs |
| FR-305 | SDD-C-012 | `quality-a11y-acr-check` wired into `quality-hooks-fast` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; `make/blueprint.generated.mk` | contract test: `quality-a11y-acr-check` present in `quality-hooks-fast` recipe | — | `quality-hooks-fast` blocks on stale/missing ACR |
| NFR-EAA-001 | SDD-C-008 | Explicit WCAG 2.1 AA tag array in axe runner and preset | `axe_page_scan.mjs`; `axe_preset.ts` | AC-008, AC-009 contract assertions | ADR Option decision | all axe scans use `['wcag2a','wcag2aa','wcag21a','wcag21aa']`; no scan passes on default ruleset |
| NFR-REL-001 | SDD-C-012 | Additive-only template and Make changes; consumer-seeded files not overwritten | all template files; `make/platform.mk` | full test suite passes unchanged (`make test-unit-all`); no existing assertions modified | — | zero behavior change for consumers who do not adopt new targets |
| NFR-OPS-001 | SDD-C-012 | `acr_staleness_days` in `blueprint/contract.yaml`; diagnostic output | `blueprint/contract.yaml`; `check_acr_freshness.py` | unit test: staleness threshold applied correctly; diagnostic message includes days elapsed | — | diagnostic output names file path, configured window, days elapsed, and remediation action |
| NFR-TEST-001 | SDD-C-008 | Contract assertions on file existence and string presence | `tests/blueprint/test_quality_contracts.py`; `tests/platform/` | `make infra-contract-test-fast` — all new assertions pass | — | no live browser required for any contract assertion |
| AC-001 | SDD-C-012 | `NFR-A11Y-001` string in spec.md template | `.spec-kit/templates/blueprint/spec.md` | `test_spec_template_exposes_a11y_nfr` | — | — |
| AC-002 | SDD-C-012 | `wcag21aa` and `attachTo: document.body` strings in tasks.md template | `.spec-kit/templates/blueprint/tasks.md` | `test_tasks_template_exposes_a11y_task_block` | — | — |
| AC-003 | SDD-C-012 | `Accessibility Gate` string in hardening_review.md template | `.spec-kit/templates/blueprint/hardening_review.md` | `test_hardening_review_template_exposes_accessibility_gate` | — | — |
| AC-004 | SDD-C-012 | `WCAG SC` string in traceability.md template header | `.spec-kit/templates/blueprint/traceability.md` | `test_traceability_template_exposes_wcag_sc_column` | — | — |
| AC-005 | SDD-C-012 | `check_spec_pr_ready.py` Accessibility Gate validation | `check_spec_pr_ready.py` | `make infra-contract-test-fast` | — | — |
| AC-006 | SDD-C-012 | `touchpoints-test-a11y` target; `test_a11y.sh` exists | `make/platform.mk`; `scripts/bin/platform/touchpoints/test_a11y.sh` | contract test: target resolution; script file existence | — | — |
| AC-007 | SDD-C-012 | `apps-a11y-smoke` target; `test-smoke-all-local` includes it | `make/platform.mk` | contract test: both assertions | — | — |
| AC-008 | SDD-C-012 | `wcag21a` and `wcag21aa` in `axe_page_scan.mjs` | `scripts/lib/platform/touchpoints/axe_page_scan.mjs` | contract test: string presence | — | — |
| AC-009 | SDD-C-012 | `WCAG21AA_AXE_CONFIG` in `axe_preset.ts` | `scripts/lib/platform/touchpoints/axe_preset.ts` | contract test: string presence | — | — |
| AC-010 | SDD-C-012 | `acr.md` scaffold exists with SC `4.1.3` row | `docs/platform/accessibility/acr.md` | contract test: file existence; SC row | — | — |
| AC-011 | SDD-C-012 | `check_acr_freshness.py` exit codes; `quality-a11y-acr-check` wired into `quality-hooks-fast` | `scripts/bin/platform/quality/check_acr_freshness.py`; `make/blueprint.generated.mk` | unit test: three exit-code scenarios; contract test: recipe inclusion | — | — |
| AC-012 | SDD-C-012 | PR Packager skill runbook contains ACR review item | `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` | manual runbook review | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-101, FR-102, FR-103, FR-104, FR-105, FR-201, FR-202, FR-203, FR-204, FR-205, FR-301, FR-302, FR-303, FR-304, FR-305, NFR-EAA-001, NFR-REL-001, NFR-OPS-001, NFR-TEST-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012

## Validation Summary
- Required bundles executed:
- Result summary: pending — SPEC_READY=false (sign-offs pending)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: identify other WCAG 2.1 criterion table sources to ensure `sync_acr_criteria.py` stays current with W3C errata
- Follow-up (parked): create `consumer_fitness_status.sh` in a standalone work item when additional consumer fitness checks are identified beyond the ACR check
- Follow-up (parked): add `layer:` field to `spec.md` template in a standalone cross-cutting work item
