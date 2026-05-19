# PR Context

## Summary
- Work item: issue-248-observability-module (observability, 9th of 11 modules from issue #248)
- Objective: Fix the dangling OTEL endpoint defect on the STACKIT lane — deploy an in-cluster OTEL Collector via ArgoCD so consumers use the same `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc.cluster.local:4317` on both local and STACKIT lanes. Extend foundation TF outputs with push URLs; reconcile `blueprint-observability-auth` K8s Secret; configure collector to fan out signals to STACKIT Observability managed backends.
- Scope boundaries: Shell layer (`observability.sh`, `observability_apply.sh`, `observability_destroy.sh`, `observability_smoke.sh`); foundation TF output extension + bootstrap template sync; STACKIT otel-collector Helm values; ArgoCD Application manifests for dev/stage/prod; module contract; unit tests; README. Out of scope: Grafana k8s-monitoring on STACKIT, Faro, spanmetrics connector, retention policy shell contract, standalone Loki/Prometheus/Tempo.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011
- Contract surfaces changed: `blueprint/modules/observability/module.contract.yaml` — added 4 outputs (`OBSERVABILITY_LOGS_ENDPOINT`, `OBSERVABILITY_METRICS_ENDPOINT`, `OBSERVABILITY_TRACES_ENDPOINT`, `OBSERVABILITY_API_KEY`) and 1 optional env (`OBSERVABILITY_USERNAME`); `infra/cloud/stackit/terraform/foundation/outputs.tf` — added 3 push-URL outputs; `artifacts/infra/observability_runtime.env` — 4 new state keys; `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` — ArgoCD Application added to existing ConfigMap files

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/observability.sh` — new helper functions: push URL accessors, `observability_reconcile_runtime_secret`, `observability_delete_runtime_secret`, `observability_api_key`, `observability_secret_name`
  - `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` — STACKIT otel-collector Helm values: receivers, batch processor, BasicAuth extension, three exporters (prometheusremotewrite, loki, otlp/stackit), `extraEnvFrom: blueprint-observability-auth`
  - `infra/gitops/argocd/optional/dev/observability.yaml` — ArgoCD Application added (same pattern applied to stage and prod)
  - `infra/cloud/stackit/terraform/foundation/outputs.tf` — three new push-URL outputs (and bootstrap template copy)
  - `tests/infra/modules/observability/test_contract.py` — 42 assertions across 8 test classes
- High-risk files:
  - `scripts/bin/infra/observability_apply.sh` — `observability_reconcile_runtime_secret` call order and new state keys (regression risk to existing `otel_endpoint` / `otel_protocol` keys)
  - `scripts/bin/infra/observability_destroy.sh` — `observability_delete_runtime_secret` must run before foundation TF destroy; ordering is safety-critical
  - `scripts/lib/infra/observability.sh` lines 61–74 — Secret reconciliation via `apply_optional_module_secret_from_literals` / `delete_optional_module_secret` pattern (same as kms, object-storage)

## Validation Evidence
- Required commands executed: `make test-unit-all`, `make infra-validate`, `make quality-hooks-run`, `make docs-build && make docs-smoke`, `make quality-hardening-review`
- Result summary: All gates green. 1061 tests pass (42 new observability assertions; 1019 pre-existing). `make infra-validate` exit 0. `make docs-build && make docs-smoke` exit 0. `make quality-hardening-review` exit 0. `make quality-hooks-run` passes all checks; `blueprint-template-smoke` failure is a pre-existing defect (declare -A associative arrays in `prune_codex_skills.sh` not supported by macOS `/bin/sh`), confirmed present on stash before this branch.
- Artifact references: `artifacts/infra/observability_runtime.env` (state file), `artifacts/docs/docs_build.env`, `artifacts/docs/docs_smoke.env`, `specs/2026-05-18-issue-248-observability-module/evidence_manifest.json`

## Risk and Rollback
- Main risks: (1) `stackit_observability_instance` TF attribute names — verified against provider v0.88.0 source (`metrics_push_url`, `logs_push_url`, `otlp_grpc_traces_url` confirmed); no fallback needed. (2) ArgoCD Application inline values may drift from local otel-collector values over time — mitigated by `selfHeal: true` and the single authoritative values file at `infra/cloud/stackit/helm/observability/otel-collector.values.yaml`. (3) `blueprint-observability-auth` Secret must be deleted before foundation TF destroy; if destroy fails mid-way, Secret may remain — operator must run `kubectl delete secret blueprint-observability-auth -n observability` manually before retrying.
- Rollback strategy: Set `OBSERVABILITY_ENABLED=false` in profile; ArgoCD will not apply the Application on re-sync; run `make infra-observability-destroy` to remove the STACKIT instance, credential, and K8s Secret. No data loss — STACKIT Observability data retention is managed at the STACKIT Observability console level independently of this module.

## Deferred Proposals
- Proposal A (not implemented): spanmetrics connector in otel-collector values — auto-derive span metrics from traces; deferred until a consumer requests it.
- Proposal B (not implemented): Faro browser telemetry endpoint on STACKIT lane — no active consumer need; requires evaluating OTC Faro receiver maturity and STACKIT Observability push protocol support.
- Proposal C (not implemented): `OBSERVABILITY_RETENTION_DAYS` shell contract — surface TF-level retention vars as a shell-layer contract variable; low effort, deferred to avoid scope creep.
- Proposal D (not implemented): `blueprint-template-smoke` declare -A fix — pre-existing defect on macOS `/bin/sh`; out of scope for this PR; repo-wide cleanup item.
