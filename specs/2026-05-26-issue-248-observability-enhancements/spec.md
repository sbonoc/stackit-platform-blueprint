# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-observability-enhancements.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-001 excluded — no missing inputs; SDD-C-018 excluded — no blueprint upstream workarounds; SDD-C-022/SDD-C-023 excluded — no new HTTP route handlers or payload-transform logic in the application layer; SDD-C-024 excluded — no pre-PR smoke/deterministic failures at intake.

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: STACKIT Observability has no local-lane managed equivalent; local lane deploys in-cluster OTEL Collector + Grafana k8s-monitoring stack on Docker Desktop (established pattern for this module).

## Objective
- Business outcome: Extend the blueprint observability module with three additive capabilities derived from an existing consumer reference implementation — Faro browser RUM telemetry receiver (both lanes), Grafana dashboard provisioning make targets (convention directory + ConfigMap + seed dashboards), and OTEL pipeline improvements (memory_limiter, healthcheck span filter, spanmetrics on local lane). Consumers gain a single `FARO_ENDPOINT` contract on both lanes, a drop-in dashboard provisioning pattern, and an OOM-safe collector pipeline.
- Success metric: `FARO_ENDPOINT` resolves to `http://otel-collector.observability.svc.cluster.local:12347/collect` on both lanes; `make infra-observability-dashboards-apply` creates a labeled ConfigMap Grafana auto-discovers; `make infra-observability-smoke` validates `faro_endpoint`; `python3 -m pytest tests/infra/modules/observability/ -x -q` passes with ≥ 12 new assertions.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST add `observability_faro_endpoint()` to `scripts/lib/infra/observability.sh`, returning `http://${OTEL_COLLECTOR_SERVICE_DNS}:12347${FARO_COLLECT_PATH}` (using the existing env vars set by `observability_init_env`). The function MUST be usable from both apply and init_env contexts.
- FR-002 MUST export `FARO_ENDPOINT` from `observability_init_env()` via `set_default_env FARO_ENDPOINT "$(observability_faro_endpoint)"`. This gives consumer apps a contract-stable env var on both lanes without lane-specific branching.
- FR-003 MUST update `infra/local/helm/observability/otel-collector.values.yaml` to add: (a) `faro` receiver with `endpoint: 0.0.0.0:12347` and `cors.allowed_origins: ["${env:FARO_CORS_ALLOWED_ORIGINS}"]` (OTC env substitution); (b) `extraEnvs: [{ name: FARO_CORS_ALLOWED_ORIGINS, value: "*" }]` default; (c) `faro: { enabled: true, containerPort: 12347, servicePort: 12347, protocol: TCP }` port entry; (d) `faro` receiver included in traces and logs pipeline receivers.
- FR-004 MUST update `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` with identical Faro receiver, `extraEnvs` default, and port config as the local lane (this file is the baseline template for ArgoCD inline values).
- FR-005 MUST update all three ArgoCD Application inline values blocks in `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` to add Faro receiver (port 12347, `cors.allowed_origins: ["${env:FARO_CORS_ALLOWED_ORIGINS}"]`), `extraEnvs: [{ name: FARO_CORS_ALLOWED_ORIGINS, value: "*" }]` default, the `faro` Service port declaration, and include `faro` in the traces and logs pipeline receivers.
- FR-006 MUST add `FARO_ENDPOINT` to `outputs.produced` in `blueprint/modules/observability/module.contract.yaml`. MUST add `FARO_CORS_ALLOWED_ORIGINS` to `optional_env` with default `*`.
- FR-007 MUST update `scripts/bin/infra/observability_apply.sh` to write `faro_endpoint=$(observability_faro_endpoint)` to `observability_runtime.env` on both lanes (alongside the existing `faro_enabled` and `faro_collect_path` keys).
- FR-008 MUST update `scripts/bin/infra/observability_smoke.sh` to validate on both lanes that `faro_endpoint` is non-empty and starts with `http`.
- FR-009 MUST add `memory_limiter` processor config (`check_interval: 1s`, `limit_percentage: 80`, `spike_limit_percentage: 25`) to both lane OTEL values files and all three ArgoCD Application inline values. The processor MUST appear before `batch` in all pipeline processor chains.
- FR-010 MUST add `filter/drop-healthcheck-spans` processor to both lane values files and all three ArgoCD Application inline values. Config: `error_mode: ignore`, span filter on `attributes["http.route"] == "/healthz"` OR `attributes["http.target"] == "/healthz"`. The processor MUST appear after `memory_limiter` and before `batch` in the traces pipeline only.
- FR-011 MUST add `spanmetrics` connector to `infra/local/helm/observability/otel-collector.values.yaml`. The local traces pipeline MUST export to `[spanmetrics, debug]`; the local metrics pipeline MUST receive from `[otlp, spanmetrics]`. (The STACKIT lane already has `spanmetrics`.)
- FR-012 MUST create `infra/observability/dashboards/golden-signals.json` — a valid Grafana dashboard JSON monitoring the four golden signals (latency, traffic, errors, saturation) derived from spans via the `spanmetrics` connector's Prometheus endpoint.
- FR-013 MUST create `scripts/bin/infra/observability_dashboards_apply.sh`. The script MUST: source bootstrap.sh and profile.sh; derive ConfigMap name from `${OBSERVABILITY_DASHBOARDS_NAME:-grafana-dashboards}` and namespace from `${OBSERVABILITY_NAMESPACE:-observability}`; apply a ConfigMap containing all `*.json` files from `infra/observability/dashboards/` with label `grafana_dashboard: "1"`, using `kubectl create configmap ... --from-file=... -o yaml --dry-run=client | kubectl apply -f -`.
- FR-014 MUST create `scripts/bin/infra/observability_dashboards_destroy.sh`. The script MUST delete the ConfigMap `${OBSERVABILITY_DASHBOARDS_NAME:-grafana-dashboards}` in `${OBSERVABILITY_NAMESPACE:-observability}`, tolerating `NotFound` errors.
- FR-015 MUST declare `infra-observability-dashboards-apply` and `infra-observability-dashboards-destroy` make targets in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and `make/blueprint.generated.mk`. Both MUST be added to the PHONY list.
- FR-016 MUST mirror the seed dashboard file(s) to `scripts/templates/blueprint/bootstrap/infra/observability/dashboards/` so consumer repos seeded from the bootstrap template receive the seed dashboards out of the box.
- FR-017 MUST add `OBSERVABILITY_DASHBOARDS_NAME` to `blueprint/modules/observability/module.contract.yaml` under `inputs.optional_env` with default `grafana-dashboards`.
- FR-018 MUST add ≥ 12 new assertions to `tests/infra/modules/observability/test_contract.py` covering: `observability_faro_endpoint` in shell lib; `FARO_ENDPOINT` in contract outputs; Faro port 12347 in local values, STACKIT values, and each ArgoCD manifest; `memory_limiter` in local and STACKIT values; `filter/drop-healthcheck-spans` in local and STACKIT values; `spanmetrics` in local values; `infra-observability-dashboards-apply` target in Makefile template; seed dashboard JSON file exists; `OBSERVABILITY_DASHBOARDS_NAME` in contract optional_env.
- FR-019 MUST update `docs/platform/modules/observability/README.md` to document: `FARO_ENDPOINT` output and URL format; dashboard provisioning section with `infra-observability-dashboards-apply/destroy` usage and `OBSERVABILITY_DASHBOARDS_NAME`; OTEL pipeline improvements (memory_limiter, filter, spanmetrics on local lane); updated runtime state table with `faro_endpoint` key; updated make targets section.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 Faro receiver MUST default `allowed_origins` to `["*"]` via OTC env substitution (`${env:FARO_CORS_ALLOWED_ORIGINS}` with `extraEnvs` default `*`). Faro is a telemetry-only ingress — it has no write access to STACKIT backends; a blanket origin restriction would block legitimate browser SDKs without security benefit. Consumers requiring stricter CORS MUST override `FARO_CORS_ALLOWED_ORIGINS` via their ArgoCD Application `extraEnvs` override. Single-origin strings are supported; multi-origin requires comma-separated injection (single OTC env var limitation).
- NFR-OPS-001 `memory_limiter` MUST be declared before `batch` in all pipeline processor chains on both lanes and in all ArgoCD Application inline values. Out-of-order placement risks the batch exporter buffering telemetry that MUST be dropped before export, amplifying memory pressure rather than containing it.
- NFR-OPS-002 The dashboard ConfigMap MUST carry the label `grafana_dashboard: "1"`. Without this label the Grafana sidecar does not auto-discover the ConfigMap and dashboards are not loaded.
- NFR-OPS-003 The dashboard apply script MUST use `kubectl create configmap ... --dry-run=client | kubectl apply` (declarative, idempotent) rather than imperative `kubectl create`. Imperative creates fail on re-run if the ConfigMap already exists; declarative apply is safe on retry.
- NFR-A11Y-001 N/A — no UI or frontend changes in this work item.

