# Hardening Review

## Repository-Wide Findings Fixed
- Finding: no repository-wide hardening regressions introduced; all 77 pre-existing unit assertions continue to pass and all quality-hooks-fast checks pass with no new failures.

## Security Review

### Faro receiver (NFR-SEC-001)
- Faro receiver accepts telemetry-only payloads. It has no read access to STACKIT backends, no write path to secrets, and no authentication surface. CORS `allowed_origins: ["${env:FARO_CORS_ALLOWED_ORIGINS}"]` defaults to `*` via `extraEnvs`; consumers override by setting `FARO_CORS_ALLOWED_ORIGINS` in their ArgoCD Application inline values — no Helm redeploy required.
- The OTC env substitution (`${env:VAR}`) uses a pod environment variable, not the file config provider. This is intentional: origin strings are non-sensitive and do not require Secret-based injection.
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
- Proposal 1: Faro per-origin CORS — implemented in this PR via OTC `${env:FARO_CORS_ALLOWED_ORIGINS}` substitution with `extraEnvs` default `*`; consumers override via ArgoCD Application `extraEnvs`.
- Proposal 2: `OBSERVABILITY_RETENTION_DAYS` shell contract — rejected. Retention is a TF-level concern; no OTEL/shell mechanism to act on it. A dangling contract var would mislead consumers.
- Proposal 3: Langfuse integration — rejected. Consumer-specific LLM observability; not appropriate for the generic blueprint module.
- Proposal 4: Replace `grafana/k8s-monitoring` with separate charts — parked. Disruptive refactor, low value vs. maintenance cost; trigger: on-scope: observability.
- Proposal 5: OTel semconv forwards-compatibility for healthcheck filter — parked. Add `url.path` as a third filter condition for OTel semconv v1.20+ SDKs; trigger: on-scope: observability.
