# Observability Module (Optional)

## Purpose
Provision and deploy the observability stack and the OTEL/Faro runtime contract used by backend/UI runtime components.

## Enable
Set:

```bash
export OBSERVABILITY_ENABLED=true
```

By default it is disabled.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `OBSERVABILITY_ENABLED=true`.
- `stackit-*` profiles:
  - Provisioning is managed by STACKIT foundation Terraform layer: `infra/cloud/stackit/terraform/foundation`
  - Module wrappers reconcile/verify the `foundation` contract (no standalone per-module Terraform root)
  - Managed Grafana/Loki/Tempo contract through STACKIT Observability outputs
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

## Commands
- `make infra-observability-plan`
- `make infra-observability-apply`
- `make infra-observability-deploy`
- `make infra-observability-smoke`
- `make infra-observability-destroy`
