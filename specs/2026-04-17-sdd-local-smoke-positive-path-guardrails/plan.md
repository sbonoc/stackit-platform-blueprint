# Implementation Plan

## Implementation Start Gate
- Implementation is allowed with `SPEC_READY=true` and all required sign-offs approved in `spec.md`.
- Missing-input blocker token remains documented but absent for this implementation-ready work item.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Limit scope to SDD templates, governance docs, control catalog, and regression tests.
  - Reuse existing sync/validation tooling and avoid adding new command surfaces.
- Anti-abstraction gate:
  - Update canonical markdown artifacts directly.
  - Keep control-catalog additions minimal (new IDs only for the new gates).
- Integration-first testing gate:
  - Add targeted regression tests for template and catalog guardrail markers before broad validation bundles.
- Positive-path filter/transform test gate:
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices
1. Slice 1: finalize Discover/Architecture/Specify artifacts and approve ADR path/readiness.
2. Slice 2: update canonical SDD templates (`plan.md`, `tasks.md`) for blueprint and consumer tracks.
3. Slice 3: update governance/interoperability docs and control catalog; regenerate rendered/synced mirrors.
4. Slice 4: add regression tests and execute validation bundles; finalize publish artifacts.

## Change Strategy
- Migration/rollout sequence:
  - update canonical `.spec-kit` templates and policy artifacts.
  - update governance docs and assistant interoperability surfaces.
  - regenerate control catalog and mirror sync outputs.
  - validate with targeted tests and required make bundles.
- Backward compatibility policy:
  - existing commands and branch/scaffold behavior remain unchanged.
- Rollback plan:
  - revert this work-item change set and rerun SDD/docs/infra validation targets.

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates`
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls`
- Contract checks:
  - `python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py --check`
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`
- Integration checks:
  - `make quality-sdd-check`
  - `make quality-sdd-check-all`
  - `make infra-validate`
- E2E checks:
  - not applicable for this governance/template-only scope.

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
- App onboarding impact: no-impact
- Notes: this work item updates SDD policy/templates only.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/governance/spec_driven_development.md`
  - `docs/blueprint/governance/assistant_compatibility.md`
  - `AGENTS.md`
  - `CLAUDE.md`
- Consumer docs updates:
  - `scripts/templates/consumer/init/AGENTS.md.tmpl`
  - consumer-init `.spec-kit` mirrors from sync tooling.
- Mermaid diagrams updated:
  - not required for this policy-only scope.
- Docs validation commands:
  - `make quality-docs-check-blueprint-template-sync`
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - For work that touches HTTP route handlers, query/filter logic, or new API endpoints, run local smoke before PR publication.
  - Execute local smoke with deterministic wrappers (`make infra-provision`, `make infra-deploy`, `make infra-port-forward-start`), then run positive-path `curl` assertions per changed endpoint.
  - Positive-path filter assertions MUST use non-empty fixture/request values; empty-result-only assertions MUST NOT satisfy this gate.
  - Record evidence in `pr_context.md` as `Endpoint | Method | Auth | Result`.
  - Stop/cleanup wrappers after smoke (`make infra-port-forward-stop`, `make infra-port-forward-cleanup`).
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces:
  - no runtime telemetry changes; diagnostics live in deterministic SDD evidence artifacts.
- Alerts/ownership:
  - failures surface through existing quality and infra validation gates in CI.
- Runbook updates:
  - no new operational runbook command is introduced.

## Risks and Mitigations
- Risk 1: template wording drift between canonical and consumer-init mirrors.
- Mitigation 1: enforce sync/check scripts and regression tests in the same change.
- Risk 2: assistants skip new gates when drafting work items.
- Mitigation 2: encode gate language in templates, governance docs, and control catalog with explicit IDs.

## Rollback Notes
- Revert modified template/governance/control-catalog files and rerun:
  - `make quality-sdd-check-all`
  - `make quality-docs-check-blueprint-template-sync`
  - `make infra-validate`
