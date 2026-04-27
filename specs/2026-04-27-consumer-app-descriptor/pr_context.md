# PR Context

## Summary
- Work item: 2026-04-27-consumer-app-descriptor
- Objective: Introduce a consumer-owned `apps.yaml` descriptor that records logical app metadata once and lets blueprint tooling derive GitOps manifest paths, app catalog output, and upgrade diagnostics.
- Scope boundaries: Intake only in this change set. Implementation scope covers contract/schema/bootstrap/validation/rendering/docs after sign-off.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-007; NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001.
- Acceptance criteria covered: AC-001 through AC-007 planned.
- Contract surfaces changed: planned `apps.yaml`, `blueprint/contract.yaml`, consumer init templates, app runtime GitOps validation, app catalog scaffold, upgrade diagnostics, and docs.

## Key Reviewer Files
- Primary files to review first: `spec.md`, `architecture.md`, `plan.md`, `docs/blueprint/architecture/decisions/ADR-2026-04-27-consumer-app-descriptor.md`.
- High-risk files: planned `blueprint/contract.yaml`, `scripts/lib/blueprint/contract_validators/app_runtime_gitops.py`, `scripts/lib/platform/apps/catalog_scaffold_renderer.py`, `scripts/lib/blueprint/upgrade_consumer.py`.

## Validation Evidence
- Required commands executed: pending `make quality-sdd-check` after intake population.
- Result summary: implementation not started; sign-offs pending.
- Artifact references: `traceability.md`, `evidence_manifest.json`, `hardening_review.md`.

## Risk and Rollback
- Main risks: descriptor convention excludes custom manifest filenames in first version; generated catalog output must not drift from descriptor; existing consumers lack the new file initially.
- Rollback strategy: revert descriptor contract/template/loader/renderer/docs changes; current #206/#207/#203 safeguards remain.

## Deferred Proposals
- Custom manifest filename overrides remain deferred until convention-based descriptor adoption is validated.
