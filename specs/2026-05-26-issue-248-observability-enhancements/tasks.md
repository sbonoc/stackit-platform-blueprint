# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm ADR status is `approved` in `spec.md`

## Slice 1 — Faro receiver shell lib + contract + state + smoke

- [x] T-101 Add `observability_faro_endpoint()` to `scripts/lib/infra/observability.sh` (FR-001)
- [x] T-102 Export `FARO_ENDPOINT` from `observability_init_env()` via `set_default_env` (FR-002)
- [x] T-103 Add `FARO_ENDPOINT` to `blueprint/modules/observability/module.contract.yaml` outputs.produced (FR-006)
- [x] T-104 Add `FARO_CORS_ALLOWED_ORIGINS` and `OBSERVABILITY_DASHBOARDS_NAME` to contract optional_env (FR-006, FR-017)
- [x] T-105 Write `faro_endpoint` state key in `observability_apply.sh` on both lanes (FR-007)
- [x] T-106 Add `faro_endpoint` smoke validation in `observability_smoke.sh` (FR-008)
- [x] T-107 Add ≥4 Slice 1 test assertions (faro_endpoint function, FARO_ENDPOINT in contract, faro_endpoint state key in mock, smoke validation present) (FR-018)

## Slice 2 — OTEL pipeline improvements (values files + ArgoCD manifests)

- [x] T-201 Add Faro receiver + port to `infra/local/helm/observability/otel-collector.values.yaml` (FR-003)
- [x] T-202 Add Faro receiver + port to `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` (FR-004)
- [x] T-203 Update `infra/gitops/argocd/optional/dev/observability.yaml` — Faro receiver, port, memory_limiter, filter, faro in pipelines (FR-005, FR-009, FR-010)
- [x] T-204 Update `infra/gitops/argocd/optional/stage/observability.yaml` — same changes (FR-005, FR-009, FR-010)
- [x] T-205 Update `infra/gitops/argocd/optional/prod/observability.yaml` — same changes (FR-005, FR-009, FR-010)
- [x] T-206 Add `memory_limiter` processor to local and STACKIT values files (FR-009)
- [x] T-207 Add `filter/drop-healthcheck-spans` processor to local and STACKIT values files (FR-010)
- [x] T-208 Add `spanmetrics` connector to local values file (FR-011)
- [x] T-209 Add ≥5 Slice 2 test assertions (Faro port in local, STACKIT, dev/stage/prod ArgoCD; memory_limiter in local and STACKIT; filter in local and STACKIT; spanmetrics in local) (FR-018)

## Slice 3 — Dashboard provisioning

- [x] T-301 Create `infra/observability/dashboards/golden-signals.json` seed dashboard (FR-012)
- [x] T-302 Create `scripts/bin/infra/observability_dashboards_apply.sh` (FR-013)
- [x] T-303 Create `scripts/bin/infra/observability_dashboards_destroy.sh` (FR-014)
- [x] T-304 Add `infra-observability-dashboards-apply` and `infra-observability-dashboards-destroy` make targets to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and PHONY list (FR-015)
- [x] T-305 Regenerate `make/blueprint.generated.mk` from template (`make blueprint-render-makefile`) (FR-015)
- [x] T-306 Mirror seed dashboard to `scripts/templates/blueprint/bootstrap/infra/observability/dashboards/` (FR-016)
- [x] T-307 Add ≥3 Slice 3 test assertions (dashboard apply target in Makefile template, seed dashboard file exists, OBSERVABILITY_DASHBOARDS_NAME in contract) (FR-018)

## Slice 4 — Documentation + quality gates

- [x] T-401 Update `docs/platform/modules/observability/README.md` with Faro endpoint, dashboard provisioning, OTEL improvements, updated state table and make targets (FR-019)
- [x] T-402 Verify `make quality-hooks-fast` passes with no regressions (AC-013) — only quality-spec-pr-ready fails (expected: publish phase not yet done)
- [x] T-403 Verify `make quality-validate-bootstrap-template-drift` passes (FR-016 check)
- [x] T-404 Run `python3 scripts/bin/quality/render_core_targets_doc.py` to regenerate `docs/reference/generated/core_targets.generated.md` (FR-015 side-effect)
- [x] T-405 Confirm `python3 -m pytest tests/infra/modules/observability/ -x -q` passes with ≥12 new assertions (AC-012) — 77 total, 21 new

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling/infrastructure-only change, no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling/infrastructure-only change
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling/infrastructure-only change

## Publish Phase

- [ ] T-501 Populate `pr_context.md` with validation evidence and reviewed file list
- [ ] T-502 Populate `evidence_manifest.json` (make spec-evidence-manifest SPEC_DIR=...)
- [ ] T-503 Populate `hardening_review.md` with security and operational review
- [ ] T-504 Mark PR ready for review (remove Draft status)
