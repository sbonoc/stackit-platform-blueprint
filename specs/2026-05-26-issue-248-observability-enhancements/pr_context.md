# PR Context

## Summary
- Work item: 2026-05-26-issue-248-observability-enhancements
- Objective: Extend the blueprint observability module with Faro browser RUM telemetry receiver (both lanes), Grafana dashboard provisioning make targets (convention directory + ConfigMap + seed dashboard), and OTEL pipeline improvements (memory_limiter, healthcheck span filter, spanmetrics on local lane). All changes are additive — no existing collector behaviour is altered.
- Scope boundaries: Shell lib (`observability.sh`), both OTEL values files (`local` + `stackit`), three ArgoCD Application inline values (`dev/stage/prod`), module contract, apply/smoke scripts, two new dashboard scripts, Makefile template, seed dashboard, bootstrap mirror, tests, README. No Terraform changes. No ArgoCD Application structure changes.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-019, NFR-SEC-001, NFR-OPS-001 through NFR-OPS-003, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-013
- Contract surfaces changed: `blueprint/modules/observability/module.contract.yaml` — added `FARO_ENDPOINT` to outputs.produced; added `FARO_CORS_ALLOWED_ORIGINS` and `OBSERVABILITY_DASHBOARDS_NAME` to optional_env. Two new make targets: `infra-observability-dashboards-apply`, `infra-observability-dashboards-destroy`.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/observability.sh` — `observability_faro_endpoint()` helper and `FARO_ENDPOINT` export in `observability_init_env`
  - `infra/local/helm/observability/otel-collector.values.yaml` — Faro receiver + port, memory_limiter, filter, spanmetrics connector added to debug-only local config
  - `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` — Faro receiver + port, memory_limiter, filter added (spanmetrics was already present)
  - `infra/gitops/argocd/optional/dev/observability.yaml` — ArgoCD Application inline values updated (same changes applied to stage + prod)
  - `scripts/bin/infra/observability_dashboards_apply.sh` — new dashboard ConfigMap provisioning script
- Supporting files:
  - `blueprint/modules/observability/module.contract.yaml` — contract additions
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — new make targets
  - `infra/observability/dashboards/golden-signals.json` — seed Grafana dashboard
  - `tests/infra/modules/observability/test_contract.py` — ≥12 new assertions

## Validation Evidence
- Required commands executed: (to be filled at publish phase)
- Result summary: (to be filled at publish phase)
- Artifact references: `specs/2026-05-26-issue-248-observability-enhancements/evidence_manifest.json`

## Risk and Rollback
- Main risks: (1) ArgoCD Application inline values for dev/stage/prod must each be updated individually — mitigated by contract test asserting Faro port in all three. (2) `memory_limiter` processor ordering must be before `batch` — mitigated by contract test. (3) Dashboard apply fails if `infra/observability/dashboards/` is empty — mitigated by seed dashboard shipped with blueprint.
- Rollback strategy: revert the commit; all changes are additive and the existing collector behaviour is unchanged. ArgoCD selfHeal will reconcile the Application back to the pre-change state within one sync cycle.

## Deferred Proposals
- Proposal A (not implemented): `OBSERVABILITY_RETENTION_DAYS` shell contract — retention remains a TF-level concern; deferred to backlog.
- Proposal B (not implemented): Langfuse integration — consumer-specific; not appropriate for the generic blueprint module.
- Proposal C (not implemented): Replacing `grafana/k8s-monitoring` with separate charts — low value vs. maintenance cost; deferred indefinitely.
