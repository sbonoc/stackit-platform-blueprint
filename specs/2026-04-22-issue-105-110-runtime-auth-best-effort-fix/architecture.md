# Architecture

## Context
- Work item: 2026-04-22-issue-105-110-runtime-auth-best-effort-fix
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: none (no application code)
- Frontend stack profile: none
- Test automation profile: pytest unit tests in `tests/infra/test_tooling_contracts.py`; fast-lane via `make infra-contract-test-fast`
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Two runtime auth scripts have behavior that conflicts with their declared best-effort contract. `reconcile_eso_runtime_secrets.sh` aborts under `set -e` before writing its state file when `kustomize apply` fails due to missing namespaces — causing the orchestrator to record `plugin_eso_status=failure` and fail the entire `make infra-provision-deploy` even when `RUNTIME_CREDENTIALS_REQUIRED=false`. `reconcile_argocd_repo_credentials.sh` rejects `gho_` tokens as a reconcile issue, creating a confusing `success-with-warnings` state when the same token authenticates successfully for repo read operations.
- Scope boundaries: two one-line changes in `scripts/bin/platform/auth/`; two structural contract tests added to `tests/infra/test_tooling_contracts.py`.
- Out of scope: namespace creation timing, retry logic, orchestrator changes.

## Bounded Contexts and Responsibilities
- Context A — ESO runtime credential reconciliation: `reconcile_eso_runtime_secrets.sh` owns the `runtime_credentials_eso_reconcile` state artifact. Its best-effort mode (`RUNTIME_CREDENTIALS_REQUIRED=false`) must never propagate a non-zero exit for recoverable failures.
- Context B — ArgoCD repo credential reconciliation: `reconcile_argocd_repo_credentials.sh` validates and seeds ArgoCD git repository credentials. Token-format policy must match actual authentication behavior to avoid ambiguous warning states.

## High-Level Component Design
- Domain layer: none
- Application layer: none
- Infrastructure adapters:
  - `reconcile_eso_runtime_secrets.sh` line 362: `run_kustomize_apply` call wrapped in `if !` so `set -e` cannot abort before the state file is written. `record_reconcile_issue` captures the failure. The existing end-of-script logic then sets `status=warn-and-skip` (required=false) or `status=failed-required` + `log_fatal` (required=true).
  - `reconcile_argocd_repo_credentials.sh` `gho_` branch: replaces `record_reconcile_issue` with `log_info` so the token is accepted without raising a reconcile issue.
- Presentation/API/workflow boundaries: `make infra-provision-deploy` → `reconcile_runtime_identity.sh` orchestrator → `reconcile_eso_runtime_secrets.sh` / `reconcile_argocd_repo_credentials.sh`.

## Integration and Dependency Edges
- Upstream dependencies: `run_kustomize_apply` helper in `scripts/lib/infra/tooling.sh`; `record_reconcile_issue` function in both scripts; `log_info`/`log_fatal` in `scripts/lib/shell/bootstrap.sh`.
- Downstream dependencies: `reconcile_runtime_identity.sh` reads exit codes from both scripts to set `plugin_eso_status` and `plugin_argocd_repo_status`.
- Data/API/event contracts touched: `artifacts/infra/runtime_credentials_eso_reconcile.env` state file format unchanged.

## Non-Functional Architecture Notes
- Security: no change to credential handling; `gho_` tokens accepted exactly as `ghp_`/`github_pat_` tokens were.
- Observability: `log_info` message added for `gho_` acceptance; `record_reconcile_issue` message added for kustomize apply failure in best-effort mode.
- Reliability and rollback: rollback by reverting the two one-line changes. Dry-run mode is unaffected because `run_kustomize_apply` returns 0 in dry-run unconditionally.
- Monitoring/alerting: none.

## Risks and Tradeoffs
- Risk 1: accepting `gho_` tokens means ArgoCD can lose repo access when the OAuth token expires — mitigated by `ARGOCD_REPO_CREDENTIALS_REQUIRED=false` default and the INFO log guiding operators toward PATs.
- Tradeoff 1: the `if !` guard means a kustomize apply failure in required=false mode is silently captured as a warning; operators who want strict apply validation should set `RUNTIME_CREDENTIALS_REQUIRED=true`.
