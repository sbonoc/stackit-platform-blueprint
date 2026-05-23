# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: none
- ADR status: none
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001
- Control exception rationale: version pin bump — no runtime logic, API, or security surface changed.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Restore local provisioning after `bitnamilegacy/postgresql:16.x` tags were removed from Docker Hub; align blueprint PostgreSQL version with the latest STACKIT-supported major version (17).
- Success metric: `make infra-audit-version` passes with the new pin; POSTGRES_VERSION default is 17 across local and STACKIT paths.

## Normative Requirements

### Functional Requirements (Normative)
- REQ-001 `POSTGRES_LOCAL_IMAGE_TAG` in `versions.baseline.sh` and `versions.sh` MUST be bumped to `17.6.0-debian-12-r4`.
- REQ-002 `infra/local/helm/postgres/values.yaml` image tag MUST match `POSTGRES_LOCAL_IMAGE_TAG`.
- REQ-003 `POSTGRES_VERSION` default in `postgres.sh`, `infra/cloud/stackit/terraform/modules/postgres/variables.tf`, and `infra/cloud/stackit/terraform/foundation/variables.tf` MUST be bumped to `17`.
- REQ-004 Documentation MUST reflect the new version default and document the bump policy for future tag retirements.

### Acceptance Criteria
- AC-001 `make infra-audit-version` MUST pass with the new `17.6.0-debian-12-r4` pin resolving via `docker manifest inspect`.
- AC-002 `grep -r "16" scripts/lib/infra/postgres.sh infra/cloud/stackit/terraform/modules/postgres/variables.tf infra/cloud/stackit/terraform/foundation/variables.tf` MUST return no version-default matches.
