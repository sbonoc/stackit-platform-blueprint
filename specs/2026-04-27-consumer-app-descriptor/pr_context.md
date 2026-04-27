# PR Context

## Summary
- Work item: 2026-04-27-consumer-app-descriptor
- Objective: Introduce a consumer-owned `apps/descriptor.yaml` descriptor that records app/component metadata once and lets blueprint tooling validate GitOps manifest refs, render deprecated catalog compatibility output, and produce upgrade diagnostics/advisory artifacts.
- Scope boundaries: Intake only in this change set. Implementation scope covers contract/schema/bootstrap/validation/rendering/advisory/deprecation/docs after sign-off.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-011; NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001.
- Acceptance criteria covered: AC-001 through AC-009 planned.
- Contract surfaces changed: planned `apps/descriptor.yaml`, `blueprint/contract.yaml`, consumer init templates, app runtime GitOps validation, deprecated app catalog compatibility scaffold, upgrade diagnostics, suggested descriptor artifact, deprecation tracking, and docs.

## Key Reviewer Files
- Primary files to review first: `spec.md`, `architecture.md`, `plan.md`, `docs/blueprint/architecture/decisions/ADR-2026-04-27-consumer-app-descriptor.md`.
- High-risk files: planned `blueprint/contract.yaml`, `scripts/lib/blueprint/contract_validators/app_runtime_gitops.py`, `scripts/lib/platform/apps/catalog_scaffold_renderer.py`, `scripts/lib/blueprint/upgrade_consumer.py`.

## Validation Evidence
- Required commands executed: `make quality-sdd-check`.
- Result summary: `make quality-sdd-check` passed for intake artifacts; implementation not started; sign-offs pending.
- Artifact references: `traceability.md`, `evidence_manifest.json`, `hardening_review.md`.

## Risk and Rollback
- Main risks: descriptor schema can overreach into Kubernetes modeling; deprecated catalog output must not drift from descriptor; existing consumers lack the new file initially; deprecations need explicit removal tracking.
- Rollback strategy: revert descriptor contract/template/loader/renderer/docs changes; current #206/#207/#203 safeguards remain.

## Deferred Proposals
- Removal of deprecated `apps/catalog/manifest.yaml` compatibility output is deferred until after the two-minor-release migration window.
- Removal of deprecated `_is_consumer_owned_workload()` bridge guard is deferred until after the two-minor-release migration window or descriptor coverage becomes mandatory, whichever is later.
