# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Follow the established secrets-manager and dns module patterns exactly; no new abstraction layers. Reuse `apply_optional_module_secret_from_literals` and `delete_optional_module_secret` for the Secret lifecycle.
- Anti-abstraction gate: Helper functions in `observability.sh` are thin delegators to `stackit_foundation_output_value_or_default`; no intermediate caching or wrapping.
- Integration-first testing gate: Unit tests in `test_contract.py` cover state file structure, helper function logic (via subprocess mocking), and ArgoCD manifest content before implementation code is written (red → green TDD order).
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in this work item.
- Finding-to-test translation gate: Q-1 TF attribute verification result MUST be captured as a unit test assertion against the foundation outputs.tf content before any implementation begins.

## Delivery Slices

### Slice 1 — Red: failing tests for new state keys and foundation outputs
1. Add `tests/infra/modules/observability/test_contract.py` entry to `scripts/lib/quality/test_pyramid_contract.json`.
2. Write `test_contract.py` with failing assertions for: `logs_endpoint`, `metrics_endpoint`, `traces_endpoint`, `api_key` present in state file structure; `observability_metrics_push_url()`, `observability_logs_push_url()`, `observability_traces_push_url()`, `observability_api_key()` functions exist in `observability.sh`; foundation `outputs.tf` contains `observability_metrics_push_url` output; ArgoCD manifest files for dev/stage/prod contain an `Application` kind; `blueprint-observability-auth` Secret reconciliation functions exist in `observability.sh`.
3. Run `uv run python3 -m pytest tests/infra/modules/observability/test_contract.py` — expect failures (red).

### Slice 2 — Green: foundation TF outputs + shell helpers
Q-1 resolved (Step 02, 2026-05-19): `metrics_push_url`, `logs_push_url`, `otlp_grpc_traces_url` confirmed as computed attributes on `stackit_observability_instance` in provider v0.88.0. No URL-construction fallback required.
1. Extend `infra/cloud/stackit/terraform/foundation/outputs.tf` with `observability_metrics_push_url`, `observability_logs_push_url`, `observability_traces_push_url` outputs sourced from `stackit_observability_instance.foundation[0].metrics_push_url`, `.logs_push_url`, `.otlp_grpc_traces_url` respectively, conditional on `var.observability_enabled`.
2. Sync bootstrap template copy `scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/outputs.tf` with the same additions.
3. Add `observability_metrics_push_url()`, `observability_logs_push_url()`, `observability_traces_push_url()`, `observability_api_key()`, `observability_reconcile_runtime_secret()`, `observability_delete_runtime_secret()` to `scripts/lib/infra/observability.sh`. Use `apply_optional_module_secret_from_literals` / `delete_optional_module_secret` from `fallback_runtime.sh` for Secret lifecycle (same pattern as kms, object-storage, identity-aware-proxy modules).
4. Run `uv run python3 -m pytest tests/infra/modules/observability/test_contract.py` — expect partial green (foundation + helper assertions pass; ArgoCD manifest assertions still red).
5. Run `make test-unit-all` — all existing tests must remain green.

### Slice 3 — Green: STACKIT otel-collector values file + ArgoCD manifests
1. Create `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` with OTLP receiver, batch processor, three exporters (`prometheusremotewrite`, `loki`, `otlp/stackit`), and spanmetrics connector. Use `extraVolumes`/`extraVolumeMounts` to mount `blueprint-observability-auth` Secret at `/etc/otel/secrets` (read-only); reference credentials and push URLs via the OTC file config provider (`${file:/etc/otel/secrets/<key>}`).
2. Update `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` to add an ArgoCD `Application` resource deploying the `open-telemetry/opentelemetry-collector` chart from `open-telemetry` Helm registry, using the STACKIT values file path, targeting the `observability` namespace.
3. Run `uv run python3 -m pytest tests/infra/modules/observability/test_contract.py` — expect all ArgoCD manifest assertions green.

### Slice 4 — Green: shell script updates + state file + smoke hardening
1. Update `scripts/bin/infra/observability_apply.sh`:
   - In `foundation_contract` case: add `observability_reconcile_runtime_secret` call after `optional_module_apply_foundation_contract`.
   - In `write_state_file "observability_runtime"`: add `logs_endpoint=$(observability_logs_push_url)`, `metrics_endpoint=$(observability_metrics_push_url)`, `traces_endpoint=$(observability_traces_push_url)`, `api_key=$(observability_api_key)` for both lanes.
