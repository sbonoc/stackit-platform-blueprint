# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-111-112-app-dockerfile-and-runtime.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-005, SDD-C-012
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest unit tests in `tests/infra/test_tooling_contracts.py`; fast-lane via `make infra-contract-test-fast`
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: `make apps-publish-ghcr` no longer warns and skips with `candidate_count=0` due to missing Dockerfiles; generated consumers receive deployment manifests that reference consumer-owned GHCR images rather than public Python/nginx placeholders with hardcoded command overrides — closing the gap between the image build lane (`publish_ghcr.sh`) and the gitops deployment lane.
- Success metric: structural contract tests confirm both Dockerfiles exist with correct multi-stage patterns and correct EXPOSE ports; deployment manifest image fields reference GHCR paths and no hardcoded `command:` block appears in the backend manifest.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST: `apps/backend/Dockerfile` MUST exist and implement a multi-stage Python build with a final stage that EXPOSEs port 8080 and defines a CMD that starts the application server.
- FR-002 MUST: `apps/touchpoints/Dockerfile` MUST exist and implement a multi-stage build with a Node.js build stage and an nginx final stage that EXPOSEs port 80.
- FR-003 MUST: `infra/gitops/platform/base/apps/backend-api-deployment.yaml` MUST reference a GHCR consumer image (`ghcr.io/example-org/platform-blueprint-backend:0.1.0-dev`, matching the default `publish_ghcr.sh` output when `APP_RELEASE` is not set to `1`) and MUST NOT contain a `command:` override.
- FR-004 MUST: `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` MUST reference a GHCR consumer image (`ghcr.io/example-org/platform-blueprint-touchpoints:0.1.0-dev`, matching the default `publish_ghcr.sh` output when `APP_RELEASE` is not set to `1`).
- FR-005 MUST: Bootstrap template copies of both deployment manifests (`scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/`) MUST be updated to match the live manifests (template drift check enforced by `make infra-validate`).

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST: Dockerfiles MUST NOT embed secrets, tokens, credentials, or external service endpoints.
- NFR-OPS-001 MUST: Both deployment manifests MUST keep `imagePullPolicy: IfNotPresent` unchanged to preserve local-first cluster compatibility.

## Normative Option Decision
- Option A: Add minimal single-stage Dockerfiles (`FROM python:... CMD [...]`, `FROM nginx:...`); remove command overrides from deployment manifests.
- Option B: Add multi-stage Dockerfiles (builder + runtime stages) with explicit EXPOSE and CMD; update deployment manifests to GHCR references; update bootstrap template copies.
- Selected option: OPTION_B
- Rationale: Multi-stage Dockerfiles are the canonical pattern for production-grade container builds — they separate build tooling from the runtime image and reduce final image size. A single-stage Dockerfile would demonstrate a sub-optimal pattern that consumers would need to rewrite. The template bootstrap copies must be updated per the existing `make infra-validate` drift check.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- Event contract: none
- Make/CLI contract: none (publish_ghcr.sh already supports both Dockerfiles; no new make targets)
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: `apps/backend/Dockerfile` exists and uses a multi-stage build (`FROM ... AS builder` and `FROM ... AS runtime` or equivalent).
- AC-002 MUST: `apps/backend/Dockerfile` has `EXPOSE 8080` and a CMD that invokes an application server.
- AC-003 MUST: `apps/touchpoints/Dockerfile` exists and uses a multi-stage build with a Node.js builder stage and an nginx final stage.
- AC-004 MUST: `apps/touchpoints/Dockerfile` has `EXPOSE 80`.
- AC-005 MUST: `infra/gitops/platform/base/apps/backend-api-deployment.yaml` image field references a GHCR registry (`ghcr.io/`) — not a bare docker hub image such as `python:x.y.z`. The scaffold default is `ghcr.io/example-org/platform-blueprint-backend:0.1.0-dev` (matching `publish_ghcr.sh` defaults with `APP_RELEASE=0`).
- AC-006 MUST: `infra/gitops/platform/base/apps/backend-api-deployment.yaml` does NOT contain a `command:` key.
- AC-007 MUST: `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` image field references a GHCR registry (`ghcr.io/`) — not a bare docker hub image such as `nginx:x.y.z`. The scaffold default is `ghcr.io/example-org/platform-blueprint-touchpoints:0.1.0-dev`.
- AC-008 MUST: A structural contract test class `AppDockerfileAndRuntimeTests` asserts AC-001 through AC-007.

## Informative Notes (Non-Normative)
- Context: Issue #111 was discovered because `publish_ghcr.sh` warns and exits with `candidate_count=0` when `apps/backend/Dockerfile` and `apps/touchpoints/Dockerfile` are absent. Issue #112 was discovered because the gitops deployment manifests still reference `python:3.13.9` with a `command: [python, -m, http.server, 8080]` override — the image build lane (GHCR) and the gitops lane are disconnected.
- Tradeoffs: The scaffold Dockerfiles use a multi-stage pattern for correctness; consumers can still choose single-stage for simplicity. The GHCR image reference uses the default `example-org` owner — consumers must override `APPS_GHCR_OWNER` (or `BLUEPRINT_GITHUB_ORG`) and rebuild/push before the local cluster can pull from a real registry.
- Clarifications: none

## Explicit Exclusions
- No changes to `scripts/bin/platform/apps/bootstrap.sh` — `backend_runtime_image` and `touchpoints_runtime_image` in that script feed the catalog manifest renderer (a separate lane), not the gitops deployment manifests.
- No changes to the catalog scaffold renderer or its templates.
- No additional scaffold files (`main.py`, `requirements.txt`, `package.json`) — those are consumer responsibilities.
- No changes to `tests/blueprint/fixtures/upgrade_matrix/` fixture files — those are already simplified fixtures that are upgrade-compatible.
