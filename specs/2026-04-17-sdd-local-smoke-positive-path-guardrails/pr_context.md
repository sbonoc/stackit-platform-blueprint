# PR Context

## Summary
- Work item: `specs/2026-04-17-sdd-local-smoke-positive-path-guardrails`
- Objective: enforce deterministic SDD guardrails for positive-path filter/transform coverage, local smoke evidence, and red->green regression translation for reproducible pre-PR findings.
- Scope boundaries: SDD templates, governance/interoperability docs, control catalog, sync mirrors, and regression tests.

## Requirement Coverage
- Requirements (FR/NFR): `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria (AC): `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`
- Traceability IDs present: `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`, `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `NFR-OBS-001`, `NFR-OPS-001`, `NFR-REL-001`, `NFR-SEC-001`

## Key Reviewer Files
- `.spec-kit/templates/blueprint/plan.md`
- `.spec-kit/templates/consumer/plan.md`
- `.spec-kit/templates/blueprint/tasks.md`
- `.spec-kit/templates/consumer/tasks.md`
- `.spec-kit/control-catalog.json`
- `.spec-kit/control-catalog.md`
- `AGENTS.md`
- `scripts/templates/consumer/init/AGENTS.md.tmpl`
- `docs/blueprint/governance/spec_driven_development.md`
- `docs/blueprint/governance/assistant_compatibility.md`
- `tests/blueprint/test_quality_contracts.py`

## Validation Evidence
- `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates tests.blueprint.test_quality_contracts.QualityContractsTests.test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls`
- `python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py --check`
- `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-docs-check-blueprint-template-sync`
- `make quality-hooks-run`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make quality-hardening-review`

## Risk and Rollback
- Risk notes:
  - Risk 1: stronger template gates increase authoring burden for HTTP/filter work.
  - Mitigation 1: provide deterministic evidence schema and explicit exceptions path.
  - Risk 2: mirror drift across canonical and consumer-init/docs templates.
  - Mitigation 2: enforce sync scripts and drift checks in the same change.
- Rollback notes:
  - revert this change set and rerun:
  - `make quality-sdd-check-all`
  - `make quality-docs-check-blueprint-template-sync`
  - `make infra-validate`

## Deferred Proposals
- Add scope-aware linting in `quality-sdd-check` to enforce local-smoke/red->green gates automatically for work items tagged as HTTP/filter scope.
- Add helper scaffold command to generate `Endpoint | Method | Auth | Result` tables directly in `pr_context.md`.
