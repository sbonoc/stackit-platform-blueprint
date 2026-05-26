# Work Item Context Pack

## Context Snapshot
- Work item: 2026-05-26-issue-248-observability-enhancements
- Track: blueprint
- Parent issue: #248 (STACKIT-managed service modules — observability enhancements)
- Prerequisite PR: #308 (observability module baseline — merged 2026-05-20)

## Problem Being Solved

The blueprint observability module (PR #308) deploys an in-cluster OTEL Collector that accepts OTLP gRPC/HTTP from backend apps. Three capabilities observed in `sbonoc/agentic-graphrag` are not yet present in the generic module:

1. **Faro receiver missing** — frontend apps using the Grafana Faro browser SDK cannot push RUM or Web Vitals telemetry to the collector. There is no published `FARO_ENDPOINT` for consumers to configure their SDKs.

2. **No dashboard provisioning pattern** — consumers who want custom Grafana dashboards must write their own ConfigMap manifests, apply them manually, and figure out the k8s-monitoring label selector (`grafana_dashboard: "1"`) themselves.

3. **OTEL pipeline fragility** — the collector has no OOM protection (`memory_limiter`), healthcheck probe spans dominate trace volume (no `filter`), and the local lane lacks `spanmetrics` even though the STACKIT lane has it.

## Reference Implementation

`sbonoc/agentic-graphrag` demonstrates all three patterns in production:
- Faro receiver at `infra/gitops/argocd/values/base/otel-collector.yaml` (port 12347, `cors.allowed_origins: ["*"]`)
- Dashboard ConfigMap generation from `infra/observability/dashboards/*.json` via `render_grafana_dashboards_configmap.py`
- `memory_limiter`, `filter/drop-healthcheck-spans`, and `spanmetrics` in both local and cloud OTEL configs

## Key Design Choices

1. **Bash kubectl over Python renderer** for dashboard provisioning — matches existing script pattern; no extra tooling.
2. **`FARO_ENDPOINT` derived from existing env vars** (`OTEL_COLLECTOR_SERVICE_DNS`, `FARO_COLLECT_PATH`) — no new storage or secrets.
3. **`OBSERVABILITY_DASHBOARDS_NAME` env var** — lets consumers namespace their ConfigMap (e.g., `grafana-dashboards-marketplace`).
4. **Local-lane spanmetrics → debug exporter** — no Prometheus scrape target needed on local lane; consistent pipeline shape across lanes.
