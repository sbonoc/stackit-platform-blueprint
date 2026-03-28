# Observability Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision and deploy observability stack plus OTEL/Faro runtime wiring for all components.
- Enable flag: `OBSERVABILITY_ENABLED` (default: `false`)
- Required inputs:
- Make targets:
  - `infra-observability-plan`
  - `infra-observability-apply`
  - `infra-observability-deploy`
  - `infra-observability-smoke`
  - `infra-observability-destroy`
- Outputs:
  - `OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OTEL_PROTOCOL`
  - `OTEL_TRACES_ENABLED`
  - `OTEL_METRICS_ENABLED`
  - `OTEL_LOGS_ENABLED`
  - `FARO_ENABLED`
  - `FARO_COLLECT_PATH`
  - `STACKIT_OBSERVABILITY_INSTANCE_ID`
  - `STACKIT_OBSERVABILITY_GRAFANA_URL`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `OBSERVABILITY_ENABLED=true`.
- `stackit-*` profiles:
  - Provisioning is managed by STACKIT foundation Terraform layer: `infra/cloud/stackit/terraform/foundation`
  - Module wrappers reconcile/verify the `foundation` contract (no standalone per-module Terraform root)
  - Managed Grafana/Loki/Tempo contract through STACKIT Observability outputs
  - The default `Observability-Monitoring-Medium-EU01` plan does not accept explicit log/trace retention overrides, so those provider arguments are omitted unless you opt into a compatible plan/override strategy.
- `local-*` profiles:
  - Crossplane path: `infra/local/crossplane/`
  - Helm values:
    - `infra/local/helm/observability/grafana.values.yaml`
    - `infra/local/helm/observability/otel-collector.values.yaml`

## Runtime OTEL Contract
When enabled, module outputs/wires:
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_PROTOCOL`
- `OTEL_TRACES_ENABLED`
- `OTEL_METRICS_ENABLED`
- `OTEL_LOGS_ENABLED`
- `FARO_ENABLED`
- `FARO_COLLECT_PATH`

These values are also propagated into the app catalog contract (`apps/catalog/manifest.yaml`) under `observabilityRuntimeContract`.
