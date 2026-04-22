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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-108-109-argocd-appproject-namespace-policy.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-007, SDD-C-009, SDD-C-012, SDD-C-013
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: single-agent
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none (manifest and test change only; no managed service involved)
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none (static YAML manifest fix; no local runtime execution required)

## Objective
- Business outcome: ArgoCD AppProject `platform-local` (and all environment variants) MUST permit the `external-secrets` namespace as a deployment destination so platform and consumer-extended manifests targeting that namespace can sync without policy errors.
- Success metric: `platform-local-core` sync no longer fails with "namespace external-secrets is not permitted in project 'platform-local'"; `infra-contract-test-fast` guard fails if the namespace is ever removed.

## Normative Requirements

### Functional Requirements (Normative)

#### AppProject namespace policy fix (#108)
- FR-001 ALL AppProject overlays (local, dev, stage, prod) and the bootstrap template copy MUST include `external-secrets` under `spec.destinations` targeting `https://kubernetes.default.svc`.
- FR-002 `infra-contract-test-fast` MUST include a guard test that fails when any AppProject overlay or the bootstrap template is missing `external-secrets` from its destinations list.
- FR-003 The guard MUST check all four environment overlays (local, dev, stage, prod) and the bootstrap template AppProject file.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 Adding `external-secrets` to destinations MUST NOT expand `namespaceResourceWhitelist` or `clusterResourceWhitelist` with new resource kinds.
- NFR-OPS-001 Guard test failure message MUST identify the specific AppProject file path and the missing namespace.

## Acceptance Criteria (Normative)
- AC-001 All five AppProject files (four overlays + bootstrap template) contain `namespace: external-secrets` under `spec.destinations`.
- AC-002 `make infra-contract-test-fast` passes with the new guard test green.
- AC-003 Guard test fails (regression guard) when `external-secrets` is removed from any AppProject destinations list.
- AC-004 `make infra-validate` passes after the fix.
- AC-005 Issue #108 sync failure (`namespace external-secrets is not permitted`) is resolved at next ArgoCD re-sync.
- AC-006 Issue #109 Degraded health caused by the AppProject namespace policy gap resolves at next ArgoCD re-sync after fix is deployed. (Residual Degraded health from optional-module ExternalSecrets NotReady is tracked separately in issue #137.)

## Informative Notes (Non-Normative)
- Context: the `external-secrets` namespace is managed by the external-secrets operator (ESO) itself. Platform and consumer-extended manifests deploy namespaced RBAC resources there (e.g. Role/RoleBinding for ESO TokenRequest). These resources are legitimate deployment targets that the AppProject policy MUST explicitly allow.
- Tradeoffs: widening the AppProject destinations to include `external-secrets` allows ArgoCD to manage resources in that namespace. The `namespaceResourceWhitelist` already restricts which resource kinds can be deployed; no new kinds are added by this change, so the additional blast radius is bounded.
- Issue #109 relationship: fixing the AppProject namespace gap resolves the Degraded health signal caused by sync failures. Residual Degraded health from optional-module ExternalSecrets being NotReady (e.g. postgres-runtime-credentials when Postgres is not seeded) is a separate root cause tracked in issue #137.

## Explicit Exclusions
- Expanding `namespaceResourceWhitelist` with new resource kinds for `external-secrets`
- Optional-module ExternalSecret conditional deployment (postgres-runtime-credentials etc.) — issue #137
- Changes to `clusterResourceWhitelist`

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this IS the upstream fix)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Out of Scope
- Optional-module ExternalSecret conditional deployment (`postgres-runtime-credentials` NotReady when Postgres not seeded) — tracked in issue #137.
- Expanding `namespaceResourceWhitelist` with new resource kinds for `external-secrets`.
