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
   - Red: add tests proving `apps/descriptor.yaml` is absent from `consumer_seeded` and init template coverage.
   - Green: update `blueprint/contract.yaml`, bootstrap mirror, and `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl`.
2. Slice 2: Add descriptor schema, loader, and validation.
   - Red: add pytest cases for invalid app IDs, invalid component IDs, unsafe explicit manifest refs, missing resolved manifests, and kustomization drift.
   - Green: implement safe YAML loader and app runtime validation integration.
3. Slice 3: Feed descriptor into app catalog rendering and smoke checks.
   - Red: add renderer tests with non-baseline app IDs, multiple components, and explicit manifest refs.
   - Green: update app catalog renderer/bootstrap/smoke paths to use descriptor records while marking `apps/catalog/manifest.yaml` as generated compatibility output.
4. Slice 4: Integrate descriptor ownership into upgrade diagnostics.
   - Red: add upgrade plan/postcheck tests expecting `consumer-app-descriptor` evidence and suggested descriptor artifact generation for missing descriptors.
   - Green: emit descriptor ownership for resolved app manifests, write `artifacts/blueprint/app_descriptor.suggested.yaml`, and retain kustomization-ref fallback.
5. Slice 5: Add deprecation and removal tracking.
   - Red: add tests/docs checks that fail if deprecation diagnostics or backlog triggers are absent.
   - Green: mark `apps/catalog/manifest.yaml` compatibility output and `_is_consumer_owned_workload()` bridge with two-minor-release removal triggers.
6. Slice 6: Document and publish.
   - Red: docs validation captures missing descriptor guidance.
   - Green: update blueprint and consumer docs, generated metadata, traceability, hardening review, and PR context.

## Change Strategy
- Migration/rollout sequence: ship descriptor as consumer-seeded in new consumers first; existing consumers receive a warning-only fallback for two blueprint minor releases when `apps/descriptor.yaml` is absent; upgrade writes `artifacts/blueprint/app_descriptor.suggested.yaml` for human and agent review; docs describe adding the descriptor during upgrade follow-up.
- Backward compatibility policy: existing kustomization-derived smoke and prune guards remain active until the descriptor is present and valid. `apps/catalog/manifest.yaml` remains generated compatibility output for two blueprint minor releases, then is removed through tracked decommission work.
- Rollback plan: revert descriptor contract, template, loader, renderer, and docs changes; current #206/#207/#203 guards continue to protect existing consumers.

## Validation Strategy (Shift-Left)
- Unit checks: pytest for descriptor loader, app/component ID validation, explicit manifest path validation, renderer output, advisory artifact rendering, and upgrade diagnostic classification.
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
- Alerts/ownership: no alert change; consumer team ownership lives in `apps/descriptor.yaml`.
- Runbook updates: app onboarding and troubleshooting docs describe descriptor edits, validation failures, suggested descriptor adoption, app catalog deprecation, bridge-guard deprecation, and upgrade fallback behavior.

## Risks and Mitigations
- Risk 1 -> mitigation: descriptor schema overreach can duplicate Kubernetes; model component metadata and explicit manifest refs only.
- Risk 2 -> mitigation: generated catalog output can drift from descriptor; add renderer and smoke tests that fail on drift.
- Risk 3 -> mitigation: existing consumers lack `apps/descriptor.yaml`; two-minor-release fallback prevents hard failure and docs provide manual adoption steps.
- Risk 4 -> mitigation: deprecations can become permanent leftovers; backlog entries include removal triggers for compatibility catalog output and bridge guard.
