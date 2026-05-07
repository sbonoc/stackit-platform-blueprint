# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-consumer-app-descriptor.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale: SDD-C-022 and SDD-C-023 do not apply because this work item changes app metadata, GitOps validation, and upgrade planning paths, not HTTP route handlers, query logic, filter logic, payload-transform logic, OpenAPI endpoints, or Pact interfaces.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_bash_scripts (blueprint contract/schema, init, upgrade, validation, and app catalog tooling)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: This is blueprint metadata and local tooling work. It provisions no STACKIT managed service and consumes no cloud runtime capability.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none; validation remains local-first through blueprint template, infra, app, and docs checks.

## Objective
- Business outcome: Generated consumers get one consumer-owned app descriptor that records app topology, component ownership, service ports, health checks, and manifest references once, then blueprint tooling validates GitOps wiring and renders transitional compatibility outputs from that descriptor.
- Success metric: A generated consumer can rename the baseline apps or declare explicit manifest paths in `apps/descriptor.yaml`, run bootstrap/upgrade validation, and receive deterministic diagnostics when component manifests, services, or kustomization resources drift.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST add `apps/descriptor.yaml` as a consumer-seeded file under `repository.ownership_path_classes.consumer_seeded` in `blueprint/contract.yaml` and its blueprint bootstrap mirror.
- FR-002 MUST add a generated-consumer init template at `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` with the baseline `backend-api` and `touchpoints-web` app entries.
- FR-003 MUST define a schema-validated descriptor contract with `schemaVersion`, `apps`, `id`, `owner.team`, `components`, `components.id`, `components.kind`, `components.manifests`, `components.service`, and `components.health` fields.
- FR-004 MUST allow every component to declare explicit manifest paths and MUST provide convention defaults for absent deployment or service manifest paths using `infra/gitops/platform/base/apps/{component-id}-deployment.yaml` and `infra/gitops/platform/base/apps/{component-id}-service.yaml`.
- FR-005 MUST support multiple components per app, including API, worker, and web components, with component-level workload kind, service, port, and health metadata.
- FR-006 MUST add blueprint validation that loads `apps/descriptor.yaml`, validates the schema, verifies every component manifest path exists, verifies every app manifest path stays under `infra/gitops/platform/base/apps/`, and verifies every manifest filename is listed in `infra/gitops/platform/base/apps/kustomization.yaml`.
- FR-007 MUST update app catalog bootstrap/rendering so `apps/catalog/manifest.yaml` derives `deliveryTopology.workloads` and `runtimeDeliveryContract.gitopsWorkloads` from `apps/descriptor.yaml` when app catalog scaffold is enabled.
- FR-008 MUST mark `apps/catalog/manifest.yaml` as a generated deprecated compatibility artifact for two blueprint minor releases; descriptor data is canonical during that window.
- FR-009 MUST update upgrade planning and postcheck diagnostics to report descriptor-driven app ownership as `consumer-app-descriptor` and retain the existing kustomization-ref prune guard as fallback behavior.
- FR-010 MUST keep `_is_consumer_owned_workload()` as a deprecated bridge for two blueprint minor releases, with an explicit backlog removal trigger after descriptor adoption.
- FR-011 MUST generate `artifacts/blueprint/app_descriptor.suggested.yaml` for existing generated consumers that lack `apps/descriptor.yaml`; the artifact MUST be human-readable and agent-editable, and normal upgrade apply MUST NOT write it into the consumer working tree automatically.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST parse `apps/descriptor.yaml` with safe YAML loading and MUST reject app IDs, component IDs, and manifest paths that escape `infra/gitops/platform/base/apps/` by absolute paths, parent traversal, shell metacharacters, or unsafe path separators.
- NFR-OBS-001 MUST emit deterministic validation messages that name the descriptor app, component ID, manifest path, and missing or mismatched kustomization resource.
- NFR-REL-001 MUST hard-fail descriptor validation in template-source and new generated-consumer initialization paths while warning for existing generated consumers that lack `apps/descriptor.yaml` during the two-minor-release migration window.
- NFR-OPS-001 MUST document descriptor ownership, bootstrap behavior, upgrade advisory artifacts, app catalog deprecation, bridge-guard deprecation, and manual rename workflow in generated-consumer docs.

