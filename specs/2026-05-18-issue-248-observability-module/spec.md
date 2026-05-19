# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-observability-module.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

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
- Local-first exception rationale: STACKIT Observability has no local-lane managed equivalent; the local lane deploys an in-cluster OTEL collector + Grafana stack via Helm on Docker Desktop, which is the established pattern for this module.

## Module Enablement

- **Feature toggle:** `OBSERVABILITY_ENABLED` (type: boolean, default: `false`)
- **Declared in:** `blueprint/modules/observability/module.contract.yaml` — `enable_flag: OBSERVABILITY_ENABLED`; also listed under `optional_env`
- **Runtime guard:** `scripts/bin/infra/observability_apply.sh` exits immediately when `OBSERVABILITY_ENABLED=false`; no Terraform, no secret reconciliation, no state file writes
- **GitOps convention:** manifests live under `infra/gitops/argocd/optional/${ENV}/observability.yaml` — the `optional/` path is the platform-wide signal that the module is opt-in and not applied to every cluster by default
- **TF guard:** foundation TF outputs (`observability_metrics_push_url`, `observability_logs_push_url`, `observability_traces_push_url`) are conditional on `var.observability_enabled`; they emit empty strings when the module is disabled
- **To enable:** set `OBSERVABILITY_ENABLED=true` in the environment profile before running `make infra-observability-apply`

