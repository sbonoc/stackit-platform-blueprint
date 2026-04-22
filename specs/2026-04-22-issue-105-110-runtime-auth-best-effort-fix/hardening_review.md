# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1 (Issue #105): `reconcile_eso_runtime_secrets.sh` aborted under `set -e` before writing its state file when `kustomize apply` failed due to missing target namespaces, propagating `plugin_eso_status=failure` to the orchestrator and failing `make infra-provision-deploy` even when `RUNTIME_CREDENTIALS_REQUIRED=false`. Fixed by wrapping `run_kustomize_apply` in `if !`.
- Finding 2 (Issue #110): `reconcile_argocd_repo_credentials.sh` treated `gho_` GitHub OAuth tokens as a reconcile issue, creating a confusing `status=success-with-warnings` when the same credential authenticates successfully for repo read operations. Fixed by replacing `record_reconcile_issue` with `log_info` for `gho_` tokens.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `log_info` message added in `reconcile_argocd_repo_credentials.sh` for `gho_` acceptance; `record_reconcile_issue` message added in `reconcile_eso_runtime_secrets.sh` for kustomize apply failure in best-effort mode.
- Operational diagnostics updates: `apply_mode=kubectl-apply-kustomize-failed` now appears in the `runtime_credentials_eso_reconcile.env` state artifact when the apply fails in best-effort mode, giving operators a precise remediation target.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: minimal surgical changes; no new abstractions introduced; existing `record_reconcile_issue` / `log_info` helpers reused correctly.
- Test-automation and pyramid checks: 2 structural contract tests added; test pyramid ratios unaffected.
- Documentation/diagram/CI/skill consistency checks: ADR created; no diagram or CI changes needed.

## Proposals Only (Not Implemented)
- Proposal 1: Add retry/wait logic to `run_kustomize_apply` for namespace creation timing so the apply can succeed on second attempt. Deferred — out of scope; namespace creation timing is owned by the Crossplane provisioning layer.
- Proposal 2: Add a live integration test that runs `reconcile_eso_runtime_secrets.sh` in DRY_RUN=true mode and validates the state file output. Deferred — dry-run mode returns 0 unconditionally and does not exercise the guard; a live-cluster test is required for full coverage.
