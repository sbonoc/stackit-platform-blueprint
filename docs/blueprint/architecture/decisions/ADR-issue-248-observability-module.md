# ADR — Observability Module: In-Cluster OTEL Collector on STACKIT Lane

- **Status:** approved
- **ADR technical decision sign-off:** approved
- **Work item:** issue-248-observability-module
- **Date:** 2026-05-18
- **Author:** sbonoc

## Context

The blueprint observability module already deploys an in-cluster OpenTelemetry Collector + Grafana stack on the local (Docker Desktop) lane via Helm. On the STACKIT lane, the module provisions a `stackit_observability_instance` + `stackit_observability_credential` via the foundation Terraform layer, but the `observability_apply.sh` script writes `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc.cluster.local:4317` to the runtime state file even though the otel-collector Helm release is **never deployed** on the STACKIT lane — leaving this endpoint as a dangling DNS reference.

Additionally, the issue #248 integration contract specifies four new outputs (`OBSERVABILITY_LOGS_ENDPOINT`, `OBSERVABILITY_METRICS_ENDPOINT`, `OBSERVABILITY_TRACES_ENDPOINT`, `OBSERVABILITY_API_KEY`) that are not yet populated by any script.

The reference architecture in `sbonoc/agentic-graphrag` uses an OTEL Collector as the central signal aggregation hub on all environments, with consumers pointing to a stable in-cluster DNS endpoint. Signals fan out from the collector to the appropriate backends per environment.

## Decision

**Option A (selected): Deploy an in-cluster OTEL Collector on the STACKIT lane via ArgoCD.**

- On the STACKIT lane, the `infra-observability-deploy` step applies an ArgoCD `Application` resource that deploys the `open-telemetry/opentelemetry-collector` Helm chart into the `observability` namespace.
- The collector is configured with OTLP gRPC+HTTP receivers (identical to local lane) and three backend exporters: `prometheusremotewrite` (STACKIT metrics push URL), `loki` (STACKIT logs push URL), `otlp/stackit` (STACKIT traces push URL). Credentials are injected via `extraEnvFrom` referencing a `blueprint-observability-auth` K8s Secret.
- `OTEL_EXPORTER_OTLP_ENDPOINT` remains `http://otel-collector.observability.svc.cluster.local:4317` on both lanes — consumers require no lane-specific configuration.
- The four new outputs (`OBSERVABILITY_LOGS_ENDPOINT`, `OBSERVABILITY_METRICS_ENDPOINT`, `OBSERVABILITY_TRACES_ENDPOINT`) are written to the runtime state file as the STACKIT push URLs (non-sensitive), used to configure the collector. `OBSERVABILITY_API_KEY` state key is deliberately empty — the credential is delivered only via the K8s Secret.

**Option B (rejected): Expose STACKIT push URLs directly; consumers push without a collector.**

- Consumers would need to handle credential injection and different endpoint contracts per lane.
- Breaks the `OTEL_EXPORTER_OTLP_ENDPOINT` single-endpoint abstraction.
- Forces lane-specific branching in every consumer application.

## Consequences

- The `blueprint-observability-auth` K8s Secret is created by `observability_apply.sh` on the STACKIT lane and destroyed by `observability_destroy.sh`.
- The `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` files are extended with an ArgoCD `Application` resource alongside the existing metadata `ConfigMap`.
- `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` is created for the STACKIT-lane collector configuration.
- Foundation TF `outputs.tf` is extended with `observability_metrics_push_url`, `observability_logs_push_url`, `observability_traces_push_url` (exact attribute names verified against provider v0.88.0 at Slice 2; fallback to URL construction from instance_id + region if attributes are absent).
- Local lane is unchanged — existing crossplane+Helm deployment continues as-is.
- No consumer-facing contract change: `OTEL_EXPORTER_OTLP_ENDPOINT` is still the only env var consumers need.

## Open Questions

All questions resolved.

- **Q-1 (resolved 2026-05-19, PR #308):** Verified against provider v0.88.0 source. Confirmed attributes: `metrics_push_url` (Prometheus remote write), `logs_push_url` (Loki push), `otlp_grpc_traces_url` (OTLP gRPC traces — selected over `otlp_http_traces_url` and `jaeger_traces_url` to keep the full pipeline OTLP gRPC end-to-end with no protocol transcoding). No URL construction fallback required.