2. Update `scripts/bin/infra/observability_destroy.sh`: add `observability_delete_runtime_secret` call in `foundation_reconcile_apply` case.
3. Update `scripts/bin/infra/observability_smoke.sh`: add STACKIT-lane checks for `logs_endpoint`, `metrics_endpoint`, `traces_endpoint` non-empty; `api_key` presence (may be empty on local).
4. Update `blueprint/modules/observability/module.contract.yaml`: add new outputs and optional env.
5. Run `uv run python3 -m pytest tests/infra/modules/observability/test_contract.py` — all ≥ 15 assertions green.
6. Run `make test-unit-all` — full suite green.
7. Run `make quality-hooks-fast`.

### Slice 5 — Docs + template sync
1. Update `docs/platform/modules/observability/README.md` with dual-lane architecture, new outputs, K8s Secret lifecycle, otel-collector values path, consumer usage example.
2. Run `make infra-validate` and `make quality-hooks-run`.

## Change Strategy
- Migration/rollout sequence: Foundation TF outputs → shell helpers → otel-collector values → ArgoCD manifests → shell script updates → contract update → tests → docs.
- Backward compatibility policy: Existing state file keys (`otel_endpoint`, `otel_protocol`, etc.) are preserved. New keys are additive. Local lane smoke is unchanged (no STACKIT-specific assertions on local). ArgoCD manifest additions are additive (ConfigMap preserved, Application added).
- Rollback plan: Revert `outputs.tf` additions, `observability.sh` additions, and ArgoCD manifest Application block. The foundation TF instance/credential resources are unaffected by this change.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/modules/observability/test_contract.py` after each slice — run at lowest pyramid level.
- Contract checks: `make infra-validate` (validates module.contract.yaml + make target consistency).
- Integration checks: `make quality-hooks-fast` (aggregated hooks including infra-contract-test-fast).
- E2E checks: N/A — no HTTP route changes; smoke validation covers the observability state file contract.

## App Onboarding Contract (Normative)
- App onboarding impact: no-impact
- Notes: Consumers continue to use `OTEL_EXPORTER_OTLP_ENDPOINT` with no change. The otel-collector is a platform-layer workload, invisible to consumer app onboarding Make targets.
- Required minimum make targets (all N/A — tooling-only scope):
  - `apps-bootstrap` — N/A
  - `apps-smoke` — N/A
  - `backend-test-unit` — N/A
  - `backend-test-integration` — N/A
  - `backend-test-contracts` — N/A
  - `backend-test-e2e` — N/A
  - `touchpoints-test-unit` — N/A
  - `touchpoints-test-integration` — N/A
  - `touchpoints-test-contracts` — N/A
  - `touchpoints-test-e2e` — N/A
  - `test-unit-all` — N/A
  - `test-integration-all` — N/A
  - `test-contracts-all` — N/A
  - `test-e2e-all-local` — N/A
  - `infra-port-forward-start` — N/A
  - `infra-port-forward-stop` — N/A
  - `infra-port-forward-cleanup` — N/A

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — no blueprint-track architecture changes.
- Consumer docs updates: `docs/platform/modules/observability/README.md` — dual-lane architecture, new outputs, K8s Secret, otel-collector values.
- Mermaid diagrams updated: architecture.md already contains flowchart TD and sequenceDiagram; README update may include a simplified version.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route changes in this work item.
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-013, AC-001–AC-011)
  - include key reviewer files (outputs.tf, observability.sh, otel-collector.values.yaml, dev/observability.yaml, test_contract.py)
  - include validation evidence (test count, infra-validate pass, quality-hooks-run pass)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: otel-collector health endpoint (port 13133) monitored by K8s readiness probe. Smoke check validates state file keys. Full signal-delivery verification (data arriving at STACKIT) is manual operator responsibility via STACKIT Observability console.
- Alerts/ownership: otel-collector pod health is monitored by ArgoCD (selfHeal). ArgoCD application health failures surface in the ArgoCD UI.
- Runbook updates: `docs/platform/modules/observability/README.md` updated with troubleshooting section for push URL misconfiguration and credential Secret verification.

## Risks and Mitigations
- Risk 1 (Q-1 TF attribute names) → Resolved (2026-05-19, PR #308): `metrics_push_url`, `logs_push_url`, `otlp_grpc_traces_url` confirmed in provider v0.88.0. No fallback needed.
- Risk 2 (env var substitution in otel-collector values) → Mitigation: Use standard OTC `${ENV_VAR}` substitution syntax supported by the chart's `config` block; test locally with the existing local lane first.
- Risk 3 (ArgoCD AppProject reference) → Mitigation: Use the same AppProject referenced in the `public-endpoints` ArgoCD Application manifest as the pattern.
