# PR Context

## Summary
- Work item: Issue #108 + #109 — ArgoCD AppProject namespace policy gap
- Objective: Add `external-secrets` to `spec.destinations` in all ArgoCD AppProject overlays and the bootstrap template copy; add a guard test in `infra-contract-test-fast` to prevent regression; fix test isolation so the guard test passes when run in the full fast-lane suite.
- Scope boundaries: Destination list expansion only — no changes to `clusterResourceWhitelist` or `namespaceResourceWhitelist`. Issue #109 cause #2 (optional-module ESOs NotReady when not seeded) deferred to #137.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, NFR-SEC-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Contract surfaces changed: `spec.destinations` in five AppProject YAML files; `base_tests` array in `contract_test_fast.sh`; new test class in `test_tooling_contracts.py`

## Key Reviewer Files
- Primary files to review first:
  - `infra/gitops/argocd/overlays/*/appproject.yaml` (four overlay files)
  - `scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/appproject.yaml`
  - `tests/infra/test_tooling_contracts.py` — `AppProjectNamespacePolicyTests` class (end of file)
  - `scripts/bin/infra/contract_test_fast.sh` — `base_tests` array
- High-risk files: None. The AppProject YAML changes are additive; no existing entries were modified.

## Validation Evidence
- Required commands executed:
  - `make infra-contract-test-fast` → 94 passed, 2 subtests passed
  - `make quality-hooks-fast` → success
  - `make quality-hardening-review` → success
- Result summary: All gates green. Guard test `test_all_appproject_overlays_include_external_secrets_destination` passes. Test isolation fix confirmed: `test_profile_uses_generated_repo_contract_when_module_env_is_unset` passes in both isolation and full-suite execution.
- Artifact references: `specs/2026-04-22-issue-108-109-argocd-appproject-namespace-policy/evidence_manifest.json`

## Risk and Rollback
- Main risks: None material. The change adds a destination entry that was always intended to be present. The `namespaceResourceWhitelist` already covers the resource kinds ESO creates there.
- Rollback strategy: Revert the five AppProject YAML files. The guard test and `contract_test_fast.sh` change can remain (guard would then fail, signaling the regression explicitly).

## Deferred Proposals
- Proposal 1 (not implemented): Guard `namespaceResourceWhitelist` for Role/RoleBinding presence. Deferred — current whitelist already includes those kinds.
- Issue #109 cause #2 (not implemented): Optional-module ESOs NotReady when modules are not seeded. Tracked in #137.
