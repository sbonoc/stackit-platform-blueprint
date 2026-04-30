# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008 | N/A | `pnpm-lockfile-sync` pre-push hook in `.pre-commit-config.yaml` bootstrap template | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_template_has_pnpm_lockfile_sync_hook` | `docs/blueprint/governance/quality_hooks.md`; ADR | hook triggers on pre-push when package.json changes |
| FR-002 | SDD-C-005, SDD-C-008 | N/A | `files: (^|/)package\.json$` pattern in `pnpm-lockfile-sync` hook | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_template_pnpm_lockfile_sync_covers_workspace` | ADR | covers root and sub-package manifests |
| FR-003 | SDD-C-005, SDD-C-008 | N/A | `quality-consumer-pre-push: @true` no-op stub in `blueprint.generated.mk` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; `make/blueprint.generated.mk` | `test_make_template_has_quality_consumer_pre_push_stub` | `docs/blueprint/governance/quality_hooks.md`; `docs/platform/consumer/consumer_quality_gates.md` | target resolves to no-op by default; consumer overrides in `platform.mk` |
| FR-004 | SDD-C-005, SDD-C-008 | N/A | `quality-consumer-ci: @true` no-op stub in `blueprint.generated.mk` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; `make/blueprint.generated.mk` | `test_make_template_has_quality_consumer_ci_stub` | `docs/blueprint/governance/quality_hooks.md`; `docs/platform/consumer/consumer_quality_gates.md` | target resolves to no-op by default; consumer overrides in `platform.mk` |
| FR-005 | SDD-C-005, SDD-C-008 | N/A | `quality-consumer-pre-push` pre-push hook in `.pre-commit-config.yaml` bootstrap template | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_template_has_quality_consumer_pre_push_hook` | `docs/platform/consumer/consumer_quality_gates.md` | hook fires at pre-push and calls `make quality-consumer-pre-push` |
| FR-006 | SDD-C-005, SDD-C-008 | N/A | `@$(MAKE) quality-consumer-ci` final step in `quality-ci-blueprint` recipe | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; `make/blueprint.generated.mk` | `test_quality_ci_blueprint_calls_quality_consumer_ci` | `docs/blueprint/governance/quality_hooks.md` | `quality-ci-blueprint` always invokes consumer CI extension |
| FR-007 | SDD-C-005, SDD-C-008 | N/A | `quality-consumer-pre-push` and `quality-consumer-ci` documented with tier placement in `AGENTS.md.tmpl` | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `test_agents_md_template_has_consumer_extension_targets` | `scripts/templates/consumer/init/AGENTS.md.tmpl` | consumers install the template and get tier placement documentation on `blueprint-init-repo` |
| NFR-REL-001 | SDD-C-012 | N/A | Additive-only changes; stubs are no-ops | all template files | full test suite passes unchanged; no existing assertions modified | — | zero behavior change for consumers who do not override stubs |
| NFR-UPG-001 | SDD-C-012 | N/A | Consumer overrides in `platform.mk` (consumer-owned) | `platform.mk` convention (consumer-owned) | — | `docs/platform/consumer/consumer_quality_gates.md` | consumers accumulate overrides in `platform.mk` without merge-conflict risk |
| NFR-A11Y-001 | SDD-C-005 | N/A | N/A — tooling and governance change; no UI components | — | — | — | — |
| AC-001 | SDD-C-012 | N/A | `pnpm-lockfile-sync` string + `stages: [pre-push]` + `files: (^|/)package\.json$` in bootstrap `.pre-commit-config.yaml` | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_template_has_pnpm_lockfile_sync_hook` | — | — |
| AC-002 | SDD-C-012 | N/A | `quality-consumer-pre-push` hook with `stages: [pre-push]` in bootstrap `.pre-commit-config.yaml` | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_template_has_quality_consumer_pre_push_hook` | — | — |
| AC-003 | SDD-C-012 | N/A | `quality-consumer-pre-push` target with `@true` body in `blueprint.generated.mk.tmpl` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `test_make_template_has_quality_consumer_pre_push_stub` | — | — |
| AC-004 | SDD-C-012 | N/A | `quality-consumer-ci` target with `@true` body in `blueprint.generated.mk.tmpl` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `test_make_template_has_quality_consumer_ci_stub` | — | — |
| AC-005 | SDD-C-012 | N/A | `$(MAKE) quality-consumer-ci` in `quality-ci-blueprint` recipe in `blueprint.generated.mk.tmpl` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `test_quality_ci_blueprint_calls_quality_consumer_ci` | — | — |
| AC-006 | SDD-C-012 | N/A | 6 new contract assertions in `test_quality_contracts.py` passing via `make infra-contract-test-fast` | `tests/blueprint/test_quality_contracts.py` | `make infra-contract-test-fast` | — | — |
| AC-007 | SDD-C-012 | N/A | `quality-consumer-pre-push` and `quality-consumer-ci` present with tier documentation in `AGENTS.md.tmpl` | `scripts/templates/consumer/init/AGENTS.md.tmpl` | `test_agents_md_template_has_consumer_extension_targets` | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-REL-001, NFR-UPG-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: `make infra-contract-test-fast` (136 passed, 2 subtests), `make quality-sdd-check` (PASS), `make quality-hardening-review` (PASS), `make infra-validate` (PASS — no drift), `make docs-build && make docs-smoke` (PASS), `make quality-hooks-fast` (all implementation checks PASS)
- Result summary: All 136 assertions pass including 7 new assertions; docs lint clean across 96 markdown files; no bootstrap template drift; hardening review PASS
- Documentation validation:
  - `make docs-build` — PASS
  - `make docs-smoke` — PASS

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None — consumer docs (`consumer_quality_gates.md`) completed at Document phase (T-302)