## Objective
- Business outcome: Blueprint consumers can provision a STACKIT Observability instance on the STACKIT lane and use an identical `OTEL_EXPORTER_OTLP_ENDPOINT` contract on both local and STACKIT lanes — eliminating the dangling OTEL endpoint bug where the STACKIT lane wrote a cluster-internal collector DNS that was never deployed. All signals (traces, metrics, logs) flow through an in-cluster OTEL collector on both lanes; the collector is configured per-lane to fan out to either local backends (Grafana stack) or STACKIT Observability push URLs.
- Success metric: `make infra-observability-apply && make infra-observability-deploy` succeeds on the STACKIT lane, writes all required state keys including `logs_endpoint`, `metrics_endpoint`, `traces_endpoint`, `api_key`, and the smoke check exits 0. `test_contract.py` passes with ≥ 15 assertions. `OTEL_EXPORTER_OTLP_ENDPOINT` resolves to `http://otel-collector.observability.svc.cluster.local:4317` on both lanes.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST extend `infra/cloud/stackit/terraform/foundation/outputs.tf` and its bootstrap template copy `scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/outputs.tf` to expose the following STACKIT Observability instance push-URL outputs: `observability_metrics_push_url` (from `stackit_observability_instance.foundation[0].metrics_push_url`), `observability_logs_push_url` (from `stackit_observability_instance.foundation[0].logs_push_url`), `observability_traces_push_url` (from `stackit_observability_instance.foundation[0].otlp_grpc_traces_url`). Each output MUST be conditional on `var.observability_enabled` and MUST be non-sensitive (push URLs contain no credential material).
- FR-002 MUST add three helper functions to `scripts/lib/infra/observability.sh`: `observability_metrics_push_url()`, `observability_logs_push_url()`, `observability_traces_push_url()`. On the STACKIT lane each MUST source from the corresponding foundation output via `stackit_foundation_output_value_or_default`; on the local lane each MUST return the respective OTEL-collector-local push path (`http://otel-collector.observability.svc.cluster.local:8889/api/v1/write` for metrics, `http://otel-collector.observability.svc.cluster.local:3500/loki/api/v1/push` for logs, `http://otel-collector.observability.svc.cluster.local:4317` for traces).
- FR-003 MUST add `observability_api_key()` helper to `scripts/lib/infra/observability.sh` returning the STACKIT credential password from `stackit_foundation_output_value_or_default "observability_credential_password" ""` on STACKIT lane, and empty string on local lane (in-cluster collector requires no auth).
- FR-004 MUST add `observability_reconcile_runtime_secret()` and `observability_delete_runtime_secret()` to `scripts/lib/infra/observability.sh`. `reconcile_runtime_secret()` MUST write a K8s Secret named `blueprint-observability-auth` in `$OBSERVABILITY_NAMESPACE` containing keys `username` (from `stackit_foundation_output_value_or_default "observability_credential_username"`) and `password` (from `stackit_foundation_output_value_or_default "observability_credential_password"`). `delete_runtime_secret()` MUST remove this Secret on destroy.
- FR-005 MUST update `scripts/bin/infra/observability_apply.sh` to call `observability_reconcile_runtime_secret()` after `optional_module_apply_foundation_contract "observability"` on the `foundation_contract` case (STACKIT lane only), and to write four additional state keys: `logs_endpoint=$(observability_logs_push_url)`, `metrics_endpoint=$(observability_metrics_push_url)`, `traces_endpoint=$(observability_traces_push_url)`, `api_key=$(observability_api_key)` in the `observability_runtime` state file for both lanes.
- FR-006 MUST update `scripts/bin/infra/observability_destroy.sh` to call `observability_delete_runtime_secret()` in the `foundation_reconcile_apply` case so the `blueprint-observability-auth` K8s Secret is removed on STACKIT destroy.
- FR-007 MUST create `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` containing an OpenTelemetry Collector configuration with: OTLP gRPC+HTTP receivers (ports 4317, 4318), batch processor, and three exporters — `prometheusremotewrite` targeting `${OBSERVABILITY_METRICS_PUSH_URL}` with BasicAuth from `${OBSERVABILITY_USERNAME}`/`${OBSERVABILITY_PASSWORD}`, `loki` targeting `${OBSERVABILITY_LOGS_PUSH_URL}` with BasicAuth, and `otlp/stackit` targeting `${OBSERVABILITY_TRACES_PUSH_URL}` with BasicAuth. The values MUST include `extraEnvFrom` referencing `blueprint-observability-auth` Secret so the collector pod receives credentials as env vars.
- FR-008 MUST update `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` to include an ArgoCD `Application` resource (in addition to the existing metadata `ConfigMap`) that deploys the `open-telemetry/opentelemetry-collector` Helm chart in the `observability` namespace using the STACKIT values file at `infra/cloud/stackit/helm/observability/otel-collector.values.yaml`. The Application MUST reference the platform AppProject and set `syncPolicy.automated.selfHeal: true`.
- FR-009 MUST update `scripts/bin/infra/observability_smoke.sh` to add non-empty checks for `logs_endpoint`, `metrics_endpoint`, `traces_endpoint`, and `api_key` keys in the `observability_runtime` state file on the STACKIT lane (guarded by `is_stackit_profile`).
- FR-010 MUST update `blueprint/modules/observability/module.contract.yaml` to add `OBSERVABILITY_LOGS_ENDPOINT`, `OBSERVABILITY_METRICS_ENDPOINT`, `OBSERVABILITY_TRACES_ENDPOINT`, `OBSERVABILITY_API_KEY` to `outputs.produced` and add `OBSERVABILITY_USERNAME` as an optional input used by the collector secret reconciliation.
- FR-011 MUST add `tests/infra/modules/observability/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope before creating the test file, so the pre-commit pyramid gate does not block the commit.
- FR-012 MUST implement `tests/infra/modules/observability/test_contract.py` with ≥ 15 assertions covering: state file structure for both lanes, new endpoint keys non-empty on STACKIT, `otel_endpoint` always resolving to the in-cluster collector DNS, `api_key` empty on local lane, smoke validation logic, ArgoCD manifest Application resource present in STACKIT env files, Secret reconciliation paths, and module contract YAML outputs alignment.
- FR-013 MUST update `docs/platform/modules/observability/README.md` to document: the dual-lane architecture (in-cluster OTEL collector on both lanes), STACKIT lane provisioning flow, new state keys, K8s Secret lifecycle, Helm values file path, and usage examples for consumers configuring `OTEL_EXPORTER_OTLP_ENDPOINT`.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST ensure the STACKIT credential password NEVER appears in any state file (`artifacts/infra/observability_runtime.env`), CI log, or non-sensitive artifact. The password MUST be delivered exclusively via the `blueprint-observability-auth` K8s Secret and injected into the otel-collector pod as an env var via `extraEnvFrom`. The `api_key` state key MUST remain empty string on local lane.
- NFR-OBS-001 MUST ensure `OTEL_EXPORTER_OTLP_ENDPOINT` resolves to `http://otel-collector.observability.svc.cluster.local:4317` on both local and STACKIT lanes, so consumer applications require no lane-specific branching in their OTEL configuration. All script output MUST be prefixed with `[observability]`.
- NFR-REL-001 MUST set `syncPolicy.automated.selfHeal: true` and `syncPolicy.automated.prune: true` on the STACKIT otel-collector ArgoCD Application so ArgoCD continuously reconciles the collector deployment and any drift is self-healed without manual intervention.
- NFR-OPS-001 MUST write `logs_endpoint`, `metrics_endpoint`, `traces_endpoint` to the runtime state file so operators can verify push target configuration and diagnose fan-out failures without manual STACKIT console access. These values are non-sensitive (push URLs contain no credential material).
- NFR-A11Y-001 N/A — no UI or frontend changes in this work item.

