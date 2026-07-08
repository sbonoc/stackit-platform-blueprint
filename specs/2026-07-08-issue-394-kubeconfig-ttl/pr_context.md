# PR Context

## Summary

Fixes issue #394: `stackit_foundation_fetch_kubeconfig.sh` now force-taints
`stackit_ske_kubeconfig.foundation[0]` before every `terraform apply` in
execute mode, ensuring Terraform always regenerates the resource and its
client certificate (~1 h TTL). Previously, the idempotent `apply` skipped the
resource when no config changes were detected, silently returning a stale
kubeconfig and causing `Unauthorized` errors in kubectl and CI pipelines more
than ~1 h after the last refresh. The fix follows the existing precedent for
`stackit_postgresflex_instance.foundation[0]` in `stackit_foundation_apply.sh`.
Dry-run mode is unaffected. An ADR and operator troubleshooting section are
included. Four unit tests (T-101–T-104) cover all acceptance criteria.
Changelog and test pyramid contract updated; bootstrap template mirror synced.

## Requirement Coverage

| Requirement | Implementation | Test |
|---|---|---|
| FR-001 — force-taint before apply in execute mode | `scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh` lines 64–67 (`run_cmd terraform … taint`) | T-101 (`test_taint_precedes_apply_in_script_source`) |
| FR-002 — taint unconditionally skipped in dry-run | `elif tooling_is_execution_enabled` branch — taint line not reached when DRY_RUN=true | T-102 (`test_no_taint_call_in_dry_run_mode`) |
| FR-003 — log INFO before taint | `log_info "force-tainting …"` line 66 | T-104 (`test_log_info_with_resource_address_precedes_taint`) |
| NFR-SEC-001 — no new credential-handling paths | sole write path unchanged: `terraform output -raw ske_kubeconfig > "$kubeconfig_output"` | T-103 (kubeconfig not written when taint fails) |
| NFR-OBS-001 — log_info/log_metric before taint | `log_info "force-tainting …"` line 66 | T-104 |
| NFR-REL-001 — abort if taint exits non-zero | `set -euo pipefail` propagates non-zero taint exit; no extra handler required | T-103 (`test_script_aborts_when_taint_fails`) |
| NFR-OPS-001 — no operator action required | taint is automatic; no env var opt-in; `make infra-stackit-foundation-refresh-kubeconfig` unchanged | T-102 (dry-run exits 0 without operator input) |
| AC-001 — taint before apply in source order | same as FR-001 | T-101 |
| AC-002 — taint skipped in dry-run | same as FR-002 | T-102 |
| AC-003 — abort before output on taint failure | same as NFR-REL-001 | T-103 |
| AC-004 — log message before taint | same as NFR-OBS-001 | T-104 |

## Key Reviewer Files

- Primary files to review first:
  - `scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh` — core fix: 3 lines added in the `elif tooling_is_execution_enabled` branch (lines 64–67); verify taint precedes `terraform_backend_init` and `run_cmd_capture terraform … output`
  - `tests/infra/test_kubeconfig_ttl_issue_394.py` — 4 acceptance-criteria tests (T-101–T-104); review stub fidelity (per-subcommand exit control, call log) and static-analysis comment-line skip in T-104
- `scripts/lib/quality/test_pyramid_contract.json` — new test file registered in `unit` scope; one-line addition
- `docs/platform/architecture/decisions/ADR-issue-394-kubeconfig-ttl.md` — decision record for Option A; Mermaid flowchart covers dry-run vs execute paths
- `docs/platform/consumer/troubleshooting.md` — new operator runbook section with pre-v1.12.3 manual workaround
- `scripts/templates/blueprint/bootstrap/docs/platform/consumer/troubleshooting.md` — manual mirror of troubleshooting.md (not in sync_blueprint_template_docs.py scope); confirm identical section
- `specs/2026-07-08-issue-394-kubeconfig-ttl/spec.md` — SPEC_READY: true; SPEC_READY_EXCEPTION: bug-fix; all sign-offs approved

## Validation Evidence

```
# Unit tests (issue-specific)
$ uv run python3 -m pytest tests/infra/test_kubeconfig_ttl_issue_394.py -v
PASSED tests/infra/test_kubeconfig_ttl_issue_394.py::AC001TaintInvokedBeforeApply::test_taint_precedes_apply_in_script_source
PASSED tests/infra/test_kubeconfig_ttl_issue_394.py::AC002TaintSkippedInDryRun::test_no_taint_call_in_dry_run_mode
PASSED tests/infra/test_kubeconfig_ttl_issue_394.py::AC003AbortOnTaintFailure::test_script_aborts_when_taint_fails
PASSED tests/infra/test_kubeconfig_ttl_issue_394.py::AC004LogMessageOnTaint::test_log_info_with_resource_address_precedes_taint
4 passed in <1s

# Full test suite
$ uv run python3 -m pytest
2272 passed, 5 pre-existing cluster-integration failures (test_optional_modules + test_runtime_credentials_eso — unrelated to this change)

# Infra contract validation
$ make infra-validate
pass

# Docs drift check
$ make quality-docs-check-changed
exit 0

# All pre-push hooks passed on final push to origin
```

## Risk and Rollback

**Risk:** Force-tainting on every refresh adds one extra STACKIT API call (taint + re-plan before apply). The resource has no data, so destroy + recreate is safe and fast; no credential content is at risk. The pattern is identical to the existing PostgreSQL Flex taint precedent in `stackit_foundation_apply.sh`.

**Blast radius:** Isolated to `stackit_foundation_fetch_kubeconfig.sh`. No other script, module, or consumer contract is changed. Dry-run path is unaffected.

**Feature flag:** None — the fix is always active in execute mode; dry-run behaviour is unchanged.

**Rollback steps:**
1. Revert the three lines added in the `elif tooling_is_execution_enabled` block of `stackit_foundation_fetch_kubeconfig.sh` (lines 64–67).
2. Run `git revert <commit-sha>` for commit `fix(issue-394-kubeconfig-ttl): force-taint …` and push.
3. No Terraform state changes are needed — the taint is applied at runtime and does not persist between script runs.

**Pre-v1.12.3 manual workaround** (for consumers who cannot update immediately):
```bash
terraform -chdir="$(make print-STACKIT_FOUNDATION_TERRAFORM_DIR)" taint "stackit_ske_kubeconfig.foundation[0]"
make infra-stackit-foundation-refresh-kubeconfig
```

## Deferred Proposals

1. **ServiceAccount token authentication** — replace short-lived client-certificate kubeconfig with a `ServiceAccount` token of configurable duration; eliminates the Terraform resource TTL coupling entirely.
   Parked — trigger: on-scope: infra — blocked on STACKIT SKE SA-token provisioner stability; no urgency now that force-taint is in place.

2. **Kubeconfig expiry pre-flight check in smoke scripts** — add an `openssl x509 -checkend` guard in `make infra-smoke` to fail-fast with a clear error before attempting `kubectl` calls.
   Parked — trigger: on-scope: infra — operator-UX complement to this fix; low urgency; surfaces when smoke scripts are next in scope.
