# PR Context

## Summary
- Work item: 2026-04-22-issue-111-112-app-dockerfile-and-runtime
- Objective: add scaffold Dockerfiles for `apps/backend` and `apps/touchpoints` (Issue #111) and update gitops deployment manifests to reference consumer-owned GHCR images instead of public placeholders (Issue #112).
- Scope boundaries: `apps/backend/Dockerfile`, `apps/touchpoints/Dockerfile`, `infra/gitops/platform/base/apps/backend-api-deployment.yaml`, `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml`, bootstrap template copies of both manifests, ADR, structural contract tests.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-SEC-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008
- Contract surfaces changed: none (no new env vars, make targets, API, or events)

## Key Reviewer Files
- Primary files to review first:
  - `apps/backend/Dockerfile`
  - `apps/touchpoints/Dockerfile`
  - `infra/gitops/platform/base/apps/backend-api-deployment.yaml`
  - `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml`
  - `tests/infra/test_tooling_contracts.py` — `AppDockerfileAndRuntimeTests` class
- High-risk files:
  - `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/backend-api-deployment.yaml` (bootstrap template drift)
  - `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` (bootstrap template drift)

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make quality-hardening-review`, `make infra-contract-test-fast`, `make docs-build`, `make docs-smoke`
- Result summary: all gates green; 103 contract tests passed (was 99, +4 new `AppDockerfileAndRuntimeTests` tests)
- Artifact references: `specs/2026-04-22-issue-111-112-app-dockerfile-and-runtime/traceability.md`, `hardening_review.md`

## Risk and Rollback
- Main risks: consumers must build and push to GHCR before images are pullable in a live cluster; `imagePullPolicy: IfNotPresent` preserves local fallback.
- Rollback strategy: revert Dockerfile additions and deployment manifest image changes; bootstrap template copies roll back with the same commit.

## Deferred Proposals
- Proposal 1 (not implemented): add companion scaffold files (`main.py`, `requirements.txt`, `package.json`, `src/`) — consumer responsibility; out of scope.
- Proposal 2 (not implemented): live `publish_ghcr.sh` dry-run integration test for `candidate_count=2` — requires docker login not available in CI.