## Open Questions

All questions resolved. See PR #308 comment for Q-1 resolution record.

## Normative Option Decision

### Option Decision 1: OTEL collector deployment on STACKIT lane

- Option A: Deploy an in-cluster OTEL Collector on the STACKIT lane (ArgoCD Application) that receives OTLP from consumers and fans out to STACKIT Observability push URLs — identical `OTEL_EXPORTER_OTLP_ENDPOINT` contract on both lanes (selected).
- Option B: Expose STACKIT push URLs directly as `OBSERVABILITY_LOGS_ENDPOINT` etc.; consumers and agents push directly to STACKIT without an in-cluster collector — different endpoint contract per lane.
- Selected option: OPTION_A
- Rationale: Option A eliminates the dangling-endpoint bug (STACKIT lane currently writes the collector DNS but never deploys the collector), gives consumers an identical OTEL contract on both lanes (no lane-specific branching), follows the established agentic-graphrag architecture pattern, and is forward-compatible with spanmetrics connector and other collector features. Option B would break the single-collector abstraction and force lane-specific logic into every consumer.

### Option Decision 2: STACKIT endpoint URL sourcing (contingent on Q-1)

- Option A: Source push URLs from foundation TF outputs (`stackit_observability_instance.foundation[0].metrics_push_url` etc.) — preferred if attributes exist.
- Option B: Compute push URLs by convention from instance ID and region (URL pattern construction) — fallback if TF attributes are absent in v0.88.0.
- Selected option: OPTION_A
- Rationale: TF-sourced URLs are authoritative and immune to URL pattern drift. Q-1 verified against provider v0.88.0 source: `metrics_push_url`, `logs_push_url`, and `otlp_grpc_traces_url` all exist as computed attributes on `stackit_observability_instance`. No fallback needed. Decision recorded in PR #308 comment 2026-05-19.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/modules/observability/module.contract.yaml` — add `OBSERVABILITY_LOGS_ENDPOINT`, `OBSERVABILITY_METRICS_ENDPOINT`, `OBSERVABILITY_TRACES_ENDPOINT`, `OBSERVABILITY_API_KEY` to `outputs.produced`; add `OBSERVABILITY_USERNAME` to `optional_env`
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — existing make targets (`infra-observability-{plan,apply,deploy,smoke,destroy}`) unchanged in name; deploy now also applies ArgoCD Application resource on STACKIT lane
- Docs contract: `docs/platform/modules/observability/README.md` updated with dual-lane architecture, new state keys, Secret lifecycle

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 MUST verify that after `make infra-observability-apply` on STACKIT profile, `artifacts/infra/observability_runtime.env` contains non-empty values for `logs_endpoint`, `metrics_endpoint`, `traces_endpoint`, and an empty value for `api_key` that does NOT appear in the state file (secret delivery only via K8s Secret).
- AC-002 MUST verify that `OTEL_EXPORTER_OTLP_ENDPOINT` value in `observability_runtime.env` equals `http://otel-collector.observability.svc.cluster.local:4317` on both local and STACKIT profiles.
- AC-003 MUST verify that `make infra-observability-smoke` exits 0 on STACKIT profile after apply and deploy.
- AC-004 MUST verify that `blueprint-observability-auth` K8s Secret exists in `$OBSERVABILITY_NAMESPACE` on STACKIT profile after apply, containing `username` and `password` keys.
- AC-005 MUST verify that `infra/gitops/argocd/optional/dev/observability.yaml` contains an ArgoCD `Application` resource kind (not only a `ConfigMap`).
- AC-006 MUST verify that `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` declares `prometheusremotewrite`, `loki`, and `otlp` exporters in the pipeline configuration.
- AC-007 MUST verify that `test_contract.py` passes with ≥ 15 assertions and is registered in `test_pyramid_contract.json` under the `unit` scope.
- AC-008 MUST verify that the `blueprint-observability-auth` K8s Secret is removed after `make infra-observability-destroy` on STACKIT profile.
- AC-009 MUST verify that `observability_api_key()` returns empty string when `is_local_profile` is true.
- AC-010 MUST verify that `make infra-validate` exits 0 after all contract changes.
- AC-011 MUST verify that `docs/platform/modules/observability/README.md` documents the dual-lane architecture and the new output keys.

