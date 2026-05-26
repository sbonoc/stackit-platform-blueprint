# ADR: Observability Module Enhancements — Faro Receiver, Dashboard Provisioning, OTEL Pipeline Improvements

- **Status:** proposed
- **Work item:** 2026-05-26-issue-248-observability-enhancements
- **Date:** 2026-05-26
- **Author:** bonos

## Context

The blueprint observability module (PR #308) ships an in-cluster OTEL Collector on both local and STACKIT lanes configured with OTLP gRPC/HTTP receivers and push exporters (STACKIT lane). Three capabilities present in the `sbonoc/agentic-graphrag` consumer reference implementation are missing from the generic blueprint module:

1. **Faro receiver** — browser frontend apps cannot push RUM/Web Vitals telemetry to the collector.
2. **Dashboard provisioning** — there is no convention or tooling for consumers to load custom Grafana dashboards.
3. **OTEL pipeline safety** — the collector has no memory ceiling (`memory_limiter`), no span noise filter (healthcheck probes dominate trace volume), and the local lane lacks the `spanmetrics` connector present on the STACKIT lane.

## Decision 1: Dashboard provisioning approach

**Decision:** Convention directory `infra/observability/dashboards/` + Bash `kubectl create configmap --dry-run=client | kubectl apply` script pair, with ConfigMap label `grafana_dashboard: "1"`.

**Rationale:**

| Approach | Pros | Cons |
|---|---|---|
| A — kubectl convention dir (selected) | Matches existing script pattern; idempotent; no extra tooling; consumers add dashboards by dropping JSON files | Requires kubectl context; no JSON linting at apply time |
| B — Helm `dashboardProviders` values key | No extra script needed | Requires Grafana Helm redeploy to update; JSON embedded in YAML (noisy diffs); can't be driven by file convention |
| C — Python renderer (agentic-graphrag pattern) | Testable; strict JSON validation | Adds Python dependency to an infra-level operation; overkill for kubectl apply pattern |

Option A is consistent with `observability_dashboards_apply.sh` / `destroy.sh` naming, uses the declarative `--dry-run | apply` pattern (safe on retry), and lets consumers manage dashboards as plain JSON files without Helm knowledge. The Grafana k8s-monitoring sidecar discovers ConfigMaps with `grafana_dashboard: "1"` in any namespace — the label is the standard provisioning contract.

## Decision 2: Faro CORS origin policy

**Decision:** Default `allowed_origins: ["*"]`.

**Rationale:** Faro is a telemetry-only receiver. It does not proxy requests to STACKIT backends or carry credentials. The CORS `allowed_origins` field controls which browser origins the receiver accepts — it is not a security boundary for the observability backends. Setting `*` maximises compatibility with browser SDKs deployed on any domain, which is the expected consumer pattern. Consumers requiring stricter CORS (e.g., single-tenant production environments) can override the inline values in their ArgoCD Application manifests.

## Decision 3: Faro port selection

**Decision:** Port 12347 (OpenTelemetry Collector contrib default for the Faro receiver).

**Rationale:** Port 12347 is the upstream OTC default, matching the agentic-graphrag production deployment. Using the upstream default avoids custom port mapping documentation and is forward-compatible with OTC upgrades.

## Decision 4: Local-lane spanmetrics export target

**Decision:** Local lane spanmetrics export to `debug` exporter only (no Prometheus scrape target on local lane).

**Rationale:** The local lane deploys `grafana/k8s-monitoring`, which ships its own Prometheus instance that scrapes the cluster. Adding a `prometheusremotewrite` exporter for spanmetrics on the local lane would require wiring the collector's Prometheus port to a scrape config, adding configuration complexity. Debug export is sufficient for local development — the metrics are visible in collector logs. This is consistent with the existing local-lane configuration (debug-only exporters).

## Consequences

- `FARO_ENDPOINT` becomes a stable contract output on both lanes: `http://otel-collector.observability.svc.cluster.local:12347/collect`.
- Two new make targets (`infra-observability-dashboards-apply/destroy`) are added to the blueprint Makefile.
- `memory_limiter` protects all collector instances from OOM kills under burst load.
- `filter/drop-healthcheck-spans` eliminates K8s liveness probe spans from trace volume on all environments.
- `spanmetrics` on the local lane gives developers consistent pipeline behaviour across lanes.
