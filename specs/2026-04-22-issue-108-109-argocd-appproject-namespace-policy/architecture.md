# Architecture

## Context
- Work item: 2026-04-22-issue-108-109-argocd-appproject-namespace-policy
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: n/a (no application code)
- Frontend stack profile: n/a
- Test automation profile: pytest unit tests in `tests/infra/test_tooling_contracts.py`; fast-lane via `make infra-contract-test-fast`
- Agent execution model: SDD blueprint track; quality-hooks-fast + quality-hardening-review gates

## Problem Statement
- What needs to change and why: All four ArgoCD AppProject overlay files and the bootstrap template copy omitted `external-secrets` from `spec.destinations`. ArgoCD enforces this list as a deployment allowlist — any resource targeting a namespace not listed is rejected at sync time. ESO creates namespaced RBAC resources (Role, RoleBinding for TokenRequest) in the `external-secrets` namespace as part of its normal operation; without the destination entry those resources cannot sync, keeping `platform-local-core` in Degraded health.
- Scope boundaries: additive YAML destination entry in five AppProject files; guard test in `test_tooling_contracts.py`; `test_tooling_contracts.py` added to `contract_test_fast.sh` base_tests array. No changes to `clusterResourceWhitelist` or `namespaceResourceWhitelist`.
- Out of scope: optional-module ESO NotReady when modules are not seeded (cause #2 of #109, tracked in #137); AppProject changes for any other namespace.

## Bounded Contexts and Responsibilities
- Context A — ArgoCD AppProject policy: `spec.destinations` is the allowlist that ArgoCD enforces for all sync operations. The platform AppProject is the sole policy boundary for all platform workloads across all environments.
- Context B — External Secrets Operator (ESO): runs in the `external-secrets` namespace and creates namespaced RBAC resources there as part of its TokenRequest credential flow. These are legitimate blueprint-managed resources.

## High-Level Component Design
- Domain layer: n/a
- Application layer: n/a
- Infrastructure adapters: five AppProject YAML files are the only changed artifacts. The `external-secrets` destination entry is additive — no existing entries are modified.
- Presentation/API/workflow boundaries: `make infra-contract-test-fast` is the fast-lane quality gate. The new `AppProjectNamespacePolicyTests` class in `test_tooling_contracts.py` asserts the destination is present in all five files deterministically.

## Integration and Dependency Edges
- Upstream dependencies: ArgoCD reads AppProject resources from the cluster; the destination allowlist is evaluated at sync time against the resource's target namespace.
- Downstream dependencies: ESO Role/RoleBinding resources in `external-secrets` namespace; any future blueprint-managed RBAC resources targeting that namespace.
- Data/API/event contracts touched: `spec.destinations` list in `argoproj.io/v1alpha1/AppProject` — additive only.

## Non-Functional Architecture Notes
- Security: no new resource kinds added to `namespaceResourceWhitelist`; the `external-secrets` namespace was already in scope via operator deployment, only the explicit destination entry was missing. Guard test prevents future regression.
- Observability: guard failure message names the specific file and missing namespace, giving operators a precise remediation target without log trawling.
- Reliability and rollback: change is additive — reverting means removing five destination entries. The guard test would then fail explicitly, signaling the regression.
- Monitoring/alerting: n/a; change resolves continuous ArgoCD Degraded health on `platform-local-core` that would otherwise require manual investigation.

## Risks and Tradeoffs
- Risk 1: none material. The `external-secrets` namespace was always an intended deployment target; only the AppProject entry was absent.
- Tradeoff 1: opted not to add a `namespaceResourceWhitelist` guard for Role/RoleBinding (they are already listed). Adding it would duplicate an existing guarantee without covering a new failure mode.
