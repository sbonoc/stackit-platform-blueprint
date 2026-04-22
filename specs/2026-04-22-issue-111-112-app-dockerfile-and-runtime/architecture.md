# Architecture

## Context
- Work item: 2026-04-22-issue-111-112-app-dockerfile-and-runtime
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest structural contract tests in `tests/infra/test_tooling_contracts.py`
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `apps/backend/Dockerfile` and `apps/touchpoints/Dockerfile` do not exist, causing `publish_ghcr.sh` to warn and skip both build candidates (`candidate_count=0`). The deployment manifests at `infra/gitops/platform/base/apps/` reference public Python/nginx images with a hardcoded `command:` override instead of consumer-owned GHCR images — disconnecting the image build lane from the gitops deployment lane.
- Scope boundaries: scaffold Dockerfiles in `apps/backend/` and `apps/touchpoints/`; update deployment manifests and bootstrap template copies.
- Out of scope: catalog scaffold renderer templates, `scripts/bin/platform/apps/bootstrap.sh` runtime image variables, upgrade fixture matrix files, consumer-side `main.py`/`requirements.txt`/`package.json` starter files.

## Bounded Contexts and Responsibilities
- Context A (image build lane): `publish_ghcr.sh` builds Docker images from `apps/backend/Dockerfile` and `apps/touchpoints/Dockerfile` and pushes to GHCR. Adding the Dockerfiles closes the `candidate_count=0` warning.
- Context B (gitops deployment lane): `infra/gitops/platform/base/apps/*.yaml` define the workload manifests deployed to the local cluster via ArgoCD. Updating the image fields to GHCR references and removing the command override connects the gitops lane to the image build lane output.

## High-Level Component Design
- Domain layer: none (infrastructure-only change)
- Application layer: `apps/backend/Dockerfile` — multi-stage Python build (builder: pip install; runtime: uvicorn CMD); `apps/touchpoints/Dockerfile` — multi-stage Node.js build (builder: pnpm/npm build; runtime: nginx COPY dist)
- Infrastructure adapters: `infra/gitops/platform/base/apps/backend-api-deployment.yaml` and `touchpoints-web-deployment.yaml` updated; `scripts/templates/infra/bootstrap/...` copies synced
- Presentation/API/workflow boundaries: none changed

## Integration and Dependency Edges
- Upstream dependencies: `scripts/lib/platform/apps/versions.sh` defines `PYTHON_RUNTIME_BASE_IMAGE_VERSION`, `NODE_RUNTIME_BASE_IMAGE_VERSION`, `NGINX_RUNTIME_BASE_IMAGE_VERSION` as the platform-authoritative version variables; the scaffolded Dockerfiles currently pin those base image versions directly in the `FROM` instructions, so the values are duplicated rather than consumed via build args.
- Downstream dependencies: `publish_ghcr.sh` consumes `apps/backend/Dockerfile`; ArgoCD consumes `infra/gitops/platform/base/apps/*.yaml`.
- Data/API/event contracts touched: none

## Non-Functional Architecture Notes
- Security: Dockerfiles must not embed secrets; multi-stage build minimizes final image attack surface by excluding build tooling.
- Observability: no new metrics or logs; existing `publish_ghcr.sh` `candidate_count`/`published_count` metrics reflect Dockerfile presence.
- Reliability and rollback: revert Dockerfile additions and deployment manifest image changes; bootstrap template copies roll back with the same commit.
- Monitoring/alerting: none

## Risks and Tradeoffs
- Risk 1: consumers must build and push to their own GHCR org before the local cluster can pull the image — scaffold alone does not make the cluster fully operational. Mitigation: `imagePullPolicy: IfNotPresent` preserves local fallback; `make apps-publish-ghcr` documents the build path.
- Tradeoff 1: multi-stage Dockerfile adds complexity vs single-stage — chosen because single-stage is a known anti-pattern that mixes build tooling with the runtime image.