## Normative Option Decision
- Option A: Add `apps/descriptor.yaml` as the consumer-owned descriptor and use it as the authoritative app metadata input for GitOps validation and transitional app catalog rendering.
- Option B: Extend `apps/catalog/manifest.yaml` and make it the editable app descriptor.
- Option C: Remove `apps/catalog/manifest.yaml` in this work item and migrate all tooling immediately.
- Selected option: OPTION_A
- Rationale: Option A separates consumer-owned app declarations from generated catalog output. It keeps `apps/catalog/manifest.yaml` as a deprecated generated compatibility artifact for two blueprint minor releases, avoids hand-edit conflicts in generated catalog fields, and gives upgrade tooling one stable consumer-owned input.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` adds `apps/descriptor.yaml` to `repository.ownership_path_classes.consumer_seeded`; descriptor schema fields become the app declaration contract.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: existing targets remain; validation behavior changes under `blueprint-init-repo`, `apps-bootstrap`, `apps-smoke`, `infra-validate`, `blueprint-upgrade-consumer`, and `blueprint-upgrade-consumer-postcheck`.
- Docs contract: update `docs/platform/consumer/app_onboarding.md`, `docs/platform/consumer/quickstart.md`, `docs/platform/consumer/troubleshooting.md`, `docs/blueprint/architecture/execution_model.md`, and generated contract metadata.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST show `apps/descriptor.yaml` listed in `consumer_seeded` in `blueprint/contract.yaml` and `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`, with `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` present.
- AC-002 MUST fail validation with a deterministic error when `apps/descriptor.yaml` contains `id: ../bad`, `id: nested/app`, or a component manifest path outside `infra/gitops/platform/base/apps/`.
- AC-003 MUST fail validation with a deterministic error when a component named `marketplace-api` lacks its resolved deployment manifest.
- AC-004 MUST fail validation with a deterministic error when a resolved manifest exists but its filename is absent from `infra/gitops/platform/base/apps/kustomization.yaml`.
- AC-005 MUST render `apps/catalog/manifest.yaml` entries from descriptor app and component records without hardcoded `backend-api` or `touchpoints-web` dependency in renderer logic.
- AC-006 MUST produce upgrade plan or postcheck evidence that descriptor-owned app manifests are reported as `consumer-app-descriptor`.
- AC-007 MUST keep existing generated-consumer smoke scenarios passing for the baseline app descriptor template.
- AC-008 MUST write `artifacts/blueprint/app_descriptor.suggested.yaml` for an existing generated consumer without `apps/descriptor.yaml` and MUST include comments or fields that guide human and agent review before adoption.
- AC-009 MUST record deprecation diagnostics for `apps/catalog/manifest.yaml` as a generated compatibility artifact and for `_is_consumer_owned_workload()` as a bridge guard with two-minor-release removal tracking.

## Informative Notes (Non-Normative)
- Context: This work item promotes the parked proposal under `v1.7.0 upgrade findings (pipeline correctness gaps)`. Issues #206, #207, #208, and #203/#204 already shipped immediate guards for hardcoded workload names and prune safety. The remaining value is a durable consumer-owned app metadata source.
- Tradeoffs: A new descriptor adds one consumer-owned file and one schema surface. The gain is clearer ownership, richer diagnostics, and reduced coupling between generated catalog output and consumer app declarations.
- Clarifications: User decisions recorded in conversation: descriptor path is `apps/descriptor.yaml`; explicit manifest paths are required; multiple components per app are required; existing-consumer migration uses an advisory artifact; `_is_consumer_owned_workload()` deprecates over two blueprint minor releases; missing descriptor is hard-fail for template-source/new generated consumers and warning-only for existing generated consumers during migration; `apps/catalog/manifest.yaml` remains a deprecated generated compatibility artifact for two blueprint minor releases and then is removed.

## Explicit Exclusions
- New HTTP APIs, OpenAPI contracts, and Pact contracts are excluded.
- Immediate removal of `apps/catalog/manifest.yaml` is excluded.
- Immediate removal of `_is_consumer_owned_workload()` is excluded.
- Incremental upgrade mode (#168), dry-run mode (#167), and source-only seed advisory follow-up are excluded.
