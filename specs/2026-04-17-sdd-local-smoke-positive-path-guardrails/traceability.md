# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-023 | Canonical plan template positive-path gate | `.spec-kit/templates/blueprint/plan.md`; `.spec-kit/templates/consumer/plan.md`; `scripts/templates/consumer/init/.spec-kit/templates/consumer/plan.md.tmpl` | `tests/blueprint/test_quality_contracts.py::test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates` | `docs/blueprint/governance/spec_driven_development.md` | `make quality-sdd-check` |
| FR-002 | SDD-C-022 | Canonical plan template local smoke publish gate | `.spec-kit/templates/blueprint/plan.md`; `.spec-kit/templates/consumer/plan.md`; `scripts/templates/consumer/init/.spec-kit/templates/consumer/plan.md.tmpl` | `tests/blueprint/test_quality_contracts.py::test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates` | `docs/blueprint/governance/assistant_compatibility.md` | `make quality-sdd-check` |
| FR-003 | SDD-C-023 | Canonical tasks template positive-path verification | `.spec-kit/templates/blueprint/tasks.md`; `.spec-kit/templates/consumer/tasks.md`; `scripts/templates/consumer/init/.spec-kit/templates/consumer/tasks.md.tmpl` | `tests/blueprint/test_quality_contracts.py::test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates` | `AGENTS.md`; `scripts/templates/consumer/init/AGENTS.md.tmpl` | `make quality-sdd-check` |
| FR-004 | SDD-C-020, SDD-C-022, SDD-C-023, SDD-C-024 | Assistant-agnostic governance policy alignment | `AGENTS.md`; `CLAUDE.md`; `docs/blueprint/governance/spec_driven_development.md`; `docs/blueprint/governance/assistant_compatibility.md`; mirrored blueprint docs template files | `make quality-docs-check-blueprint-template-sync` | `docs/blueprint/governance/spec_driven_development.md`; `docs/blueprint/governance/assistant_compatibility.md` | `make quality-sdd-check` |
| FR-005 | SDD-C-005 | Stable control-catalog extension and render sync | `.spec-kit/control-catalog.json`; `.spec-kit/control-catalog.md`; `scripts/templates/consumer/init/.spec-kit/control-catalog.json.tmpl`; `scripts/templates/consumer/init/.spec-kit/control-catalog.md.tmpl` | `tests/blueprint/test_quality_contracts.py::test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls` | `.spec-kit/policy-mapping.md`; `scripts/templates/consumer/init/.spec-kit/policy-mapping.md.tmpl` | `make quality-sdd-check-control-catalog-sync` |
| FR-006 | SDD-C-024 | Red->green finding translation gate in templates and policy | `.spec-kit/templates/blueprint/plan.md`; `.spec-kit/templates/consumer/plan.md`; `.spec-kit/templates/blueprint/tasks.md`; `.spec-kit/templates/consumer/tasks.md`; `.spec-kit/control-catalog.json` | `tests/blueprint/test_quality_contracts.py::test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates`; `tests/blueprint/test_quality_contracts.py::test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls` | `AGENTS.md`; `docs/blueprint/governance/spec_driven_development.md` | `make quality-sdd-check` |
| NFR-SEC-001 | SDD-C-023, SDD-C-024 | Empty-result-only rejection and red->green requirement | `.spec-kit/templates/blueprint/plan.md`; `.spec-kit/templates/consumer/plan.md`; `.spec-kit/templates/blueprint/tasks.md`; `.spec-kit/templates/consumer/tasks.md` | targeted `test_quality_contracts` tests | governance docs and AGENTS surfaces | `make quality-sdd-check` |
| NFR-OBS-001 | SDD-C-022 | Deterministic local smoke evidence schema | `.spec-kit/templates/blueprint/plan.md`; `.spec-kit/templates/consumer/plan.md` | targeted `test_quality_contracts` template marker test | `docs/blueprint/governance/assistant_compatibility.md` | `make quality-sdd-check` |
| NFR-REL-001 | SDD-C-012 | Canonical/mirror synchronization determinism | `scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py` outputs; `scripts/lib/docs/sync_blueprint_template_docs.py` outputs | `python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py --check`; `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check` | template mirror files listed above | `make quality-sdd-check-all` |
| NFR-OPS-001 | SDD-C-010 | Canonical command-only validation and publish evidence readiness | `plan.md`; `tasks.md`; `pr_context.md`; `hardening_review.md` | required make/test bundles listed below | `pr_context.md`; `hardening_review.md` | `make infra-validate` |
| AC-001 | SDD-C-022, SDD-C-023 | Plan markers for positive-path and local smoke gates | `.spec-kit/templates/blueprint/plan.md`; `.spec-kit/templates/consumer/plan.md` | `test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates` | mirrored consumer-init plan template | `make quality-sdd-check` |
| AC-002 | SDD-C-023 | Tasks markers for positive-path verification | `.spec-kit/templates/blueprint/tasks.md`; `.spec-kit/templates/consumer/tasks.md` | `test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates` | mirrored consumer-init tasks template | `make quality-sdd-check` |
| AC-003 | SDD-C-005 | Catalog IDs `SDD-C-022` and `SDD-C-023` | `.spec-kit/control-catalog.json`; `.spec-kit/control-catalog.md` | `test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls` | consumer-init catalog templates | `make quality-sdd-check-control-catalog-sync` |
| AC-004 | SDD-C-020 | Governance surfaces include guardrails | `AGENTS.md`; `CLAUDE.md`; governance docs + mirrors; consumer-init `AGENTS.md.tmpl` | docs/template sync checks | governance docs | `make quality-docs-check-blueprint-template-sync` |
| AC-005 | SDD-C-012 | Validation bundles pass for changed scope | validation command set in summary below | command outputs listed below | `traceability.md` + `evidence_manifest.json` | `make infra-validate` |
| AC-006 | SDD-C-024 | Red->green translation gate appears in templates and controls | plan/tasks templates + control catalog source/render | targeted `test_quality_contracts` tests | `AGENTS.md`; governance docs | `make quality-sdd-check` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file has a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates tests.blueprint.test_quality_contracts.QualityContractsTests.test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls`
  - `python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py --check`
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`
  - `make quality-sdd-check`
  - `make quality-sdd-check-all`
  - `make quality-docs-check-blueprint-template-sync`
  - `make quality-hooks-run`
  - `make infra-validate`
  - `make quality-hardening-review`
- Result summary: all commands listed above passed on branch `codex/2026-04-17-sdd-local-smoke-positive-path-guardrails`.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: add static linting for work-item-level enforcement of red->green finding translation when scope labels indicate HTTP/filter behavior.
