# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1 (Issue #111): `apps/backend/Dockerfile` and `apps/touchpoints/Dockerfile` were absent, causing `publish_ghcr.sh` to warn and skip both build candidates (`candidate_count=0`). Fixed by adding multi-stage scaffold Dockerfiles in `apps/backend/` and `apps/touchpoints/`.
- Finding 2 (Issue #112): `backend-api-deployment.yaml` referenced `python:3.13.9` with a hardcoded `command: [python, -m, http.server, 8080]` override; `touchpoints-web-deployment.yaml` referenced `nginx:1.29.2`. Both disconnected the gitops deployment lane from the consumer GHCR image build lane. Fixed by updating both manifests to GHCR references and removing the command override; bootstrap template copies synced.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new metrics; existing `candidate_count`/`published_count` in `apps_publish_ghcr` state file now reflects `candidate_count=2` when both Dockerfiles are present.
- Operational diagnostics updates: none.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: additive changes only; no new abstractions; existing `publish_candidate` helper in `publish_ghcr.sh` reused unchanged.
- Test-automation and pyramid checks: 4 structural contract tests added in `AppDockerfileAndRuntimeTests`; test pyramid ratios unaffected.
- Documentation/diagram/CI/skill consistency checks: ADR created; no diagram or CI changes needed.

## Proposals Only (Not Implemented)
- Proposal 1: Add companion scaffold files (`apps/backend/main.py`, `apps/backend/requirements.txt`, `apps/touchpoints/package.json`, `apps/touchpoints/src/`) so the Dockerfiles produce a runnable image without modification. Deferred — consumer starter files are out of scope; the Dockerfile scaffold is sufficient to demonstrate the build pattern.
- Proposal 2: Add a live integration test that runs `publish_ghcr.sh` in dry-run mode and validates `candidate_count=2` in the state artifact. Deferred — dry-run does not exercise the docker build path; a live test requires docker login credentials not available in CI.