## Informative Notes (Non-Normative)
- Context: The local lane already deploys the OTEL collector via Helm in `observability_apply.sh` (crossplane_plus_helm case). The STACKIT lane gap was that the foundation TF provisions the STACKIT instance and credential but the collector was never deployed, leaving `OTEL_EXPORTER_OTLP_ENDPOINT` as a dangling DNS reference. This spec closes the gap by deploying the collector via ArgoCD on the STACKIT lane, with the collector configured to fan out to STACKIT push URLs.
- Tradeoffs: Option A (in-cluster collector) adds a Kubernetes workload on the STACKIT lane that consumes cluster resources. The alternative (direct push) would require consumers to handle credential injection and URL construction themselves, which defeats the purpose of the module abstraction.
- Clarifications: The `OBSERVABILITY_API_KEY` output in issue #248 maps to the STACKIT credential password, which is consumed by the otel-collector Secret — not directly by consumers. Consumer applications always use `OTEL_EXPORTER_OTLP_ENDPOINT` with no authentication (in-cluster, plain HTTP). The `OBSERVABILITY_API_KEY` state key is deliberately empty to avoid persisting credentials in the state file; it exists in the contract to document the signal that auth is provisioned.

## Explicit Exclusions
- Grafana k8s-monitoring Helm chart deployment on STACKIT lane — STACKIT Observability provides managed Grafana; no in-cluster Grafana is deployed on stackit-* profiles.
- Faro browser telemetry endpoint — deferred; no active consumer need for frontend RUM on STACKIT lane at this time.
- spanmetrics connector configuration — out of scope for initial implementation; surfaces from backlog when a consumer requires auto-derived span metrics.
- Loki/Prometheus/Tempo standalone installation on STACKIT lane — STACKIT Observability provides managed equivalents; no self-hosted backends needed.
- OBSERVABILITY_RETENTION_DAYS shell contract implementation — retention is configured at the Terraform level via `observability_logs_retention_days` / `metrics_retention_days` / `traces_retention_days` foundation variables, not at the shell wrapper level.