## Acceptance Criteria

- AC-001 `observability_faro_endpoint()` in `observability.sh` returns `http://otel-collector.observability.svc.cluster.local:12347/collect` when default env vars are active.
- AC-002 `FARO_ENDPOINT` appears in `module.contract.yaml` under `outputs.produced`.
- AC-003 Port `12347` appears in `infra/local/helm/observability/otel-collector.values.yaml` under `ports.faro`.
- AC-004 Port `12347` appears in `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` under `ports.faro`.
- AC-005 `faro` receiver appears in the traces and logs pipeline receivers of the local OTEL values file and each of the three ArgoCD Application inline values blocks.
- AC-006 `memory_limiter` processor appears before `batch` in all pipeline configs — local values, STACKIT values, and all three ArgoCD manifests.
- AC-007 `filter/drop-healthcheck-spans` processor appears in the traces pipeline of all five OTEL config sources (local values, STACKIT values, dev/stage/prod ArgoCD manifests).
- AC-008 `spanmetrics` connector appears in `infra/local/helm/observability/otel-collector.values.yaml` traces (exporter) and metrics (receiver) pipelines.
- AC-009 `infra/observability/dashboards/golden-signals.json` exists and is valid JSON containing a Grafana dashboard definition.
- AC-010 `infra-observability-dashboards-apply` make target creates a ConfigMap named `grafana-dashboards` in namespace `observability` with label `grafana_dashboard: "1"` when `OBSERVABILITY_DASHBOARDS_NAME` is unset.
- AC-011 `infra-observability-dashboards-destroy` make target removes the ConfigMap without error.
- AC-012 `python3 -m pytest tests/infra/modules/observability/ -x -q` passes with ≥ 12 new assertions.
- AC-013 `make quality-hooks-fast` passes with no regressions.

