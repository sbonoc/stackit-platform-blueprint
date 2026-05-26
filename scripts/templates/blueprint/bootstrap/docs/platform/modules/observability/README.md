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

Local lane is unchanged by this work item.

## Consumer Usage

Consumers only need to set one env var — identical on both lanes:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc.cluster.local:4317
```

No lane-specific branching required. The OTEL Collector fans out signals to the appropriate backend per environment.

## Runtime State File (`artifacts/infra/observability_runtime.env`)

| Key | STACKIT | Local |
|---|---|---|
| `otel_endpoint` | `http://otel-collector.observability.svc.cluster.local:4317` | same |
| `logs_endpoint` | STACKIT Loki push URL | empty |
| `metrics_endpoint` | STACKIT Prometheus remote-write URL | empty |
| `traces_endpoint` | STACKIT OTLP gRPC traces URL | empty |
| `api_key` | empty (delivered only via K8s Secret) | empty |

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

## Smoke Check

`make infra-observability-smoke` validates:
- `otel_endpoint` format is `http://...`
- On STACKIT lane: `logs_endpoint`, `metrics_endpoint`, `traces_endpoint` are non-empty
- Deploy artifact health status is `Healthy`

Full signal-delivery verification (data actually arriving in STACKIT Observability) requires manual check in the STACKIT console — this is out of scope for the automated smoke check.

## Troubleshooting

**Push URL missing in state file:** Ensure `OBSERVABILITY_ENABLED=true` and foundation TF outputs include the three push URL attributes. Run `make infra-observability-apply` again.

**`blueprint-observability-auth` Secret missing:** Run `make infra-observability-apply` — the apply step reconciles the Secret. Verify the pod has an `extraVolumeMounts` entry for the `obs-auth` volume at `/etc/otel/secrets`.

**OTEL Collector not healthy in ArgoCD:** Check that `make infra-observability-deploy` completed after `make infra-observability-apply`. ArgoCD `selfHeal: true` will reconcile automatically; check the ArgoCD UI for sync errors.
