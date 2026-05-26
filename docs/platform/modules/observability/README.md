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
  - `FARO_ENDPOINT`
  - `STACKIT_OBSERVABILITY_INSTANCE_ID`
  - `STACKIT_OBSERVABILITY_GRAFANA_URL`
  - `OBSERVABILITY_LOGS_ENDPOINT`
  - `OBSERVABILITY_METRICS_ENDPOINT`
  - `OBSERVABILITY_TRACES_ENDPOINT`
  - `OBSERVABILITY_API_KEY`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Module Enablement

- **Feature flag:** `OBSERVABILITY_ENABLED` (boolean, default: `false`)
- **To enable:** set `OBSERVABILITY_ENABLED=true` in your environment profile before running `make infra-observability-apply`
- **GitOps path:** `infra/gitops/argocd/optional/${ENV}/observability.yaml` — the `optional/` prefix signals opt-in per environment

## Dual-Lane Architecture

### STACKIT lane (`stackit-*` profiles)

Provisioning is managed by the STACKIT foundation Terraform layer (`infra/cloud/stackit/terraform/foundation`). The module uses the foundation-contract driver — no standalone per-module Terraform root.

**Two-phase deployment:**

1. `make infra-observability-apply` — runs `stackit_foundation_apply.sh`, reconciles the `blueprint-observability-auth` K8s Secret, writes the runtime state file.
2. `make infra-observability-deploy` — applies the ArgoCD `Application` manifest; ArgoCD syncs the in-cluster OTEL Collector Helm release.

**Signal flow:**

```
Consumer App (OTEL SDK)
  → OTLP gRPC :4317
  → otel-collector (K8s Deployment, observability namespace)
      → prometheusremotewrite → STACKIT Observability (metrics_push_url)
      → loki              → STACKIT Observability (logs_push_url)
      → otlp/stackit      → STACKIT Observability (otlp_grpc_traces_url)
```

Credentials are injected from `blueprint-observability-auth` K8s Secret via a projected volume mount at `/etc/otel/secrets` (read-only). The OTC config reads each key via the file config provider (`${file:/etc/otel/secrets/<key>}`). Push URLs are stored in the same Secret (set by the apply step using foundation TF outputs).

**STACKIT Helm values file:** `infra/cloud/stackit/helm/observability/otel-collector.values.yaml`

**ArgoCD Application:** `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` — chart `open-telemetry/opentelemetry-collector` v0.147.1, `selfHeal: true`

### Local lane (`local-*` profiles)

Crossplane + Helm deploys an in-cluster Grafana k8s-monitoring stack and OTEL Collector:
- `infra/local/helm/observability/grafana.values.yaml`
- `infra/local/helm/observability/otel-collector.values.yaml`

The local lane includes Faro receiver, memory_limiter, filter/drop-healthcheck-spans, and spanmetrics — same as STACKIT lane but exporting to `debug` instead of remote endpoints.

## Consumer Usage

Consumers only need to set one env var — identical on both lanes:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc.cluster.local:4317
```

For Faro (browser RUM) telemetry, the collector exposes a Faro-protocol endpoint:

```
FARO_ENDPOINT=http://otel-collector.observability.svc.cluster.local:12347/collect
```

This value is computed by `observability_faro_endpoint()` in `scripts/lib/infra/observability.sh` and exported as `FARO_ENDPOINT` via `observability_init_env()`. It is written to the runtime state file as `faro_endpoint`.

No lane-specific branching required. The OTEL Collector fans out signals to the appropriate backend per environment.

## OTEL Pipeline Improvements

The OTEL Collector pipeline has been enhanced with the following processors and connectors:

### Faro Receiver (port 12347)

All environments now expose a [Grafana Faro](https://grafana.com/oss/faro/) receiver at port 12347 for browser RUM telemetry. The receiver accepts Faro-protocol payloads and feeds them into the traces and logs pipelines.

- Receiver config: `faro: { endpoint: 0.0.0.0:12347, cors: { allowed_origins: ["*"] } }`
- CORS allowed origins default is `"*"` (override via `FARO_CORS_ALLOWED_ORIGINS`)
- Port 12347 is declared in the Helm `ports` section: `faro: { enabled: true, containerPort: 12347, servicePort: 12347 }`

### memory_limiter Processor (OOM Protection)

A `memory_limiter` processor is added before `batch` in all pipelines to prevent OOM:

```yaml
memory_limiter:
  check_interval: 1s
  limit_percentage: 80
  spike_limit_percentage: 25
```

Pipeline order: `memory_limiter → filter/drop-healthcheck-spans → batch` (traces), `memory_limiter → batch` (metrics/logs).

### filter/drop-healthcheck-spans (Healthcheck Noise Reduction)

A filter processor drops Kubernetes readiness/liveness probe spans to reduce trace volume:

```yaml
filter/drop-healthcheck-spans:
  error_mode: ignore
  traces:
    span:
      - attributes["http.route"] == "/healthz"
      - attributes["http.target"] == "/healthz"
```

### spanmetrics Connector (RED Metrics from Traces)

The `spanmetrics` connector auto-derives Request Rate, Error Rate, and Duration (RED) metrics from traces. This enables the Golden Signals dashboard without additional instrumentation.

Histograms: `[100us, 1ms, 2ms, 6ms, 10ms, 100ms, 250ms]`
Dimensions: `http.method`, `http.status_code`

## Runtime State File (`artifacts/infra/observability_runtime.env`)

| Key | STACKIT | Local |
|---|---|---|
| `otel_endpoint` | `http://otel-collector.observability.svc.cluster.local:4317` | same |
| `faro_endpoint` | `http://otel-collector.observability.svc.cluster.local:12347/collect` | same |
| `logs_endpoint` | STACKIT Loki push URL | empty |
| `metrics_endpoint` | STACKIT Prometheus remote-write URL | empty |
| `traces_endpoint` | STACKIT OTLP gRPC traces URL | empty |
| `api_key` | empty (delivered only via K8s Secret) | empty |

## Dashboard Provisioning

Grafana dashboards can be provisioned as Kubernetes ConfigMaps with the `grafana_dashboard: "1"` sidecar label using the following make targets:

```bash
make infra-observability-dashboards-apply    # idempotent: --dry-run=client | kubectl apply
make infra-observability-dashboards-destroy  # kubectl delete --ignore-not-found=true
```

### Seed Dashboard

`infra/observability/dashboards/golden-signals.json` — a Grafana dashboard backed by `spanmetrics` data covering the four Golden Signals:

- **Request Rate** — `traces_spanmetrics_calls_total` rate
- **Error Rate** — ratio of `status_code=STATUS_CODE_ERROR` spans
- **Latency P99** — `histogram_quantile(0.99, ...)` from `traces_spanmetrics_duration_milliseconds_bucket`
- **Saturation** — active span count

### Configuration

| Variable | Default | Description |
|---|---|---|
| `OBSERVABILITY_DASHBOARDS_NAME` | `grafana-dashboards` | ConfigMap name |
| `OBSERVABILITY_NAMESPACE` | `observability` | Target namespace |

The ConfigMap is labeled `grafana_dashboard=1` so the Grafana sidecar auto-provisions it. Provisioning is idempotent (`--dry-run=client | kubectl apply`).

A bootstrap seed copy is mirrored at `scripts/templates/blueprint/bootstrap/infra/observability/dashboards/golden-signals.json` for consumer repositories.

## K8s Secret Lifecycle

**Secret name:** `blueprint-observability-auth` (namespace: `observability`)

**Contents:** `username`, `password` (STACKIT Observability credential), `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL`

- Created: `make infra-observability-apply` (STACKIT lane only)
- Deleted: `make infra-observability-destroy` (before foundation TF destroy)
- The credential password is not written to `observability_runtime.env` or any git-tracked artifact. In Terraform state it is stored as a sensitive value and excluded from `terraform output` and plan output; it is delivered to the collector exclusively via K8s Secret.

## Security

- Credential password delivered only via K8s Secret; never appears in `observability_runtime.env` or git-tracked state.
- Push URLs are non-sensitive and appear in the runtime state file for operator visibility.
- `OBSERVABILITY_API_KEY` state key is deliberately empty — consumers use `OTEL_EXPORTER_OTLP_ENDPOINT` exclusively; no key required.

## Make Targets Reference

| Target | Description |
|---|---|
| `infra-observability-plan` | Plan observability resources and OTEL runtime contract |
| `infra-observability-apply` | Apply observability resources and OTEL collector stack |
| `infra-observability-deploy` | Deploy observability runtime config through ArgoCD |
| `infra-observability-smoke` | Smoke observability and OTEL runtime contract |
| `infra-observability-destroy` | Destroy observability artifacts |
| `infra-observability-dashboards-apply` | Apply Grafana dashboard ConfigMap from `infra/observability/dashboards/` |
| `infra-observability-dashboards-destroy` | Delete Grafana dashboard ConfigMap |

## Smoke Check

`make infra-observability-smoke` validates:
- `otel_endpoint` format is `http://...`
- `faro_endpoint` format is `http://...` (universal — both lanes)
- On STACKIT lane: `logs_endpoint`, `metrics_endpoint`, `traces_endpoint` are non-empty
- Deploy artifact health status is `Healthy`

Full signal-delivery verification (data actually arriving in STACKIT Observability) requires manual check in the STACKIT console — this is out of scope for the automated smoke check.

## Troubleshooting

**Push URL missing in state file:** Ensure `OBSERVABILITY_ENABLED=true` and foundation TF outputs include the three push URL attributes. Run `make infra-observability-apply` again.

**`blueprint-observability-auth` Secret missing:** Run `make infra-observability-apply` — the apply step reconciles the Secret. Verify the pod has an `extraVolumeMounts` entry for the `obs-auth` volume at `/etc/otel/secrets`.

**OTEL Collector not healthy in ArgoCD:** Check that `make infra-observability-deploy` completed after `make infra-observability-apply`. ArgoCD `selfHeal: true` will reconcile automatically; check the ArgoCD UI for sync errors.
