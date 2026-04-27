# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: keep implementation minimal and explicit; avoid speculative abstractions.
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate: prefer direct framework primitives over wrapper layers; keep model representations singular.
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate: contract/boundary tests precede implementation; realistic environment coverage for integration points.
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate: not applicable — this work item changes app metadata, validation, and rendering paths; no filter or payload-transform logic is introduced.
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate: each reproducible finding becomes a failing test first, then the fix turns it green.
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Dependency-Ordered Execution Slices

| Slice | Owner | Depends on | Inputs | Outputs | Requirements | Tasks |
|---|---|---|---|---|---|---|
| S1 Descriptor contract and seed surface | Software Engineer - contract/bootstrap | approved spec and ADR | `spec.md` FR-001/FR-002, ownership contract, init template conventions | `apps/descriptor.yaml` in consumer-seeded contract paths, bootstrap mirror parity, generated-consumer init template | FR-001, FR-002, AC-001 | T-001, T-002, T-101, T-102 |
| S2 Descriptor schema, loader, and validation core | Software Engineer - validation/domain | S1 | descriptor YAML shape, explicit manifest refs, convention defaults, path safety rules | descriptor model/loader, safe path resolver, app runtime GitOps validation integration | FR-003, FR-004, FR-005, FR-006, NFR-SEC-001, NFR-OBS-001, AC-002, AC-003, AC-004 | T-003, T-004, T-101, T-102, T-104 |
| S3 App catalog compatibility rendering and smoke | Software Engineer - app runtime/catalog | S2 | normalized descriptor records and existing catalog renderer contract | descriptor-driven `apps/catalog/manifest.yaml` compatibility output, bootstrap/smoke assertions without hardcoded baseline app IDs | FR-005, FR-007, FR-008, AC-005, AC-007 | T-005, T-105, A-001 |
| S4 Upgrade diagnostics and advisory artifact | Software Engineer - upgrade pipeline | S2 | normalized descriptor records, existing upgrade plan/postcheck flow, migration fallback policy | `consumer-app-descriptor` ownership evidence, suggested descriptor artifact, warning-only existing-consumer fallback | FR-009, FR-011, NFR-REL-001, AC-006, AC-008 | T-006, T-007, T-106, T-107 |
| S5 Deprecation tracking and bridge cleanup preparation | Software Engineer - governance/upgrade | S3, S4 | decommission decisions, backlog triggers, compatibility window | deprecation diagnostics/docs checks for app catalog compatibility output and `_is_consumer_owned_workload()` bridge | FR-008, FR-010, AC-009 | T-008, T-009, T-108 |
| S6 Documentation, evidence, and publish preparation | Software Engineer - docs/release | S1, S2, S3, S4, S5 | implemented behavior, validation output, traceability matrix, ADR | blueprint docs, consumer docs, generated metadata, traceability evidence, hardening review, PR context | NFR-OPS-001, AC-007, AC-009 | T-010, T-011, T-201 through T-210, P-001 through P-003 |

## Slice Validation Strategy

| Slice | Lowest valid red check | Green validation | Exit evidence |
|---|---|---|---|
| S1 | Contract/template parity tests fail because `apps/descriptor.yaml` is not consumer-seeded and init template is absent. | Targeted contract validation plus `make quality-sdd-check`. | Contract diff, template path, and passing contract parity tests. |
| S2 | Descriptor unit tests fail for unsafe IDs, unsafe manifest paths, missing resolved manifests, and missing kustomization resources. | Descriptor unit suite and app runtime validator tests pass. | Test output naming rejected app/component/path cases and deterministic diagnostics. |
| S3 | Renderer tests fail for non-baseline app IDs, multiple components, and explicit manifest refs. | Renderer tests plus `make apps-bootstrap` and `make apps-smoke`. | Rendered deprecated catalog output and app smoke evidence derived from descriptor records. |
| S4 | Upgrade plan/postcheck tests fail for absent `consumer-app-descriptor` evidence and absent suggested descriptor artifact. | Upgrade diagnostics tests pass with descriptor present and descriptor absent. | Upgrade plan/postcheck artifacts plus `artifacts/blueprint/app_descriptor.suggested.yaml` evidence. |
| S5 | Deprecation docs/checks fail when removal triggers or bridge/catalog warnings are absent. | Deprecation tracking checks and targeted docs checks pass. | Backlog removal triggers, diagnostic text, and docs references. |
| S6 | Docs validation or publish artifact review fails for missing descriptor guidance or stale traceability evidence. | `make quality-hooks-run`, `make infra-validate`, docs validation, and applicable app/bootstrap smoke gates pass. | Updated `traceability.md`, `pr_context.md`, `hardening_review.md`, docs validation output, and PR-ready summary. |

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
