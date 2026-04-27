# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-consumer-app-descriptor.md
- ADR status: proposed

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
- Business outcome: Generated consumers get one consumer-owned app descriptor that records logical app names and app metadata once, then blueprint tooling derives convention-based GitOps workload paths and validates those paths against `kustomization.yaml`, smoke contracts, and app catalog output.
- Success metric: A generated consumer can rename the baseline apps through `apps.yaml`, run bootstrap/upgrade validation, and receive deterministic diagnostics when the derived deployment/service manifests or kustomization resources drift.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST add `apps.yaml` as a consumer-seeded file under `repository.ownership_path_classes.consumer_seeded` in `blueprint/contract.yaml` and its blueprint bootstrap mirror.
- FR-002 MUST add a generated-consumer init template at `scripts/templates/consumer/init/apps.yaml.tmpl` with the baseline `backend-api` and `touchpoints-web` app entries.
- FR-003 MUST define a schema-validated descriptor contract with `schemaVersion`, `apps`, `name`, `team`, `servicePort`, `healthCheckPath`, and `workloadKind` fields. `name` MUST derive `infra/gitops/platform/base/apps/{name}-deployment.yaml` and `infra/gitops/platform/base/apps/{name}-service.yaml`.
- FR-004 MUST add blueprint validation that loads `apps.yaml`, validates the schema, verifies every derived manifest path exists, and verifies every derived manifest filename is listed in `infra/gitops/platform/base/apps/kustomization.yaml`.
- FR-005 MUST update app catalog bootstrap/rendering so `apps/catalog/manifest.yaml` derives `deliveryTopology.workloads` and `runtimeDeliveryContract.gitopsWorkloads` from `apps.yaml` when app catalog scaffold is enabled.
- FR-006 MUST update upgrade planning and postcheck diagnostics to report descriptor-driven app ownership as `consumer-app-descriptor` and retain the existing kustomization-ref prune guard as fallback behavior.
- FR-007 MUST remove or retire the path-prefix bridge dependency on `_is_consumer_owned_workload()` once descriptor-driven validation covers `base/apps/` manifests; the fallback kustomization-ref guard MUST remain active for non-app overlay files.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST parse `apps.yaml` with safe YAML loading and MUST reject app names that escape the `infra/gitops/platform/base/apps/` path by absolute paths, parent traversal, shell metacharacters, or path separators.
- NFR-OBS-001 MUST emit deterministic validation messages that name the descriptor app, derived manifest path, and missing or mismatched kustomization resource.
- NFR-REL-001 MUST remain backward-compatible for existing consumers without `apps.yaml` during one blueprint upgrade cycle by warning and falling back to current kustomization-derived behavior.
- NFR-OPS-001 MUST document descriptor ownership, bootstrap behavior, upgrade diagnostics, and manual rename workflow in generated-consumer docs.

## Normative Option Decision
- Option A: Add root-level `apps.yaml` as the consumer-owned descriptor and use it as the authoritative app metadata input for GitOps validation and app catalog rendering.
- Option B: Extend `apps/catalog/manifest.yaml` and make it the editable app descriptor.
- Selected option: OPTION_A
- Rationale: Option A separates consumer-owned app declarations from generated catalog output. It keeps `apps/catalog/manifest.yaml` renderable, avoids hand-edit conflicts in generated catalog fields, and gives upgrade tooling one stable consumer-owned input.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` adds `apps.yaml` to `repository.ownership_path_classes.consumer_seeded`; descriptor schema fields become the app declaration contract.
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
- AC-001 MUST show `apps.yaml` listed in `consumer_seeded` in `blueprint/contract.yaml` and `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`, with `scripts/templates/consumer/init/apps.yaml.tmpl` present.
- AC-002 MUST fail validation with a deterministic error when `apps.yaml` contains `name: ../bad` or `name: nested/app`.
- AC-003 MUST fail validation with a deterministic error when an app named `marketplace-api` lacks `infra/gitops/platform/base/apps/marketplace-api-deployment.yaml`.
- AC-004 MUST fail validation with a deterministic error when a derived manifest exists but its filename is absent from `infra/gitops/platform/base/apps/kustomization.yaml`.
- AC-005 MUST render `apps/catalog/manifest.yaml` entries for app descriptor records without hardcoded `backend-api` or `touchpoints-web` dependency in renderer logic.
- AC-006 MUST produce upgrade plan or postcheck evidence that descriptor-owned app manifests are reported as `consumer-app-descriptor`.
- AC-007 MUST keep existing generated-consumer smoke scenarios passing for the baseline app descriptor template.

## Informative Notes (Non-Normative)
- Context: This work item promotes the parked proposal under `v1.7.0 upgrade findings (pipeline correctness gaps)`. Issues #206, #207, #208, and #203/#204 already shipped immediate guards for hardcoded workload names and prune safety. The remaining value is a durable consumer-owned app metadata source.
- Tradeoffs: A new descriptor adds one consumer-owned file and one schema surface. The gain is clearer ownership, richer diagnostics, and reduced coupling between generated catalog output and consumer app declarations.
- Clarifications: none

## Explicit Exclusions
- New HTTP APIs, OpenAPI contracts, and Pact contracts are excluded.
- Arbitrary custom manifest filenames that do not follow `{name}-deployment.yaml` and `{name}-service.yaml` are excluded from this first descriptor version.
- Incremental upgrade mode (#168), dry-run mode (#167), and source-only seed advisory follow-up are excluded.
