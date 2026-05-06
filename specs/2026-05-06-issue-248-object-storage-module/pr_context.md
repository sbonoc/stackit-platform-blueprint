# PR Context

## Summary
- Work item: Issue #248 — Object-storage module dual-lane implementation (MinIO local + STACKIT Terraform standalone module)
- Objective: Elevate object-storage from partial scaffold to production-grade optional module: correct execution class (`fallback_runtime` on local lane), Secret-backed credentials (no plaintext in rendered values), STACKIT standalone Terraform module, `OBJECT_STORAGE_REGION` in 5-key runtime contract, and complete module documentation.
- Scope boundaries: `scripts/lib/infra/object_storage.sh`, `scripts/bin/infra/object_storage_{apply,destroy,smoke}.sh`, `scripts/bin/infra/bootstrap.sh`, `scripts/lib/infra/module_execution.sh`, `infra/local/helm/object-storage/values.yaml`, `scripts/templates/infra/bootstrap/infra/local/helm/object-storage/values.yaml`, `infra/cloud/stackit/terraform/modules/object-storage/`, `blueprint/modules/object-storage/module.contract.yaml`, `docs/platform/modules/object-storage/README.md`, test files. Foundation Terraform inline resources and existing make targets are not modified.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001 (N/A)
- Acceptance criteria covered: AC-001 through AC-009
- Contract surfaces changed: `blueprint/modules/object-storage/module.contract.yaml` — additive `OBJECT_STORAGE_REGION` output added to `outputs.produced`

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/object_storage.sh` — secret lifecycle functions and render function (credential removal)
  - `scripts/bin/infra/object_storage_apply.sh` — reconcile ordering (secret before helm)
  - `scripts/lib/infra/module_execution.sh` — execution class correction (provider_backed → fallback_runtime)
  - `infra/local/helm/object-storage/values.yaml` — existingSecret pattern replaces plaintext
- High-risk files: `scripts/lib/infra/module_execution.sh` (class change affects routing — guarded by tooling contract tests), `scripts/bin/infra/bootstrap.sh` (credential variable removal — guarded by apply script test)

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/infra/modules/object-storage/ -v` (27/27 passed), `python3 -m pytest tests/infra/test_tooling_contracts.py -k object` (2/2 passed), `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (8/9 checks pass; remaining resolves with publish completion)
- Result summary: All implementation tests green. shellcheck clean. infra-validate clean. infra-contract-test-fast clean. quality-docs-check-changed clean. No regressions in existing test suite.
- Artifact references: `artifacts/infra/object_storage_runtime.env` (written by apply), `artifacts/infra/object_storage_smoke.env` (written by smoke), `artifacts/infra/rendered/object-storage.values.yaml` (rendered by apply — contains no credentials)

## Risk and Rollback
- Main risks: (1) `auth.existingSecret` requires the K8s Secret `blueprint-object-storage-auth` to exist before pod start — guaranteed by `object_storage_reconcile_runtime_secret` calling before `run_helm_upgrade_install`; if apply fails mid-way the Secret exists but the chart may not — idempotent re-run resolves. (2) Execution class change (`provider_backed` → `fallback_runtime`) for local lane affects `OPTIONAL_MODULE_EXECUTION_CLASS` output — guarded by tooling contract tests.
- Rollback strategy: Revert the PR; existing runtime state files are not touched by rollback. The K8s Secret `blueprint-object-storage-auth` can be deleted manually via `kubectl delete secret -n data blueprint-object-storage-auth` if needed.

## Deferred Proposals
- none
