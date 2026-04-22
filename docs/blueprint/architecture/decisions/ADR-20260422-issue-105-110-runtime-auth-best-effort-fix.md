# ADR-20260422: Runtime Auth Best-Effort Fix (Issues #105, #110)

## Status
Approved

## Context
Two runtime auth scripts have behavior that conflicts with their declared best-effort contract:

1. `reconcile_eso_runtime_secrets.sh` aborts under `set -e` when `kustomize apply infra/gitops/platform/base/security` fails due to missing namespaces, propagating `plugin_eso_status=failure` to the orchestrator and aborting `make infra-provision-deploy` even when `RUNTIME_CREDENTIALS_REQUIRED=false`.

2. `reconcile_argocd_repo_credentials.sh` treats `gho_` (GitHub OAuth) token prefixes as a reconcile issue, producing `status=success-with-warnings` even when the same token authenticates successfully for repo read operations.

## Decision

### Issue #105 — kustomize apply guard

**Option A (selected)**: Wrap `run_kustomize_apply` in `if !` so `set -e` cannot abort. The failure is captured by `record_reconcile_issue`; the existing end-of-script logic determines the final status.

**Option B**: Use `set +e`/`set -e` pair around the call. Rejected — broader blast radius; risks silencing subsequent failures in the same block.

### Issue #110 — gho_ token policy

**Option A (selected)**: Accept `gho_` tokens; replace `record_reconcile_issue` with `log_info` noting PAT preference. Removes the ambiguous success-with-warnings state without weakening auth validation (empty tokens are still rejected).

**Option B**: Keep PAT-only policy but escalate to hard error. Rejected — breaks local operator flows where `gh auth token` returns `gho_` and the credential actually works.

## Consequences
- `make infra-provision-deploy` no longer aborts for recoverable namespace timing issues in best-effort mode.
- Local operator flows using `gho_` tokens get `status=success` instead of the confusing `success-with-warnings`.
- PAT preference is communicated via INFO log, not a warning that affects status.
- Dry-run mode is unaffected.
