# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `apps/backend/Dockerfile` — multi-stage Python/uvicorn scaffold (Issue #111)
- [x] T-002 Add `apps/touchpoints/Dockerfile` — multi-stage Node.js + nginx scaffold (Issue #111)
- [x] T-003 Update `infra/gitops/platform/base/apps/backend-api-deployment.yaml` — GHCR image, remove command override (Issue #112)
- [x] T-004 Update `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` — GHCR image (Issue #112)
- [x] T-005 Sync bootstrap template copies of both deployment manifests (drift check)
- [x] T-006 Create ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-111-112-app-dockerfile-and-runtime.md`

## Test Automation
- [x] T-101 Add `AppDockerfileAndRuntimeTests::test_backend_dockerfile_multi_stage` in `tests/infra/test_tooling_contracts.py`
- [x] T-102 Add `AppDockerfileAndRuntimeTests::test_touchpoints_dockerfile_multi_stage` in `tests/infra/test_tooling_contracts.py`
- [x] T-103 N/A — no filter/payload-transform logic
- [x] T-104 Issues #111 and #112 translated into `AppDockerfileAndRuntimeTests` structural assertions
- [x] T-105 Add `AppDockerfileAndRuntimeTests::test_backend_deployment_ghcr_image` and `test_touchpoints_deployment_ghcr_image`
- [x] T-106 `make infra-contract-test-fast` passes (103 tests)

## Validation and Release Readiness
- [x] T-201 `make quality-hooks-fast` passes
- [x] T-202 Traceability document updated
- [x] T-203 No stale TODOs, dead code, or drift
- [x] T-204 `make docs-build` and `make docs-smoke` pass (no doc changes)
- [x] T-205 `make quality-hardening-review` passes

## Publish
- [x] P-001 `hardening_review.md` updated
- [x] P-002 `pr_context.md` updated
- [x] P-003 PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected
