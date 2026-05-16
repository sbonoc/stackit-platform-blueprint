# PR Context

## Summary
- Work item: 2026-05-16-issue-248-secrets-manager-module (Part of #248)
- Objective: Add standalone Terraform module and shell layer for STACKIT Secrets Manager; expose namespace and auth_method_details as runtime state keys; deliver credentials as blueprint-secrets-manager-auth K8s Secret
- Scope boundaries: Additive only — new TF module files, new shell helpers, additive state keys, additive contract outputs. No refactoring of existing scripts or routing.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-013, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-015 (all green; 27 assertions in test_contract.py)
- Contract surfaces changed: `blueprint/modules/secrets-manager/module.contract.yaml` — two new outputs (SECRETS_MANAGER_NAMESPACE, SECRETS_MANAGER_AUTH_METHOD_DETAILS)

## Key Reviewer Files
- Primary files to review first:
  - `infra/cloud/stackit/terraform/modules/secrets-manager/main.tf` — instance + user resources, lifecycle block
  - `scripts/lib/infra/secrets_manager.sh` — namespace(), auth_method_details(), reconcile/delete helpers
  - `tests/infra/modules/secrets-manager/test_contract.py` — 27 assertions covering all ACs
- High-risk files:
  - `scripts/bin/infra/secrets_manager_apply.sh` — NFR-SEC-001: password must not appear in state write
  - `scripts/bin/infra/secrets_manager_destroy.sh` — AC-014: delete_runtime_secret called before state removal

## Validation Evidence
- Required commands executed: `uv run pytest tests/infra/modules/secrets-manager/test_contract.py -v` and `uv run pytest tests/infra/test_optional_modules.py::OptionalModulesTests::test_secrets_manager_module_flow -v`
- Result summary: 28 passed, 0 failed. quality-hooks-fast: shellcheck PASS, infra-validate PASS, infra-contract-test-fast PASS, quality-sdd-check-all PASS.
- Artifact references: `tests/infra/modules/secrets-manager/test_contract.py`, `tests/infra/test_optional_modules.py` (updated assertions)

## Risk and Rollback
- Main risks: Foundation Terraform already manages a stackit_secretsmanager_instance — standalone module introduces a second provisioning path. Mitigated: foundation and standalone are independent; foundation never calls standalone module.
- Rollback strategy: Revert secrets_manager.sh, apply.sh, plan.sh, smoke.sh, destroy.sh, module.contract.yaml changes. TF module files can remain (no state side-effects if not applied). Destroy provisioned STACKIT instance via foundation_reconcile_apply driver.

## Deferred Proposals
- None for this work item. Remaining 5 stub modules (dns, public-endpoints, observability, workflows, identity-aware-proxy) tracked in AGENTS.backlog.md under Issue #248.
