# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two YAML files each gain one key (`configs.cm.resource.customizations.ignoreResourceUpdates.all: ""`). One new pytest file. No abstractions introduced.
- Anti-abstraction gate: Direct YAML override; no wrapper scripts or helper code.
- Integration-first testing gate: Regression tests verify the YAML override is present in both files. No live cluster required.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: The reproducible health=N/A finding is translated into AC-001/AC-002/AC-003 tests that fail without the fix and pass with it.

## Delivery Slices

### Slice 1 — Regression tests (red) + YAML fix + chart bump (green)

Write failing regression tests for AC-001, AC-002, and AC-003, then apply the YAML override and chart pin bump to turn them green.

**Files touched:**
- `tests/infra/test_argocd_values_health_fix.py` (new)
- `infra/local/helm/core/argocd.values.yaml`
- `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`
- `scripts/lib/infra/versions.sh`
- `scripts/lib/infra/versions.baseline.sh`

**Steps (red → green):**
1. Write `test_argocd_values_health_fix.py` with three test cases:
   - `test_argocd_values_ignoreResourceUpdates_all_is_empty`: reads `infra/local/helm/core/argocd.values.yaml`, asserts `configs.cm["resource.customizations.ignoreResourceUpdates.all"] == ""`
   - `test_argocd_template_ignoreResourceUpdates_all_is_empty`: reads `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`, asserts the same.
   - `test_argocd_chart_version_is_9_5_13`: reads `scripts/lib/infra/versions.sh`, asserts `ARGOCD_CHART_VERSION="9.5.13"` is present.
2. Confirm all three tests fail.
3. Add `configs.cm` block to `infra/local/helm/core/argocd.values.yaml`:
   ```yaml
   configs:
     cm:
       # Override argo-cd chart default: the all-resource /status ignoreResourceUpdates
       # suppresses health evaluation events in ArgoCD v3.x (issue #277).
       resource.customizations.ignoreResourceUpdates.all: ""
   ```
4. Apply the identical change to `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`.
5. Bump `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13` in `scripts/lib/infra/versions.sh`.
6. Bump `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13` in `scripts/lib/infra/versions.baseline.sh`.
7. Confirm all three tests pass.
8. Run `make infra-contract-test-fast` to verify no existing contract tests regress.

## Change Strategy
- Migration/rollout sequence: `make infra-deploy` on the next local install re-runs `helm upgrade --install` with the updated values, which regenerates `argocd-cm`. No manual steps required.
- Backward compatibility policy: The override is additive to the existing values file. Existing consumers receive the fix on the next blueprint upgrade (FR-002). No breaking change.
- Rollback plan: Remove the `configs.cm` block from `argocd.values.yaml` and re-run `make infra-deploy`. No state migration.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/test_argocd_values_health_fix.py -v` (AC-001, AC-002, AC-003, AC-004)
- Contract checks: `make infra-contract-test-fast`
- Integration checks: N/A — no running services touched by unit-testable code paths.
- E2E checks: Manual smoke on Docker Desktop (AC-005): after `make infra-deploy`, run `argocd app get platform-local-core` and confirm `Health: Healthy`. Not automated in CI (no live-cluster lane).

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
- Notes: No app onboarding make targets or port-forward wrappers are modified by this work item. All targets above remain unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — the YAML comment in `argocd.values.yaml` is the canonical explanation.
- Consumer docs updates: none.
- Mermaid diagrams updated: architecture.md diagram is the only diagram; no docs/ Mermaid pages.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP routes or API endpoints changed.
- Publish checklist:
  - Requirement coverage: FR-001, FR-002 → YAML files; AC-001–AC-003 → pytest; AC-004 → manual evidence
  - Key reviewer files: `infra/local/helm/core/argocd.values.yaml`, `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`, `tests/infra/test_argocd_values_health_fix.py`
  - Validation evidence: pytest output + (manual) argocd CLI output
  - Rollback notes: remove `configs.cm` block + `make infra-deploy`

## Operational Readiness
- Logging/metrics/traces: ArgoCD health status becomes meaningful after deploy; no new metrics/logs added.
- Alerts/ownership: ArgoCD health-based alerting can be adopted once health is correct (out of scope for this work item).
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1: Setting `ignoreResourceUpdates.all: ""` may produce unexpected behavior if the Helm chart renders an empty string as a non-empty YAML value. Mitigation: regression test verifies the YAML is parsed as empty string; ArgoCD interprets an empty value as "no ignoreResourceUpdates rules for all resources."
