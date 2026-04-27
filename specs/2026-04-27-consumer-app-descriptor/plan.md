# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate:
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate:
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate:
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices
1. Slice 1: Add descriptor contract and seed surface.
   - Red: add tests proving `apps.yaml` is absent from `consumer_seeded` and init template coverage.
   - Green: update `blueprint/contract.yaml`, bootstrap mirror, and `scripts/templates/consumer/init/apps.yaml.tmpl`.
2. Slice 2: Add descriptor schema, loader, and validation.
   - Red: add pytest cases for invalid names, missing derived manifests, and kustomization drift.
   - Green: implement safe YAML loader and app runtime validation integration.
3. Slice 3: Feed descriptor into app catalog rendering and smoke checks.
   - Red: add renderer tests with non-baseline app names.
   - Green: update app catalog renderer/bootstrap/smoke paths to use descriptor records.
4. Slice 4: Integrate descriptor ownership into upgrade diagnostics.
   - Red: add upgrade plan/postcheck tests expecting `consumer-app-descriptor` evidence.
   - Green: emit descriptor ownership for derived app manifests and retain kustomization-ref fallback.
5. Slice 5: Document and publish.
   - Red: docs validation captures missing descriptor guidance.
   - Green: update blueprint and consumer docs, generated metadata, traceability, hardening review, and PR context.

## Change Strategy
- Migration/rollout sequence: ship descriptor as consumer-seeded in new consumers first; existing consumers receive a warning-only fallback for one upgrade cycle when `apps.yaml` is absent; docs describe adding the descriptor during upgrade follow-up.
- Backward compatibility policy: existing kustomization-derived smoke and prune guards remain active until the descriptor is present and valid.
- Rollback plan: revert descriptor contract, template, loader, renderer, and docs changes; current #206/#207/#203 guards continue to protect existing consumers.

## Validation Strategy (Shift-Left)
- Unit checks: pytest for descriptor loader, name/path validation, renderer output, and upgrade diagnostic classification.
- Contract checks: `make infra-validate`, `make quality-sdd-check`, and targeted contract validation tests for `blueprint/contract.yaml`.
- Integration checks: `make apps-bootstrap`, `make apps-smoke`, and `make blueprint-template-smoke` with baseline descriptor.
- E2E checks: no new e2e lane; existing generated-consumer smoke scenarios cover the affected bootstrap/smoke boundary.

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
- App onboarding impact: no-impact | impacted (select one)
- App onboarding impact: impacted
- Notes: app delivery metadata and GitOps manifest validation are affected; all minimum targets remain in scope and must stay available.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/execution_model.md`, generated contract metadata, and ADR.
- Consumer docs updates: `docs/platform/consumer/app_onboarding.md`, `docs/platform/consumer/quickstart.md`, and `docs/platform/consumer/troubleshooting.md`.
- Mermaid diagrams updated: ADR flowchart and architecture flowchart.
- Docs validation commands:
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
- Logging/metrics/traces: no runtime metric change; validation diagnostics name descriptor apps and derived paths.
- Alerts/ownership: no alert change; consumer team ownership lives in `apps.yaml`.
- Runbook updates: app onboarding and troubleshooting docs describe descriptor edits, validation failures, and upgrade fallback behavior.

## Risks and Mitigations
- Risk 1 -> mitigation: custom manifest names outside the initial convention are not represented; document exclusion and keep kustomization-ref fallback.
- Risk 2 -> mitigation: generated catalog output can drift from descriptor; add renderer and smoke tests that fail on drift.
- Risk 3 -> mitigation: existing consumers lack `apps.yaml`; one-cycle fallback prevents hard failure and docs provide manual adoption steps.
