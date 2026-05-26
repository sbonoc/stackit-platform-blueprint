# Hardening Review

## Repository-Wide Findings Fixed
- No repository-wide hardening findings identified at intake. This section will be updated before publish phase with any findings discovered during implementation.

## Security Review

### Faro receiver (NFR-SEC-001)
- Faro receiver accepts telemetry-only payloads. It has no read access to STACKIT backends, no write path to secrets, and no authentication surface. CORS `allowed_origins: ["*"]` is appropriate for a telemetry ingress.
- The Faro receiver port (12347) is in-cluster only; no NodePort or LoadBalancer Service is declared. Browser apps reach it via in-cluster DNS (`otel-collector.observability.svc.cluster.local:12347`), meaning only workloads running inside the cluster can push Faro telemetry. External browser access requires an explicit Ingress or Gateway route, which is out of scope.

### Dashboard provisioning (FR-013, NFR-OPS-002, NFR-OPS-003)
- The apply script creates a ConfigMap with no Secret material. ConfigMap contents are limited to Grafana dashboard JSON — no credentials or sensitive data.
- The `--dry-run=client | kubectl apply` pattern ensures idempotency and does not alter existing resources outside the target ConfigMap name.
- `OBSERVABILITY_DASHBOARDS_NAME` allows consumers to namespace their ConfigMaps without conflicting with platform-owned ConfigMaps.

### OTEL pipeline changes (FR-009, FR-010)
- `memory_limiter` does not alter data content — it drops telemetry when memory pressure exceeds the configured threshold. No security impact.
- `filter/drop-healthcheck-spans` drops spans by attribute value. The filter is applied before batch export, so dropped spans never reach STACKIT push URLs. No security impact; reduces telemetry noise.

## Observability and Diagnostics Changes
- `faro_endpoint` key added to `observability_runtime.env` state file — operators can verify the Faro endpoint is written without reading shell scripts.
- `memory_limiter` exposes an OTC internal metric (`otelcol_processor_refused_metric_points`, `otelcol_processor_refused_spans`) on the collector's metrics port (default 8888) indicating when the limiter is actively dropping data. No additional diagnostic instrumentation needed.
- `spanmetrics` on local lane derives RED metrics (rate, errors, duration) from traces visible in local Grafana via the debug exporter log stream.

## Architecture and Code Quality Compliance
- All five OTEL config sources (local values, STACKIT values, dev/stage/prod ArgoCD manifests) are updated consistently — no config drift between the values file template and the inline ArgoCD values.
- `observability_faro_endpoint()` follows the existing helper function pattern (`observability_metrics_push_url`, etc.) — pure function, no side effects.
- Dashboard apply/destroy scripts follow the bootstrap.sh + profile.sh sourcing pattern consistent with all other `scripts/bin/infra/*.sh` scripts.
- Seed dashboard is generic (golden-signals) and not consumer-specific — appropriate for the blueprint module.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- WCAG 2.2 AA — N/A; no UI changes.
- Keyboard navigation — N/A.
- Screen reader compatibility — N/A.
- Color contrast — N/A.

## Proposals Only (Not Implemented)
- **Faro per-origin CORS** — configuring CORS via env var injection into OTC Helm values is not supported by the file config provider pattern; deferred. Consumers can override inline ArgoCD values.
- **`OBSERVABILITY_RETENTION_DAYS` shell contract** — retention is a TF-level concern; deferred to backlog.
- **Langfuse integration** — consumer-specific; not appropriate for the generic blueprint module.
- **Separate charts for local observability** — replacing `grafana/k8s-monitoring` with individual Grafana/Loki/Prometheus/Tempo charts; deferred indefinitely.
