# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-27-issue-217-template-descriptor-kustomization-sync
- Track: blueprint
- SPEC_READY: true
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-217-template-descriptor-kustomization-sync.md
- ADR status: approved
- Source issue: #217 — blueprint-template-smoke fails because v1.8.0 seed templates have descriptor-kustomization mismatch
- Related shipped context: #213 (consumer-app-descriptor — introduced validate_app_descriptor and kustomization membership check in infra-validate); fix-issue-206 (reclassified seed manifests from source_only to consumer_seeded, added consumer init manifest templates)

## Guardrail Controls
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make blueprint-template-smoke`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
