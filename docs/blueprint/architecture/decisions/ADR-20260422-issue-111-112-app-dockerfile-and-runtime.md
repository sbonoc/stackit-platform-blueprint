# ADR-20260422: App Dockerfile Scaffold and Runtime Deployment Fix (Issues #111, #112)

## Status
Approved

## Context
Two gaps exist between the image build lane and the gitops deployment lane:

1. `apps/backend/Dockerfile` and `apps/touchpoints/Dockerfile` do not exist. `publish_ghcr.sh` warns and skips both build candidates (`candidate_count=0`), so the GHCR image lane produces no output.

2. The gitops deployment manifests at `infra/gitops/platform/base/apps/` reference public Docker Hub images (`python:3.13.9`, `nginx:1.29.2`) with a hardcoded `command:` override that duplicates the Python HTTP server invocation in the manifest. This means ArgoCD deploys a python.org image with a script-injected command rather than the consumer's own GHCR image.

## Decision

### Issue #111 — scaffold Dockerfiles

**Option A**: Single-stage Dockerfiles (`FROM python:... CMD [...]`, `FROM nginx:...`). Simpler but mixes build tooling with the runtime image — a known anti-pattern that inflates the final image and exposes build-time dependencies.

**Option B (selected)**: Multi-stage Dockerfiles with an explicit builder stage and a lean runtime stage. Demonstrates the canonical production pattern, separates pip/pnpm from the final image, and is consistent with the FastAPI/Vue stack profiles declared in the spec.

### Issue #112 — deployment manifest image references

**Option A**: Keep placeholder public images; add documentation note that consumers must override via values. Deferred debt — consumers reading the manifest would not know what GHCR image `publish_ghcr.sh` produces.

**Option B (selected)**: Update image fields to match the default `publish_ghcr.sh` output (`ghcr.io/example-org/platform-blueprint-backend:0.1.0`, `ghcr.io/example-org/platform-blueprint-touchpoints:0.1.0`); remove the hardcoded `command:` override from the backend manifest (CMD is now defined in the Dockerfile). Update bootstrap template copies for drift-check compliance.

## Consequences
- `publish_ghcr.sh` now finds both Dockerfiles (`candidate_count=2`) and can build and push in execute mode.
- Deployment manifests reference the same images that `publish_ghcr.sh` produces, closing the build–gitops lane gap.
- Consumers must build and push their images to their own GHCR org before the images are pullable in a live cluster; `imagePullPolicy: IfNotPresent` preserves local-first fallback.
- Bootstrap template copies are synced; `make infra-validate` drift check passes.
