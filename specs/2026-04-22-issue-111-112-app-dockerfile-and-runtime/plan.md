# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: four file additions/modifications; no new helpers or abstractions.
- Anti-abstraction gate: reuses existing `publish_ghcr.sh` publish_candidate function; no new scripts.
- Integration-first testing gate: structural contract tests verify Dockerfile existence and manifest image fields.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: issue #111 (missing Dockerfiles) and #112 (wrong image references) translated into `AppDockerfileAndRuntimeTests` structural assertions.

## Delivery Slices
1. Slice 1 — scaffold Dockerfiles: add `apps/backend/Dockerfile` (multi-stage Python/uvicorn) and `apps/touchpoints/Dockerfile` (multi-stage Node.js + nginx); add `test_backend_dockerfile_multi_stage` and `test_touchpoints_dockerfile_multi_stage`.
2. Slice 2 — deployment manifest image fix: update `infra/gitops/platform/base/apps/backend-api-deployment.yaml` (GHCR image, remove command override) and `touchpoints-web-deployment.yaml` (GHCR image); sync bootstrap template copies; add `test_backend_deployment_ghcr_image` and `test_touchpoints_deployment_ghcr_image`.

## Change Strategy
- Migration/rollout sequence: both slices ship in one PR; no migration needed.
- Backward compatibility policy: `imagePullPolicy: IfNotPresent` preserved; `publish_ghcr.sh` already handles missing Dockerfiles gracefully (warn+skip).
- Rollback plan: revert Dockerfile additions and deployment manifest image changes.

## Validation Strategy (Shift-Left)
- Unit checks: `AppDockerfileAndRuntimeTests` (4 tests) in `tests/infra/test_tooling_contracts.py`.
- Contract checks: `make infra-contract-test-fast` (103 tests pass).
- Integration checks: `make quality-hooks-fast` passes end-to-end.
- E2E checks: N/A (live cluster not available in CI; image build requires docker login).

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
- Notes: no app delivery scope affected; Dockerfiles are additive; deployment manifest changes do not break smoke (smoke counts deployment objects, not pod readiness).

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-111-112-app-dockerfile-and-runtime.md`; `AGENTS.decisions.md`.
- Consumer docs updates: none.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no new metrics; existing `candidate_count`/`published_count` in `publish_ghcr.sh` reflect Dockerfile presence.
- Alerts/ownership: none.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1: consumers must build and push to their GHCR org before images are pullable in a live cluster -> mitigation: `imagePullPolicy: IfNotPresent` preserves local-first fallback; `make apps-publish-ghcr` documents the build path.
- Risk 2: the touchpoints Dockerfile references `npm run build` which requires a `package.json` build script absent in the empty scaffold directory -> mitigation: this is a consumer responsibility; the Dockerfile is a scaffold/template, not an immediately runnable artifact.
