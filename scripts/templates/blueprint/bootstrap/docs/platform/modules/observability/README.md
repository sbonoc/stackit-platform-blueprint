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

**STACKIT prerequisite:** The Secrets Store CSI Driver and its Vault provider must be running in `kube-system` before the observability module is deployed. Both are installed as core ArgoCD Applications in `infra/gitops/argocd/core/{env}/secrets-store-csi-driver*.yaml` with `sync-wave: -1`. See `docs/platform/prerequisites.md`.

**Two-phase deployment:**

1. `make infra-observability-apply` — runs `stackit_foundation_apply.sh`, writes observability credentials to STACKIT Secrets Manager via Vault TF provider, writes the runtime state file.
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

Credentials are delivered via the Secrets Store CSI Driver from STACKIT Secrets Manager at pod start as a tmpfs mount at `/etc/otel/secrets` (read-only). The OTC config reads each key via the file config provider (`${file:/etc/otel/secrets/<key>}`). Credentials (`username`, `password`, `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL`) are written to Secrets Manager by the Vault Terraform provider during the apply step. No K8s Secret object is created on STACKIT lanes.

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

- Receiver config: `faro: { endpoint: 0.0.0.0:12347, cors: { allowed_origins: ["${env:FARO_CORS_ALLOWED_ORIGINS}"] } }`
- CORS allowed origins default is `"*"` set via `extraEnvs: [{ name: FARO_CORS_ALLOWED_ORIGINS, value: "*" }]`
- To restrict origins: override `FARO_CORS_ALLOWED_ORIGINS` in your ArgoCD Application `extraEnvs` (single origin string; multi-origin not supported by OTC env substitution)
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

## Credential Delivery (STACKIT lane)

Credentials are delivered to the OTC pod via the Secrets Store CSI Driver — not a K8s Secret. The `blueprint-observability-auth` K8s Secret is **not** created on STACKIT lanes after this change.

**CSI path:** `observability` namespace, `SecretProviderClass: blueprint-observability-csi` → Vault provider → STACKIT Secrets Manager → tmpfs mount at `/etc/otel/secrets`

**Contents mounted as files:** `username`, `password`, `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL`

**Fail-safe:** A CSI mount failure prevents the OTC pod from starting (`ContainerCreating` stuck). This is the intended behaviour (NFR-REL-001) — credentials must be available or the pod does not start.

### Credential Rotation

1. Update the secret value in STACKIT Secrets Manager for the `observability/otel-credentials` path.
2. The CSI driver polls for changes on its configured rotation interval (default: 2 minutes). Files in the tmpfs mount are updated automatically without a pod restart.
3. For immediate rotation: restart the OTC pod (`kubectl rollout restart deployment blueprint-otel-collector -n observability`).

## K8s Secret Lifecycle (local lane only)

**Secret name:** `blueprint-observability-auth` (namespace: `observability`)

**Contents:** `username`, `password`, `METRICS_PUSH_URL`, `LOGS_PUSH_URL`, `TRACES_PUSH_URL`

- Created: `make infra-observability-apply` (local lane only — `crossplane_plus_helm` driver)
- Deleted: `make infra-observability-destroy` (local lane only)
- The credential password is not written to `observability_runtime.env` or any git-tracked artifact.

## Security

- **STACKIT lane:** Credentials delivered via CSI tmpfs mount from STACKIT Secrets Manager — never written to etcd. `blueprint-observability-auth` K8s Secret does not exist post-deploy on STACKIT profiles. Credential reads are auditable via Secrets Manager access logs.
- **Local lane:** Credential password delivered only via K8s Secret; never appears in `observability_runtime.env` or git-tracked state.
- Push URLs are non-sensitive and appear in the runtime state file for operator visibility.
- `OBSERVABILITY_API_KEY` state key is deliberately empty — consumers use `OTEL_EXPORTER_OTLP_ENDPOINT` exclusively; no key required.
- `SecretProviderClass` is namespace-scoped to `observability` — no cross-namespace secret access (NFR-SEC-003).

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

**OTC pod stuck in `ContainerCreating` (STACKIT lane):** The CSI driver cannot mount the credential volume. Verify: (1) the Secrets Store CSI Driver DaemonSet is running in `kube-system`; (2) the Vault provider sidecar is running; (3) STACKIT Secrets Manager is accessible from the cluster; (4) the `SecretProviderClass blueprint-observability-csi` exists in the `observability` namespace.

**OTEL Collector not healthy in ArgoCD:** Check that `make infra-observability-deploy` completed after `make infra-observability-apply`. ArgoCD `selfHeal: true` will reconcile automatically; check the ArgoCD UI for sync errors.

**`blueprint-observability-auth` Secret missing (local lane only):** Run `make infra-observability-apply` — the apply step reconciles the Secret on local profiles. On STACKIT profiles, this Secret is intentionally not created.
