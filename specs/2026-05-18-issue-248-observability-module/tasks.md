# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0` (Q-1 must be resolved)
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1 (red: failing tests)
- [x] T-001 Add `tests/infra/modules/observability/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope
- [x] T-002 Write `tests/infra/modules/observability/test_contract.py` with ≥ 15 failing assertions

## Implementation — Slice 2 (green: foundation TF + shell helpers)
- [x] T-003 Verify Q-1: confirm exact `stackit_observability_instance` push URL attribute names in provider v0.88.0 via `terraform providers schema -json`
- [x] T-004 Extend `infra/cloud/stackit/terraform/foundation/outputs.tf` with `observability_metrics_push_url`, `observability_logs_push_url`, `observability_traces_push_url`
- [x] T-005 Sync bootstrap template copy `scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/outputs.tf` with same additions
- [x] T-006 Add `observability_metrics_push_url()`, `observability_logs_push_url()`, `observability_traces_push_url()`, `observability_api_key()` to `scripts/lib/infra/observability.sh`
- [x] T-007 Add `observability_reconcile_runtime_secret()` and `observability_delete_runtime_secret()` to `scripts/lib/infra/observability.sh`

## Implementation — Slice 3 (green: STACKIT otel-collector + ArgoCD)
- [ ] T-008 Create `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` with OTLP receiver, batch processor, `prometheusremotewrite` + `loki` + `otlp/stackit` exporters, and `extraEnvFrom` referencing `blueprint-observability-auth` Secret
- [ ] T-009 Update `infra/gitops/argocd/optional/dev/observability.yaml` to add ArgoCD `Application` resource for otel-collector
- [ ] T-010 Update `infra/gitops/argocd/optional/stage/observability.yaml` to add ArgoCD `Application` resource for otel-collector
- [ ] T-011 Update `infra/gitops/argocd/optional/prod/observability.yaml` to add ArgoCD `Application` resource for otel-collector

## Implementation — Slice 4 (green: shell scripts + contract)
- [ ] T-012 Update `scripts/bin/infra/observability_apply.sh`: add `observability_reconcile_runtime_secret` call in `foundation_contract` case and add four new state keys (`logs_endpoint`, `metrics_endpoint`, `traces_endpoint`, `api_key`) to `write_state_file`
- [ ] T-013 Update `scripts/bin/infra/observability_destroy.sh`: add `observability_delete_runtime_secret` call in `foundation_reconcile_apply` case
- [ ] T-014 Update `scripts/bin/infra/observability_smoke.sh`: add non-empty checks for `logs_endpoint`, `metrics_endpoint`, `traces_endpoint` on STACKIT profile
- [ ] T-015 Update `blueprint/modules/observability/module.contract.yaml`: add `OBSERVABILITY_LOGS_ENDPOINT`, `OBSERVABILITY_METRICS_ENDPOINT`, `OBSERVABILITY_TRACES_ENDPOINT`, `OBSERVABILITY_API_KEY` to `outputs.produced`; add `OBSERVABILITY_USERNAME` to `optional_env`

## Implementation — Slice 5 (docs + validation)
- [ ] T-016 Update `docs/platform/modules/observability/README.md` with dual-lane architecture, new outputs, K8s Secret lifecycle, otel-collector values path, consumer usage example
- [ ] T-017 Run `make infra-validate` and confirm exit 0
- [ ] T-018 Run `make quality-hooks-run` and confirm exit 0

## Test Automation
- [ ] T-101 Confirm `test_contract.py` has ≥ 15 passing assertions after Slice 4
- [ ] T-102 Confirm all existing module tests still pass (`make test-unit-all`)
- [ ] T-103 N/A — no filter/payload-transform logic
- [ ] T-104 Translate Q-1 resolution finding into a deterministic test assertion (foundation outputs.tf content check)
- [ ] T-105 N/A — no boundary/integration tests required; state file contract is fully covered at unit level

## Accessibility Testing
- [ ] T-A01 NFR-A11Y-001: N/A — no UI or frontend changes in this work item

## Validation and Release Readiness
- [ ] T-201 Run `make test-unit-all` (all tests green including new `test_contract.py`)
- [ ] T-202 Run `make infra-validate` (contract + make target consistency)
- [ ] T-203 Run `make quality-hooks-run` (full pre-push gate)
- [ ] T-204 Run `make docs-build && make docs-smoke`
- [ ] T-205 Run `make quality-hardening-review`

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage (FR-001–FR-013, AC-001–AC-011), key reviewer files, validation evidence, risk/rollback notes
- [ ] P-003 Ensure PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling/infrastructure-only change, no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling/infrastructure-only change
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling/infrastructure-only change
