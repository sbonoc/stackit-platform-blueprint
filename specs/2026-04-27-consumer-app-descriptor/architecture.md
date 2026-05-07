# Architecture

## Context
- Work item: 2026-04-27-consumer-app-descriptor
- Owner: Sergi Bono
- Date: 2026-04-27

## Stack and Execution Model
- Backend stack profile: python_plus_bash_scripts (blueprint contract/schema, init, upgrade, validation, and app catalog tooling)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: The current app runtime path stack protects consumer-renamed manifests through a mix of `consumer_seeded` path ownership, a `base/apps/` bridge guard, and kustomization-reference scanning. That prevents destructive upgrades, but it does not give blueprint tooling an authoritative consumer-owned app metadata source for team ownership, component topology, explicit manifest paths, service ports, health checks, catalog rendering, or preflight diagnostics.
- Scope boundaries: Add `apps/descriptor.yaml` as a consumer-seeded descriptor; validate descriptor schema, explicit manifest paths, convention defaults, and kustomization membership; feed descriptor values into app catalog compatibility rendering and app runtime validation; update upgrade diagnostics, advisory artifact generation, deprecation tracking, and docs.
- Out of scope: new HTTP APIs, OpenAPI/Pact contracts, immediate app catalog removal, immediate bridge guard removal, #167 dry-run mode, #168 incremental upgrade mode, and source-only seed advisory.

## Bounded Contexts and Responsibilities
- Context A - Consumer app declaration: `apps/descriptor.yaml` is owned by the generated consumer after init. It records apps, components, owners, service metadata, health checks, and manifest refs.
- Context B - Blueprint contract validation: `infra-validate` and app runtime validators read `apps/descriptor.yaml`, enforce schema rules, and verify manifest/kustomization consistency.
- Context C - App catalog compatibility rendering: `apps-bootstrap` uses descriptor records as the input for deprecated generated `apps/catalog/manifest.yaml` workload and runtime delivery sections during the two-minor-release compatibility window.
- Context D - Upgrade planning and postcheck: upgrade tooling reports descriptor-owned app manifests as consumer app descriptor paths, generates `artifacts/blueprint/app_descriptor.suggested.yaml` for existing consumers without the descriptor, and keeps existing prune guards as fallback protection.
- Context E - Decommission tracking: backlog and diagnostics keep `apps/catalog/manifest.yaml` and `_is_consumer_owned_workload()` removal visible until the removal triggers are reached.

## High-Level Component Design
- Domain layer: versioned app descriptor model with app ID, owner team, multiple components, workload kind, service ports, health checks, explicit manifest refs, and convention default resolution.
- Application layer: descriptor loader and validator used by contract validation, app catalog renderer, template smoke assertions, and upgrade diagnostics.
- Infrastructure adapters: safe YAML loader, filesystem checks for `infra/gitops/platform/base/apps`, kustomization resource parser, advisory artifact writer, and existing template rendering.
- Presentation/API/workflow boundaries: `apps/descriptor.yaml`, validation stderr, deprecated `apps/catalog/manifest.yaml`, `artifacts/blueprint/app_descriptor.suggested.yaml`, upgrade plan/apply/postcheck artifacts, and consumer documentation.

```mermaid
flowchart TD
    A[apps/descriptor.yaml consumer descriptor] --> B[Descriptor loader and schema validator]
    B --> C[Component manifest refs and convention defaults]
    C --> D[infra-validate app runtime checks]
    C --> E[apps-bootstrap compatibility catalog renderer]
    C --> F[blueprint-upgrade diagnostics]
    C --> J[existing-consumer suggested descriptor artifact]
    D --> G[deterministic validation output]
    E --> H[deprecated apps/catalog/manifest.yaml]
    F --> I[consumer-app-descriptor ownership evidence]
```

Caption: The descriptor becomes the single consumer-owned input for app metadata; generated compatibility and validation surfaces derive from it.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` ownership classes, `scripts/templates/consumer/init`, app runtime GitOps contract, app catalog scaffold contract, existing upgrade prune guard stack, and existing app catalog version audit behavior.
- Downstream dependencies: `make blueprint-init-repo`, `make infra-validate`, `make apps-bootstrap`, `make apps-smoke`, `make blueprint-upgrade-consumer`, `make blueprint-upgrade-consumer-postcheck`, generated-consumer docs.
- Data/API/event contracts touched: config contract only. No HTTP API, OpenAPI, Pact, or event contract changes.

## Non-Functional Architecture Notes
- Security: app IDs, component IDs, and manifest refs are restricted to safe identifiers or repo-relative paths under `infra/gitops/platform/base/apps`.
- Observability: validation and upgrade diagnostics include app ID, component ID, manifest path, and mismatched kustomization resource.
- Reliability and rollback: two-minor-release fallback keeps existing kustomization-derived behavior for consumers that lack `apps/descriptor.yaml`; rollback is reverting the descriptor PR and leaving current guards intact.
- Monitoring/alerting: no runtime alert changes. Operational signal is local validation output and upgrade artifacts.

## Risks and Tradeoffs
- Risk 1: Descriptor schema becomes too broad if it models every Kubernetes possibility; mitigation is component-level metadata plus explicit manifest refs, not full workload spec modeling.
- Risk 2: Existing catalog rendering has hardcoded baseline assumptions; mitigation is tests proving descriptor values replace hardcoded workload IDs in rendered output.
- Risk 3: Existing consumers lack the descriptor; mitigation is warning-only migration plus `artifacts/blueprint/app_descriptor.suggested.yaml`.
- Tradeoff 1: A separate `apps/descriptor.yaml` adds a file, but avoids making generated `apps/catalog/manifest.yaml` both source input and output.
- Tradeoff 2: `apps/catalog/manifest.yaml` remains for two minor releases as compatibility output, adding temporary duplication; removal is tracked to avoid permanent leftovers.
