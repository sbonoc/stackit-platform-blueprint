# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Dangling OTEL endpoint on STACKIT lane — `observability_apply.sh` wrote `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc.cluster.local:4317` to the runtime state file, but the otel-collector was never deployed on STACKIT. Fixed by deploying the collector via ArgoCD (FR-008, FR-007) and writing correct push-URL state keys (FR-005).
- Finding 2: Foundation TF outputs missing for observability push URLs — `infra/cloud/stackit/terraform/foundation/outputs.tf` and its bootstrap template copy did not expose `observability_metrics_push_url`, `observability_logs_push_url`, or `observability_traces_push_url`. Added and conditioned on `var.observability_enabled` (FR-001).
- Finding 3: Bootstrap template README out of sync — `scripts/templates/blueprint/bootstrap/docs/platform/modules/observability/README.md` diverged from the live README after T-016 changes. Fixed by running `sync_module_contract_summaries.py` and committing the result separately (commit 0a75438).

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: OTEL Collector Helm values (`infra/cloud/stackit/helm/observability/otel-collector.values.yaml`) configure three signal exporters — `prometheusremotewrite` (metrics), `loki` (logs), `otlp/stackit` (traces) — each using BasicAuth from env vars injected via `extraEnvFrom: blueprint-observability-auth`. Signal pipelines are explicit and non-overlapping. Health check extension exposed on port 13133 for K8s readiness probes.
- Operational diagnostics updates: `observability_runtime.env` now includes `logs_endpoint`, `metrics_endpoint`, `traces_endpoint` (push URLs, non-sensitive) so operators can verify fan-out targets without STACKIT console access (NFR-OPS-001). `observability_smoke.sh` validates all three endpoints are non-empty on STACKIT lane (FR-009). `observability_smoke.env` is written with `status=passed` after a successful smoke run.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Single Responsibility — each new shell function has one purpose; `observability_reconcile_runtime_secret()` delegates to `apply_optional_module_secret_from_literals`; `observability_delete_runtime_secret()` delegates to `delete_optional_module_secret`. Open/Closed — the Secret pattern from kms/object-storage/identity-aware-proxy is reused without modification; no new patterns introduced. Credential isolation — password is passed only through `blueprint-observability-auth` K8s Secret via `extraEnvFrom`; it never appears in state files, CI logs, or git-tracked artifacts (NFR-SEC-001). Feature-flag guard implemented at three independent layers: `observability_apply.sh` early exit, TF conditional outputs, `optional/` GitOps path prefix.
- Test-automation and pyramid checks: `test_contract.py` registered in `test_pyramid_contract.json` before test code was committed (T-001 → T-002 ordering), satisfying the pyramid pre-commit gate. 42 assertions across 8 test classes covering state file structure (both lanes), endpoint keys non-empty on STACKIT, `otel_endpoint` DNS constant, `api_key` empty on local, smoke script content, ArgoCD Application presence, Secret reconciliation paths, module contract YAML outputs. 1061 tests pass in `make test-unit-all`.
- Documentation/diagram/CI/skill consistency checks: `architecture.md` flowchart and sequence diagram updated to reflect Secret-only push URL injection (no ConfigMap). `module.contract.yaml` `paths.helm` includes the new STACKIT values file; `outputs.produced` and `optional_env` match what `observability_apply.sh` writes and what `test_contract.py` asserts. `make infra-validate` exit 0 — contract.yaml and makefile consistent. `make docs-build && make docs-smoke` exit 0 — README renders without errors.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI or frontend changes in this work item (NFR-A11Y-001)
- [x] SC 2.1.1 (Keyboard): N/A — no UI or frontend changes
- [x] SC 2.4.7 (Focus Visible): N/A — no UI or frontend changes
- [x] SC 1.4.1 (Use of Color): N/A — no UI or frontend changes
- [x] SC 3.3.1 (Error Identification): N/A — no UI or frontend changes
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI or frontend changes

## Proposals Only (Not Implemented)
- Proposal 1: spanmetrics connector in otel-collector values — add a `spanmetrics` connector so span-derived metrics (request rates, error rates, latency percentiles) are auto-derived from traces and forwarded to the Prometheus remote-write endpoint. Out of scope for initial implementation; surfaces when a consumer requests auto-derived span metrics. Follow-up: file backlog item under issue-248.
- Proposal 2: Faro browser telemetry endpoint on STACKIT lane — expose a Faro/GrafanaAgent receiver in the STACKIT otel-collector for browser RUM telemetry. Deferred — no active consumer need; requires evaluating OTC Faro receiver maturity and STACKIT Observability push protocol support.
- Proposal 3: `OBSERVABILITY_RETENTION_DAYS` shell contract — surface TF-level retention vars as a shell-layer contract variable. Low effort; deferred to avoid scope creep in this PR.
- Proposal 4: `blueprint-template-smoke` declare -A fix — pre-existing `declare -A` (associative arrays) failure on macOS `/bin/sh` in `prune_codex_skills.sh`. Pre-existing defect confirmed on `main` before this branch; out of scope for this PR; repo-wide cleanup item.
