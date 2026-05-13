# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two static YAML keys + two test method additions. No abstractions, no new functions, no new files beyond what AC requires.
- Anti-abstraction gate: Direct YAML edits; no wrapper layers or helper functions introduced.
- Integration-first testing gate: Tests parse the seed values file directly via `yaml.safe_load`; no mocking or infrastructure required.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in scope.
- Finding-to-test translation gate: Both bugs are reproducible (helm pre-install failure, init-container ImagePullBackOff). Slice 1 MUST write failing assertions before adding the YAML keys; Slice 2 turns them green.

## Delivery Slices

### Slice 1 — RED: failing test assertions
Write two failing test methods in `OpenSearchLocalHelmChartTests` in `tests/infra/modules/opensearch/test_opensearch_module.py`:

1. `test_opensearch_seed_values_allow_insecure_images`:
   - Parse `_SEED_VALUES` via `yaml.safe_load`.
   - Assert `parsed.get("global", {}).get("security", {}).get("allowInsecureImages") is True`.
   - Expected result: FAIL (key absent in seed file).

2. `test_opensearch_seed_values_sysctl_image_disabled`:
   - Parse `_SEED_VALUES` via `yaml.safe_load`.
   - Assert `parsed.get("sysctlImage", {}).get("enabled") is False`.
   - Expected result: FAIL (key absent in seed file).

Run `uv run python3 -m pytest tests/infra/modules/opensearch/test_opensearch_module.py -v` — confirms 2 new failures, all pre-existing tests still green.

### Slice 2 — GREEN: add YAML keys to all three files
Add both keys to:
- `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`
- `infra/local/helm/opensearch/values.yaml`
- `artifacts/infra/rendered/opensearch.values.yaml`

Both keys are static YAML at the top level:
```yaml
global:
  security:
    allowInsecureImages: true
sysctlImage:
  enabled: false
```

Run `uv run python3 -m pytest tests/infra/modules/opensearch/test_opensearch_module.py -v` — confirms all tests green.
Run `make quality-hooks-fast` and `make infra-validate` — confirm no regressions.

## Change Strategy
- Migration/rollout sequence: template fix propagates to new consumers at bootstrap; existing consumers receive the fix at next blueprint upgrade.
- Backward compatibility policy: additive; existing helm values structure is preserved, two keys are appended.
- Rollback plan: remove both keys from the three YAML files; the state is identical to pre-fix (which was already broken on chart 1.6.x).

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/modules/opensearch/test_opensearch_module.py -v` — 2 new assertions + all pre-existing assertions green.
- Contract checks: `make infra-validate` — confirms template and seed file structure against contract.
- Integration checks: none required — change is static YAML; no runtime integration paths affected.
- E2E checks: not in scope for this work item; `infra-opensearch-apply` live test requires a running Kubernetes cluster.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: no Make-target contract changes; no app delivery workflow scope; all listed targets are pre-existing and unaffected by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: review `docs/platform/modules/opensearch/README.md` for a chart version compatibility note; add if absent.
- Consumer docs updates: review `scripts/templates/blueprint/bootstrap/docs/platform/modules/opensearch/README.md` for the same note; add if absent.
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route or filter scope.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: none — no script paths change.
- Alerts/ownership: none.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1: `sysctlImage.enabled: false` skips host sysctl tuning → mitigation: acceptable for local single-node dev cluster with persistence disabled; STACKIT managed service is unaffected.
- Risk 2: `global.security.allowInsecureImages: true` present for consumers using a trusted-registry image override → mitigation: flag is harmless when no `bitnamilegacy/` image is present; does not weaken security for trusted-registry images.
