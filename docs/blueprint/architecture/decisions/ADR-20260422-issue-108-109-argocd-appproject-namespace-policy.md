# ADR-20260422-issue-108-109-argocd-appproject-namespace-policy: ArgoCD AppProject Namespace Policy Gap

## Metadata
- Status: approved
- Date: 2026-04-22
- Owners: @sbonoc
- Related spec path: `specs/2026-04-22-issue-108-109-argocd-appproject-namespace-policy/spec.md`

## Business Objective and Requirement Summary
- Business objective: ArgoCD AppProject `platform-local` (and all environment variants) MUST permit the `external-secrets` namespace as a deployment destination so platform and consumer-extended manifests targeting that namespace sync without policy errors.
- Functional requirements summary:
  - ALL AppProject overlays (local, dev, stage, prod) and the bootstrap template copy MUST include `external-secrets` under `spec.destinations`
  - `infra-contract-test-fast` MUST include a guard that fails when any AppProject file is missing that entry
- Non-functional requirements summary:
  - no new resource kinds added to `namespaceResourceWhitelist` or `clusterResourceWhitelist`
  - guard failure message identifies the offending file and missing namespace
- Desired timeline: immediate; unblocks ArgoCD sync for any resource targeting `external-secrets`.

## Decision Drivers
- ESO-managed namespaced RBAC resources (Role/RoleBinding for TokenRequest) are created in the `external-secrets` namespace. ArgoCD rejects sync of these resources if the AppProject does not list `external-secrets` as a permitted destination, producing `namespace external-secrets is not permitted in project 'platform-local'`.
- The gap existed in all four environment overlays and the bootstrap template, meaning it reproduced across every generated consumer and every environment.
- No automated guard existed to catch AppProject destination gaps before reaching a live cluster.

## Options Considered

### Fix the AppProject gap
- Option A: add `external-secrets` to `spec.destinations` in all AppProject overlays and the bootstrap template.
- Option B: move all resources that target `external-secrets` out of platform manifests (remove the need for the destination entirely).

## Recommended Option
- Selected option: Option A
- Rationale: Option B would require removing ESO-managed RBAC resources that are a legitimate and necessary part of the platform runtime. Option A is the minimal, correct fix — the AppProject policy was simply missing a namespace that is a genuine deployment target. The `namespaceResourceWhitelist` already bounds which resource kinds can be deployed in any listed namespace, so widening destinations does not materially increase the attack surface.

## Consequences
- **Positive**: `platform-local-core` sync no longer fails for resources in `external-secrets`; platform-local-core health signal improves once ArgoCD re-syncs.
- **Positive**: Guard test in `infra-contract-test-fast` prevents future namespace destination gaps across all AppProject files.
- **Neutral**: The `external-secrets` namespace is now a managed ArgoCD destination; the `namespaceResourceWhitelist` continues to restrict which resource kinds can be deployed there.
- **Residual**: `platform-local-core` health may still show Degraded if optional-module ExternalSecrets (e.g. `postgres-runtime-credentials`) are NotReady because their source-secret fields are absent. This is tracked separately in issue #137.