## Open Questions

All questions resolved before intake. No open questions.

## Normative Option Decisions

### Option Decision 1: Dashboard provisioning implementation approach

- Option A: Convention directory `infra/observability/dashboards/` + make target using `kubectl create configmap --dry-run=client | kubectl apply` — declarative, idempotent, no extra tooling required (selected).
- Option B: Bake dashboards into Grafana Helm chart values via `dashboardProviders` and `dashboards` keys — static, requires full Grafana re-deploy to update dashboards; cannot be driven by consumers adding JSON files.
- Option C: Python renderer script — more testable but adds a Python dependency to an operation that is straightforward with kubectl.
- Selected option: OPTION_A
- Rationale: Bash + kubectl matches the existing apply/destroy script pattern across all blueprint optional modules. Declarative `--dry-run=client | apply` is idempotent and safe on retry. A separate convention directory lets consumers add/replace dashboards without touching Helm values.

### Option Decision 2: Faro CORS origin policy

- Option A: Hardcode `allowed_origins: ["*"]` — maximum compatibility; Faro is not a security boundary.
- Option B: Runtime-configurable `allowed_origins: ["${env:FARO_CORS_ALLOWED_ORIGINS}"]` via OTC env substitution (pod env var) + `extraEnvs` default `*`; consumers override via ArgoCD Application `extraEnvs` without a Helm redeploy (selected).
- Selected option: OPTION_B
- Rationale: OTC env substitution (`${env:VAR}`) is separate from the file config provider and operates on pod-level env vars — it is fully supported for non-sensitive config like CORS origin strings. Using env substitution makes `FARO_CORS_ALLOWED_ORIGINS` a live override point without requiring consumers to fork or patch the values file. The `extraEnvs` default of `*` preserves the maximum-compatibility baseline while enabling per-deployment restriction. Single-origin string supported; multi-origin requires a single wildcard pattern.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/modules/observability/module.contract.yaml` — add `FARO_ENDPOINT` to `outputs.produced`; add `FARO_CORS_ALLOWED_ORIGINS` and `OBSERVABILITY_DASHBOARDS_NAME` to `optional_env`.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: two new make targets — `infra-observability-dashboards-apply` and `infra-observability-dashboards-destroy`.
- Docs contract: `docs/platform/modules/observability/README.md` updated; `infra/observability/dashboards/golden-signals.json` new seed dashboard.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
(See Acceptance Criteria section above — AC-001 through AC-013.)

## Informative Notes (Non-Normative)
- Context: The Faro receiver, memory_limiter, healthcheck span filter, and local-lane spanmetrics connector were observed in an existing consumer deployment. This work item extracts those patterns into the generic blueprint module so every consumer benefits by default.
- Dashboard provisioning pattern: The `grafana_dashboard: "1"` label is the standard k8s-monitoring (Grafana) sidecar label selector. Any ConfigMap carrying this label in the observability namespace is auto-discovered and mounted into Grafana's dashboard provisioner. Consumers can extend by adding their own JSON files to `infra/observability/dashboards/` before running the apply target.
- Tradeoffs: Adding `memory_limiter` adds a small CPU overhead per telemetry pipeline pass. The tradeoff is justified — OOM kills are a known production failure mode for OTEL collectors under burst load.

## Explicit Exclusions
- Faro CORS per-origin configuration via file config provider (Helm values static list) — see Option Decision 2: OPTION_B selected; env substitution via OTC `${env:FARO_CORS_ALLOWED_ORIGINS}` is the implemented mechanism.
- `OBSERVABILITY_RETENTION_DAYS` shell contract — still deferred; retention is a TF-level concern (see backlog).
- Langfuse integration — consumer-specific, not generic.
- Replacing `grafana/k8s-monitoring` all-in-one chart with separate Grafana/Loki/Prometheus/Tempo charts — disruptive refactor, low value given k8s-monitoring covers the same stack with less consumer maintenance burden.
