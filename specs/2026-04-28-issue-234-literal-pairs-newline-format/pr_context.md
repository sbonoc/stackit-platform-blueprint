# PR Context

## Summary
- Work item: `2026-04-28-issue-234-literal-pairs-newline-format` — fix `parse_literal_pairs()` to use newline-only delimiter; reject comma-separated input with visible diagnostic.
- Objective: Restore correct behavior for `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` when any value contains a comma (data URIs, base64 payloads, connection strings). The old comma-splitter silently truncated values and caused a silent ESO reconcile failure cascade that blocked all app deployments in affected environments.
- Scope boundaries: Limited to `parse_literal_pairs()` in `reconcile_eso_runtime_secrets.sh`, its test coverage in `test_runtime_credentials_eso.py`, and consumer documentation (`runtime_credentials_eso.md`, `troubleshooting.md`) with bootstrap template copies. No other auth scripts, no HTTP endpoints, no infrastructure topology changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001
- Acceptance criteria covered: AC-001 (comma-in-value positive path — PASS), AC-002 (comma-separated rejection — PASS), AC-003 (full value verbatim preservation — PASS)
- Contract surfaces changed: `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` env var — **breaking change**: newline-separated `key=value` pairs only; comma-separated format no longer accepted. Error message in `record_reconcile_issue` updated to reference newline-separated as sole format.

## Key Reviewer Files
- Primary files to review first:
  1. `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` — `parse_literal_pairs()` replacement (newline loop + comma-detection heuristic + `log_warn` calls)
  2. `tests/infra/test_runtime_credentials_eso.py` — two new tests (AC-001/AC-002/AC-003) and two migrated tests (T-001a, line 290 fix)
- High-risk files:
  1. `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` — breaking behavior change; any consumer passing comma-separated `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` will now receive a non-zero exit + `log_warn`
  2. `docs/platform/consumer/runtime_credentials_eso.md` + `scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md` — format contract declared; migration guide added

## Validation Evidence
- Required commands executed:
  - `python3 -m pytest tests/infra/test_runtime_credentials_eso.py -v` — 12/12 PASS
  - `make infra-validate` — PASS
  - `make infra-contract-test-fast` — 136/136 PASS
  - `make docs-build` — PASS
  - `make docs-smoke` — PASS
  - `make quality-hooks-fast` — PASS (quality-spec-pr-ready expected-fail resolved at publish phase)
- Result summary: All 12 tests in `test_runtime_credentials_eso.py` pass; 136/136 `infra-contract-test-fast` pass; docs build clean; 0 regressions in this work item's scope. 8 pre-existing failures in `test_optional_modules.py` confirmed pre-existing (verified via `git stash` + rerun).
- Artifact references:
  - `artifacts/infra/runtime_credentials/_reconcile_state` (operational diagnostic surface)
  - `artifacts/infra/runtime_credentials/_reconcile_issues.json` (parse failure record on rejection path)

## Risk and Rollback
- Main risks:
  - Breaking change: any consumer that passes `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` in comma-separated form will now fail with a non-zero exit and `log_warn`. The diagnostic message names the expected format and instructs consumers to switch to `$'...'` quoting.
  - Consumers who applied the workaround already use newline format and are unaffected.
  - The comma-detection heuristic may have edge cases for single-line values that happen to contain comma-separated-looking segments. Mitigated by restricting detection to single-line input with >1 comma-split element where elements [1:] have an identifier key AND non-empty value.
- Rollback strategy: Revert `parse_literal_pairs()` to `IFS=',' read -r -a raw_pairs` loop. Consumers who applied the workaround would need to revert only if they relied on the comma-fallback path (none expected — the workaround was specifically to move away from comma-separated format).

## Deferred Proposals
- Proposal 1 (not implemented): Bash unit test harness for `parse_literal_pairs()` isolated from the full reconcile subprocess. Deferred — existing integration-level tests provide adequate coverage; a dedicated bash unit harness requires new test infrastructure outside this scope.
- Proposal 2 (not implemented): Consumer cleanup — remove workaround patches in `provision_deploy_local_marketplace.sh` (consumer repo) that became no-ops after this fix. Tracked as Follow-up 1 in `traceability.md`; consumer can action after this PR ships. Workaround review date: 2026-07-28.
