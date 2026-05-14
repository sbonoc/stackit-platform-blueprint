# Work Item Context Pack

## Context Snapshot
- Work item: 2026-05-14-issue-277-argocd-health-na
- Track: blueprint
- SPEC_READY: false
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-277-argocd-health-na.md
- ADR status: proposed

## Summary
Bug fix: override the argo-cd Helm chart 9.4.16 default `resource.customizations.ignoreResourceUpdates.all: | jsonPointers: - /status` to an empty string in `infra/local/helm/core/argocd.values.yaml` and its bootstrap template. This restores ArgoCD health evaluation for all local-lane managed resources, which permanently report `health=N/A` due to a behavior change in ArgoCD v3.x.

## Root Cause
The argo-cd Helm chart 9.4.16 (ArgoCD v3.3.5) ships a default `configs.cm` entry that suppresses `.status` watch events for all resource types. In ArgoCD v3.x the health evaluator depends on these events; when suppressed, resources remain at `health=N/A` indefinitely.

## Key Files
- `infra/local/helm/core/argocd.values.yaml` — receives `configs.cm` override (FR-001)
- `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml` — template receives same override (FR-002)
- `tests/infra/test_argocd_values_health_fix.py` — regression tests (AC-001, AC-002)
- `docs/blueprint/architecture/decisions/ADR-issue-277-argocd-health-na.md` — ADR

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
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
