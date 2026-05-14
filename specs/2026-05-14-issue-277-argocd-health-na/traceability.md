# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | N/A | architecture.md §Integration and Dependency Edges | `infra/local/helm/core/argocd.values.yaml` `configs.cm.resource.customizations.ignoreResourceUpdates.all` | `tests/infra/test_argocd_values_health_fix.py::test_argocd_values_ignoreResourceUpdates_all_is_empty` | argocd.values.yaml inline comment | `argocd app get platform-local-core` post-deploy |
| FR-002 | SDD-C-005, SDD-C-024 | N/A | architecture.md §Integration and Dependency Edges | `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml` | `tests/infra/test_argocd_values_health_fix.py::test_argocd_template_ignoreResourceUpdates_all_is_empty` | bootstrap template inline comment | new consumer `make blueprint-init-repo` receives fix |
| FR-003 | SDD-C-005, SDD-C-024 | N/A | ADR §Decision | `scripts/lib/infra/versions.sh` and `scripts/lib/infra/versions.baseline.sh` `ARGOCD_CHART_VERSION=9.5.13` | `tests/infra/test_argocd_values_health_fix.py::test_argocd_chart_version_is_9_5_13` | versions.sh inline comment | `make infra-audit-version` reports 9.5.13 |
| NFR-SEC-001 | SDD-C-009 | N/A | N/A — no security surface | N/A | N/A | spec.md §NFR-SEC-001 | N/A |
| NFR-OBS-001 | SDD-C-010 | N/A | architecture.md §Non-Functional Architecture Notes | ArgoCD health evaluation restored via FR-001 fix | AC-005 manual smoke (post-deploy health check) | spec.md §NFR-OBS-001 | `argocd app get platform-local-core` Health: Healthy |
| NFR-REL-001 | SDD-C-012 | N/A | plan.md §Change Strategy | Rollback: remove `configs.cm` block + revert version pin + `make infra-deploy` | N/A | plan.md §Rollback plan | N/A |
| NFR-OPS-001 | SDD-C-010 | N/A | plan.md §Validation Strategy | N/A (operator self-service) | AC-005 manual smoke | spec.md §NFR-OPS-001 | `argocd app get platform-local-core` |
| AC-001 | SDD-C-012 | N/A | N/A | `tests/infra/test_argocd_values_health_fix.py` | pytest pass | N/A | N/A |
| AC-002 | SDD-C-012 | N/A | N/A | `tests/infra/test_argocd_values_health_fix.py` | pytest pass | N/A | N/A |
| AC-003 | SDD-C-012 | N/A | N/A | `tests/infra/test_argocd_values_health_fix.py` | pytest pass | N/A | N/A |
| AC-004 | SDD-C-008 | N/A | N/A | `tests/infra/test_argocd_values_health_fix.py` | pytest pass (no live cluster) | N/A | N/A |
| AC-005 | SDD-C-010 | N/A | N/A | `make infra-deploy` on Docker Desktop | manual smoke evidence in pr_context.md | N/A | `argocd app get platform-local-core` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005

## Validation Summary
- Required bundles executed: (to be completed at Verify phase)
- Result summary: (to be completed at Verify phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consider per-resource-type ignoreResourceUpdates for genuinely noisy resource types (e.g., ConfigMap, Endpoints) if reconciliation CPU becomes a concern at scale. Parked as a proposal.
