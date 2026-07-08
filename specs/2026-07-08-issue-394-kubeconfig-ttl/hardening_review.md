# Hardening Review

## Repository-Wide Findings Fixed

None — this is a focused bug fix. Static analysis and the full test suite (2272 tests) were run; no repository-wide issues were found or introduced. The 5 pre-existing failures in `test_optional_modules` and `test_runtime_credentials_eso` are unrelated cluster-integration tests that require a live STACKIT environment and are not caused by this change.

## Observability and Diagnostics Changes

- `log_info "force-tainting stackit_ske_kubeconfig.foundation[0] to ensure a fresh client certificate"` added to `stackit_foundation_fetch_kubeconfig.sh` (line 66) — emitted on every execute-mode refresh. The message is captured by `start_script_metric_trap` telemetry and appears in the operator's terminal output.
- The existing `log_metric "stackit_kubeconfig_bytes"` call at script end remains; `content_source` value is `terraform_output` (unchanged) when the taint-and-apply path succeeds.
- No log lines were removed; no metric names were changed.

## Architecture and Code Quality Compliance

- Follows the existing force-taint precedent for `stackit_postgresflex_instance.foundation[0]` in `stackit_foundation_apply.sh` — same guard (`tooling_is_execution_enabled`), same `run_cmd terraform … taint` pattern.
- `set -euo pipefail` at script top provides NFR-REL-001 abort behaviour with no additional error-handling code.
- No new env vars, no new shell dependencies, no new Terraform resources.
- Test pyramid contract updated: `tests/infra/test_kubeconfig_ttl_issue_394.py` registered in `unit` scope.
- ADR filed at `docs/platform/architecture/decisions/ADR-issue-394-kubeconfig-ttl.md`; status: approved.

## Proposals Only (Not Implemented)

1. **ServiceAccount token authentication** — replace the `stackit_ske_kubeconfig` Terraform resource with a `ServiceAccount`-token-based kubeconfig of configurable duration; eliminates the ~1 h TTL coupling entirely. Deferred: STACKIT SKE SA-token provisioner is not yet stable. Trigger: on-scope: infra.

2. **Kubeconfig expiry pre-flight check in smoke scripts** — add an `openssl x509 -checkend` guard in `make infra-smoke` to fail-fast with a clear error before `kubectl` calls are attempted. Deferred: operator-UX complement; low urgency post-fix. Trigger: on-scope: infra.
