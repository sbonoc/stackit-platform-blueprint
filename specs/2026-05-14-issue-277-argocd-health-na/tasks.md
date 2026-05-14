# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Write `tests/infra/test_argocd_values_health_fix.py` with AC-001, AC-002, and AC-003 test cases (red)
- [x] T-002 Confirm all three tests fail before the fix is applied
- [x] T-003 Add `configs.cm.resource.customizations.ignoreResourceUpdates.all: ""` to `infra/local/helm/core/argocd.values.yaml`
- [x] T-004 Apply the identical override to `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`
- [x] T-005 Bump `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13` in `scripts/lib/infra/versions.sh`
- [x] T-006 Bump `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13` in `scripts/lib/infra/versions.baseline.sh`
- [x] T-007 Confirm all three regression tests pass (green)

## Test Automation
- [x] T-101 `tests/infra/test_argocd_values_health_fix.py` — AC-001: argocd.values.yaml override assertion
- [x] T-102 `tests/infra/test_argocd_values_health_fix.py` — AC-002: bootstrap template override assertion
- [x] T-103 `tests/infra/test_argocd_values_health_fix.py` — AC-003: ARGOCD_CHART_VERSION pin assertion (versions.sh + versions.baseline.sh)
- [x] T-104 N/A — no filter/payload-transform logic in this work item
- [x] T-105 Finding-to-test: all three regression tests are the automated translation of the health=N/A finding; they fail without the fix and pass with it
- [x] T-106 Run `make infra-contract-test-fast` — confirm no existing contract tests regress (68 passed)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 N/A — NFR-A11Y-001 declared in spec.md as not applicable (no UI changes)
- [x] T-A02 N/A — no UI changes
- [x] T-A03 N/A — no UI changes
- [x] T-A04 N/A — no UI changes
- [x] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [x] T-201 Run `uv run python3 -m pytest tests/infra/test_argocd_values_health_fix.py -v` and `make infra-contract-test-fast` — 4 PASS, 68 PASS
- [x] T-202 Attach pytest output evidence to `traceability.md` — evidence recorded in pr_context.md Validation Evidence; traceability.md updated post-implementation
- [x] T-203 Confirm no stale TODOs or drift — quality-sdd-check-all PASS
- [x] T-204 Run `make docs-build` and `make docs-smoke` — both PASS
- [x] T-205 Run `make quality-hardening-review` — PASS

## Publish
- [x] P-001 Update `hardening_review.md` with findings and proposals-only section
- [x] P-002 Update `pr_context.md` with coverage, key files, test evidence, and rollback notes
- [x] P-003 Ensure PR description references `pr_context.md` and closes #277

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; targets unchanged by this work item
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact; targets unchanged
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact; targets unchanged
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact; targets unchanged
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact; targets unchanged
