# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: ArgoCD health=N/A for all local-lane managed resources — caused by the argo-cd Helm chart 9.4.16 default `resource.customizations.ignoreResourceUpdates.all: /status` suppressing watch events that ArgoCD v3.x health evaluator depends on. Fixed by overriding the key to empty string in `argocd.values.yaml` and the bootstrap template, and bumping the chart to 9.5.13 (ArgoCD v3.4.1).

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: none — ArgoCD health status becomes meaningful after deploy; no new metrics, logs, or traces added by this work item.
- Operational diagnostics updates: none — `argocd app get platform-local-core` will now correctly reflect `Health: Healthy` when pods are running; no new diagnostic commands required.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: N/A — pure YAML configuration change and chart version pin; no application layer code introduced.
- Test-automation and pyramid checks: 4 unit regression tests added (`tests/infra/test_argocd_values_health_fix.py`), classified in the `unit` scope of `test_pyramid_contract.json`. No integration or e2e tests added. Pyramid thresholds unaffected.
- Documentation/diagram/CI/skill consistency checks: ADR written and approved. Architecture diagram in `architecture.md` correctly represents the before/after health evaluation path. No CI YAML changes required.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI changes
- [x] SC 2.1.1 (Keyboard): N/A — no UI changes
- [x] SC 2.4.7 (Focus Visible): N/A — no UI changes
- [x] SC 1.4.1 (Use of Color): N/A — no UI changes
- [x] SC 3.3.1 (Error Identification): N/A — no UI changes
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI changes

## Proposals Only (Not Implemented)
- Proposal 1: Per-resource-type `ignoreResourceUpdates` tuning for genuinely noisy types (ConfigMap, Endpoints) if reconciliation CPU becomes a concern at scale. Parked — trigger: on-scope: infra — no current CPU pressure evidence on local Docker Desktop; backlog entry added.
