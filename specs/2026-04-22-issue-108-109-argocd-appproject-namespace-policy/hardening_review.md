# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: All four ArgoCD AppProject overlay files and the bootstrap template copy were missing `external-secrets` in `spec.destinations`, blocking ArgoCD from syncing RBAC resources (Role, RoleBinding) that the External Secrets Operator creates in the `external-secrets` namespace. Added the missing destination entry to all five files.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: None. No new metrics or log lines introduced.
- Operational diagnostics updates: Guard test failure message explicitly names the missing namespace and the offending file(s), giving operators a precise remediation target.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Change is minimal — additive YAML entries only, no logic changes. Guard test class is co-located in `test_tooling_contracts.py` following established pattern.
- Test-automation and pyramid checks: New unit-level guard test added in `AppProjectNamespacePolicyTests`. Test covers all five AppProject files deterministically. `test_tooling_contracts.py` added to `base_tests` in `contract_test_fast.sh` so it runs in both `template-source` and `generated-consumer` modes.
- Documentation/diagram/CI/skill consistency checks: ADR written at `docs/blueprint/architecture/decisions/ADR-20260422-issue-108-109-argocd-appproject-namespace-policy.md`. Traceability matrix complete. `AGENTS.decisions.md` updated.

## Test isolation fix
- `profile_module_enablement_contract` in `test_tooling_contracts.py` now explicitly sets `ROOT_DIR` to the temp repo root so that `profile.sh` resolves the patched contract from the temp dir, not from `ROOT_DIR` inherited from the `make infra-contract-test-fast` process environment.

## Proposals Only (Not Implemented)
- Proposal 1: Extend guard to also verify `namespaceResourceWhitelist` covers `Role` and `RoleBinding` kinds. Deferred — current whitelist already includes those kinds; adding a second assertion would duplicate an existing guarantee without catching a new failure mode.
